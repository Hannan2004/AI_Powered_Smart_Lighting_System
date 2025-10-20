import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from pydantic import BaseModel
from collections import Counter
from kafka import KafkaConsumer
from ..config.settings import config

logger = logging.getLogger(__name__)

class ThreatDetectionState(BaseModel):
    """State for threat detection operations"""
    messages: list = []
    security_events: list = []
    detected_threats: list = []
    threat_patterns: Dict[str, Any] = {}
    alert_level: str = "normal"
    threat_summary: Dict[str, Any] = {}

class ThreatDetectionAgent:
    """
    LangGraph agent for detecting and analyzing cybersecurity threats.
    Analyzes security events, identifies patterns, and classifies threats.
    """
    
    def __init__(self):
        self.llm = ChatGroq(
            temperature=0,
            model_name="llama3-8b-8192",
            groq_api_key=config.GROQ_API_KEY
        )
        
        self.kafka_config = config.get_kafka_config()
        self.graph = self._create_graph()
    
    def _create_graph(self):
        """Create LangGraph workflow for threat detection"""
        workflow = StateGraph(ThreatDetectionState)
        
        # Add nodes
        workflow.add_node("collect_events", self._collect_events)
        workflow.add_node("analyze_patterns", self._analyze_patterns)
        workflow.add_node("classify_threats", self._classify_threats)
        workflow.add_node("generate_alerts", self._generate_alerts)
        
        # Define edges
        workflow.set_entry_point("collect_events")
        workflow.add_edge("collect_events", "analyze_patterns")
        workflow.add_edge("analyze_patterns", "classify_threats")
        workflow.add_edge("classify_threats", "generate_alerts")
        workflow.add_edge("generate_alerts", END)
        
        return workflow.compile()
    
    def _collect_events(self, state: ThreatDetectionState) -> ThreatDetectionState:
        """Collect security events from Kafka"""
        try:
            consumer = KafkaConsumer(
                'cyber_alerts',
                bootstrap_servers=self.kafka_config['bootstrap_servers'],
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                consumer_timeout_ms=3000,
                auto_offset_reset='latest'
            )
            
            security_events = []
            cutoff_time = datetime.now() - timedelta(seconds=300)
            
            for message in consumer:
                try:
                    data = message.value
                    if data.get('event_type') in ['security_alert', 'threat_detection', 'network_traffic']:
                        msg_time = datetime.fromisoformat(data.get('timestamp', ''))
                        if msg_time > cutoff_time:
                            security_events.append(data)
                except Exception as e:
                    logger.warning(f"Error parsing event message: {e}")
                    continue
            
            consumer.close()
            
            state.security_events = security_events
            state.messages.append(f"Collected {len(security_events)} security events")
            
        except Exception as e:
            logger.error(f"Error collecting events: {e}")
            state.messages.append(f"Event collection failed: {str(e)}")
        
        return state
    
    def _analyze_patterns(self, state: ThreatDetectionState) -> ThreatDetectionState:
        """Analyze patterns in security events"""
        if not state.security_events:
            state.messages.append("No security events to analyze")
            return state
        
        # Analyze severity distribution
        severity_counts = Counter(event.get('severity', 'low') for event in state.security_events)
        
        # Analyze source patterns
        source_counts = Counter(event.get('source_id', 'unknown') for event in state.security_events)
        ip_counts = Counter(event.get('source_ip', 'unknown') for event in state.security_events if event.get('source_ip'))
        
        # Analyze event types
        event_type_counts = Counter(event.get('event_type', 'unknown') for event in state.security_events)
        
        # Identify unusual patterns
        anomalies = []
        
        # High severity concentration
        critical_high = severity_counts.get('critical', 0) + severity_counts.get('high', 0)
        if critical_high > len(state.security_events) * 0.3:
            anomalies.append("high_severity_concentration")
        
        # Single source generating many events
        max_source_events = max(source_counts.values()) if source_counts else 0
        if max_source_events > 20:
            anomalies.append("single_source_flood")
        
        # Multiple IPs from same source
        if len(ip_counts) > 10:
            anomalies.append("multiple_ip_sources")
        
        state.threat_patterns = {
            "severity_distribution": dict(severity_counts),
            "top_sources": dict(source_counts.most_common(5)),
            "top_ips": dict(ip_counts.most_common(5)),
            "event_types": dict(event_type_counts),
            "anomalies": anomalies,
            "total_events": len(state.security_events)
        }
        
        state.messages.append(f"Pattern analysis complete: {len(anomalies)} anomalies detected")
        
        return state
    
    def _classify_threats(self, state: ThreatDetectionState) -> ThreatDetectionState:
        """Classify threats using LLM analysis"""
        try:
            classification_prompt = f"""
            Classify cybersecurity threats based on event analysis:
            
            Event Patterns: {state.threat_patterns}
            Total Events: {len(state.security_events)}
            
            Identify:
            1. Primary threat types (malware, intrusion, ddos, etc.)
            2. Threat severity classification
            3. Potential attack vectors
            4. Confidence level of threat assessment
            
            Format as structured analysis. Be specific and concise.
            """
            
            response = self.llm.invoke(classification_prompt)
            
            # Extract threat information
            detected_threats = []
            content = response.content.lower()
            
            # Simple threat type detection
            threat_types = ['malware', 'intrusion', 'ddos', 'phishing', 'ransomware', 'botnet']
            for threat_type in threat_types:
                if threat_type in content:
                    confidence = "high" if f"high confidence" in content else "medium"
                    detected_threats.append({
                        "type": threat_type,
                        "confidence": confidence,
                        "evidence_count": state.threat_patterns.get("total_events", 0)
                    })
            
            # Determine alert level
            severity_dist = state.threat_patterns.get("severity_distribution", {})
            critical_count = severity_dist.get("critical", 0)
            high_count = severity_dist.get("high", 0)
            
            if critical_count > 0:
                state.alert_level = "critical"
            elif high_count > 5:
                state.alert_level = "high"
            elif high_count > 0 or len(detected_threats) > 0:
                state.alert_level = "medium"
            else:
                state.alert_level = "low"
            
            state.detected_threats = detected_threats
            state.threat_summary = {
                "llm_analysis": response.content,
                "threat_count": len(detected_threats),
                "alert_level": state.alert_level,
                "classification_timestamp": datetime.now().isoformat()
            }
            
            state.messages.append(f"Threat classification complete: {len(detected_threats)} threats detected")
            
        except Exception as e:
            logger.error(f"Error in threat classification: {e}")
            state.messages.append(f"Threat classification failed: {str(e)}")
            state.alert_level = "unknown"
        
        return state
    
    def _generate_alerts(self, state: ThreatDetectionState) -> ThreatDetectionState:
        """Generate appropriate alerts based on detected threats"""
        alerts = []
        
        # Generate alerts based on threat level
        if state.alert_level == "critical":
            alerts.append("CRITICAL ALERT: Immediate security response required")
            alerts.append("Multiple high-severity threats detected")
        elif state.alert_level == "high":
            alerts.append("HIGH ALERT: Security team attention needed")
            alerts.append("Significant threat activity detected")
        elif state.alert_level == "medium":
            alerts.append("MEDIUM ALERT: Monitor situation closely")
        else:
            alerts.append("INFO: Normal security monitoring status")
        
        # Add specific threat alerts
        for threat in state.detected_threats[:3]:  # Top 3 threats
            threat_type = threat.get("type", "unknown")
            confidence = threat.get("confidence", "low")
            alerts.append(f"THREAT DETECTED: {threat_type.upper()} - confidence: {confidence}")
        
        # Add pattern-based alerts
        anomalies = state.threat_patterns.get("anomalies", [])
        for anomaly in anomalies:
            if anomaly == "high_severity_concentration":
                alerts.append("PATTERN ALERT: Unusual concentration of high-severity events")
            elif anomaly == "single_source_flood":
                alerts.append("PATTERN ALERT: Single source generating excessive events")
            elif anomaly == "multiple_ip_sources":
                alerts.append("PATTERN ALERT: Multiple IP sources detected")
        
        state.messages.extend(alerts)
        state.messages.append(f"Generated {len(alerts)} security alerts")
        
        return state
    
    def detect_threats(self, initial_state: Optional[ThreatDetectionState] = None) -> Dict[str, Any]:
        """Execute the threat detection workflow"""
        try:
            if initial_state is None:
                initial_state = ThreatDetectionState()
            
            final_state = self.graph.invoke(initial_state)
            
            return {
                "timestamp": datetime.now().isoformat(),
                "alert_level": final_state.alert_level,
                "detected_threats": final_state.detected_threats,
                "threat_patterns": final_state.threat_patterns,
                "threat_summary": final_state.threat_summary,
                "security_alerts": [msg for msg in final_state.messages if "ALERT" in msg],
                "events_analyzed": len(final_state.security_events),
                "status": "detection_complete"
            }
            
        except Exception as e:
            logger.error(f"Error in threat detection: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "status": "detection_failed"
            }

# Create agent instance
threat_detection_agent = ThreatDetectionAgent()