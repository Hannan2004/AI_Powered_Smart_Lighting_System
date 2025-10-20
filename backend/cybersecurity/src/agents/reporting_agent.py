import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from pydantic import BaseModel
from collections import Counter
from kafka import KafkaConsumer, KafkaProducer
from ..config.settings import config

logger = logging.getLogger(__name__)

class ReportingState(BaseModel):
    """State for reporting operations"""
    messages: list = []
    incident_data: list = []
    report_content: Dict[str, Any] = {}
    executive_summary: Dict[str, Any] = {}
    recommendations: list = []
    publication_status: str = "pending"

class ReportingAgent:
    """
    LangGraph agent for generating and publishing cybersecurity reports.
    Creates incident reports, executive summaries, and publishes to stakeholders.
    """
    
    def __init__(self):
        self.llm = ChatGroq(
            temperature=0,
            model_name="llama3-8b-8192",
            groq_api_key=config.GROQ_API_KEY
        )
        
        self.kafka_config = config.get_kafka_config()
        self.producer = self._init_producer()
        self.graph = self._create_graph()
    
    def _init_producer(self):
        """Initialize Kafka producer"""
        try:
            return KafkaProducer(
                bootstrap_servers=self.kafka_config['bootstrap_servers'],
                value_serializer=lambda x: json.dumps(x).encode('utf-8'),
                key_serializer=lambda x: x.encode('utf-8') if x else None
            )
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            return None
    
    def _create_graph(self):
        """Create LangGraph workflow for reporting"""
        workflow = StateGraph(ReportingState)
        
        # Add nodes
        workflow.add_node("collect_incidents", self._collect_incidents)
        workflow.add_node("analyze_data", self._analyze_data)
        workflow.add_node("generate_report", self._generate_report)
        workflow.add_node("publish_report", self._publish_report)
        
        # Define edges
        workflow.set_entry_point("collect_incidents")
        workflow.add_edge("collect_incidents", "analyze_data")
        workflow.add_edge("analyze_data", "generate_report")
        workflow.add_edge("generate_report", "publish_report")
        workflow.add_edge("publish_report", END)
        
        return workflow.compile()
    
    def _collect_incidents(self, state: ReportingState) -> ReportingState:
        """Collect incident data from Kafka"""
        try:
            consumer = KafkaConsumer(
                'cyber_alerts',
                bootstrap_servers=self.kafka_config['bootstrap_servers'],
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                consumer_timeout_ms=5000,
                auto_offset_reset='latest'
            )
            
            incident_data = []
            cutoff_time = datetime.now() - timedelta(seconds=3600)  # Last hour
            
            for message in consumer:
                try:
                    data = message.value
                    if data.get('event_type') in ['security_alert', 'threat_detection', 'network_traffic']:
                        msg_time = datetime.fromisoformat(data.get('timestamp', ''))
                        if msg_time > cutoff_time:
                            incident_data.append(data)
                except Exception as e:
                    logger.warning(f"Error parsing incident message: {e}")
                    continue
            
            consumer.close()
            
            state.incident_data = incident_data
            state.messages.append(f"Collected {len(incident_data)} incident records")
            
        except Exception as e:
            logger.error(f"Error collecting incidents: {e}")
            state.messages.append(f"Incident collection failed: {str(e)}")
        
        return state
    
    def _analyze_data(self, state: ReportingState) -> ReportingState:
        """Analyze incident data for reporting"""
        if not state.incident_data:
            state.messages.append("No incident data available for analysis")
            return state
        
        # Basic statistics
        total_incidents = len(state.incident_data)
        severity_counts = Counter(incident.get('severity', 'low') for incident in state.incident_data)
        event_type_counts = Counter(incident.get('event_type', 'unknown') for incident in state.incident_data)
        source_counts = Counter(incident.get('source_id', 'unknown') for incident in state.incident_data)
        
        # Time analysis
        timestamps = [incident.get('timestamp') for incident in state.incident_data if incident.get('timestamp')]
        first_incident = min(timestamps) if timestamps else datetime.now().isoformat()
        last_incident = max(timestamps) if timestamps else datetime.now().isoformat()
        
        # Critical metrics
        critical_incidents = severity_counts.get('critical', 0)
        high_incidents = severity_counts.get('high', 0)
        
        # Business impact assessment
        if critical_incidents > 0:
            business_impact = "high"
        elif high_incidents > 5:
            business_impact = "medium"
        else:
            business_impact = "low"
        
        state.report_content = {
            "summary_stats": {
                "total_incidents": total_incidents,
                "time_range": f"{first_incident} to {last_incident}",
                "business_impact": business_impact
            },
            "severity_breakdown": dict(severity_counts),
            "event_type_breakdown": dict(event_type_counts),
            "top_affected_sources": dict(source_counts.most_common(5)),
            "critical_incidents": critical_incidents,
            "high_priority_incidents": high_incidents
        }
        
        state.messages.append(f"Data analysis complete: {business_impact} business impact")
        
        return state
    
    def _generate_report(self, state: ReportingState) -> ReportingState:
        """Generate comprehensive report using LLM"""
        try:
            report_prompt = f"""
            Generate cybersecurity incident report based on data:
            
            Summary: {state.report_content.get('summary_stats', {})}
            Severity Distribution: {state.report_content.get('severity_breakdown', {})}
            Event Types: {state.report_content.get('event_type_breakdown', {})}
            Top Sources: {state.report_content.get('top_affected_sources', {})}
            
            Create:
            1. Executive summary (2-3 sentences)
            2. Key findings and trends
            3. Risk assessment
            4. Actionable recommendations (3-5 items)
            5. Next steps for security team
            
            Keep it professional and actionable.
            """
            
            response = self.llm.invoke(report_prompt)
            
            # Extract recommendations from LLM response
            recommendations = []
            lines = response.content.split('\n')
            for line in lines:
                if any(keyword in line.lower() for keyword in ['recommend', 'should', 'must', 'need']):
                    if len(line.strip()) > 15:
                        recommendations.append(line.strip())
            
            # Create executive summary
            state.executive_summary = {
                "report_id": f"RPT_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "generated_at": datetime.now().isoformat(),
                "reporting_period": "Last 1 hour",
                "total_incidents": state.report_content.get('summary_stats', {}).get('total_incidents', 0),
                "business_impact": state.report_content.get('summary_stats', {}).get('business_impact', 'unknown'),
                "critical_issues": state.report_content.get('critical_incidents', 0),
                "llm_analysis": response.content
            }
            
            state.recommendations = recommendations[:5]  # Top 5 recommendations
            state.messages.append("Report generation complete")
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            state.messages.append(f"Report generation failed: {str(e)}")
        
        return state
    
    def _publish_report(self, state: ReportingState) -> ReportingState:
        """Publish report to Kafka topics"""
        if not self.producer:
            state.messages.append("Cannot publish - Kafka producer not available")
            state.publication_status = "failed"
            return state
        
        try:
            current_time = datetime.now()
            
            # Publish executive summary
            exec_key = f"exec_summary_{current_time.strftime('%Y%m%d_%H%M%S')}"
            exec_future = self.producer.send('executive_reports', key=exec_key, value=state.executive_summary)
            
            # Publish detailed report
            detailed_report = {
                "report_type": "detailed_incident_report",
                "executive_summary": state.executive_summary,
                "detailed_analysis": state.report_content,
                "recommendations": state.recommendations,
                "raw_data_count": len(state.incident_data)
            }
            
            detail_key = f"detailed_report_{current_time.strftime('%Y%m%d_%H%M%S')}"
            detail_future = self.producer.send('incident_reports', key=detail_key, value=detailed_report)
            
            # Publish to RAG knowledge base
            rag_content = {
                "knowledge_type": "incident_report",
                "timestamp": current_time.isoformat(),
                "summary": state.executive_summary,
                "searchable_text": self._create_searchable_text(state),
                "metadata": {
                    "incident_count": len(state.incident_data),
                    "business_impact": state.report_content.get('summary_stats', {}).get('business_impact', 'unknown')
                }
            }
            
            rag_key = f"knowledge_{current_time.strftime('%Y%m%d_%H%M%S')}"
            rag_future = self.producer.send('rag_knowledge_updates', key=rag_key, value=rag_content)
            
            # Wait for all publications
            exec_future.get(timeout=5)
            detail_future.get(timeout=5)
            rag_future.get(timeout=5)
            
            state.publication_status = "published"
            state.messages.append("Reports published to all channels successfully")
            
        except Exception as e:
            logger.error(f"Error publishing report: {e}")
            state.messages.append(f"Report publication failed: {str(e)}")
            state.publication_status = "failed"
        
        return state
    
    def _create_searchable_text(self, state: ReportingState) -> str:
        """Create searchable text for RAG system"""
        summary_stats = state.report_content.get('summary_stats', {})
        severity_breakdown = state.report_content.get('severity_breakdown', {})
        
        text_parts = [
            f"Cybersecurity incident report with {summary_stats.get('total_incidents', 0)} total incidents",
            f"Business impact level: {summary_stats.get('business_impact', 'unknown')}",
            f"Critical incidents: {state.report_content.get('critical_incidents', 0)}",
            f"High priority incidents: {state.report_content.get('high_priority_incidents', 0)}",
            f"Severity distribution: {severity_breakdown}"
        ]
        
        # Add recommendations
        if state.recommendations:
            text_parts.append(f"Key recommendations: {' | '.join(state.recommendations[:3])}")
        
        return " | ".join(text_parts)
    
    def generate_security_report(self, initial_state: Optional[ReportingState] = None) -> Dict[str, Any]:
        """Execute the reporting workflow"""
        try:
            if initial_state is None:
                initial_state = ReportingState()
            
            final_state = self.graph.invoke(initial_state)
            
            return {
                "timestamp": datetime.now().isoformat(),
                "publication_status": final_state.publication_status,
                "executive_summary": final_state.executive_summary,
                "report_content": final_state.report_content,
                "recommendations": final_state.recommendations,
                "incidents_analyzed": len(final_state.incident_data),
                "messages": final_state.messages,
                "status": "report_complete"
            }
            
        except Exception as e:
            logger.error(f"Error in report generation: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "status": "report_failed"
            }
    
    def __del__(self):
        """Cleanup producer"""
        if self.producer:
            try:
                self.producer.close()
            except:
                pass

# Create agent instance
reporting_agent = ReportingAgent()