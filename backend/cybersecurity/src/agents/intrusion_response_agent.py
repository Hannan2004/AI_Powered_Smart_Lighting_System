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

class IntrusionResponseState(BaseModel):
    """State for intrusion response operations"""
    messages: list = []
    network_data: list = []
    suspicious_ips: list = []
    threat_assessment: Dict[str, Any] = {}
    response_actions: list = []
    threat_level: str = "unknown"

class IntrusionResponseAgent:
    """
    LangGraph agent for detecting and responding to network intrusions.
    Monitors traffic, identifies threats, and coordinates immediate response.
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
        """Create LangGraph workflow for intrusion response"""
        workflow = StateGraph(IntrusionResponseState)
        
        # Add nodes
        workflow.add_node("monitor_network", self._monitor_network)
        workflow.add_node("identify_threats", self._identify_threats)
        workflow.add_node("assess_risk", self._assess_risk)
        workflow.add_node("generate_response", self._generate_response)
        
        # Define edges
        workflow.set_entry_point("monitor_network")
        workflow.add_edge("monitor_network", "identify_threats")
        workflow.add_edge("identify_threats", "assess_risk")
        workflow.add_edge("assess_risk", "generate_response")
        workflow.add_edge("generate_response", END)
        
        return workflow.compile()
    
    def _monitor_network(self, state: IntrusionResponseState) -> IntrusionResponseState:
        """Monitor network traffic for intrusion indicators"""
        try:
            consumer = KafkaConsumer(
                'cyber_alerts',
                bootstrap_servers=self.kafka_config['bootstrap_servers'],
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                consumer_timeout_ms=3000,
                auto_offset_reset='latest'
            )
            
            network_data = []
            cutoff_time = datetime.now() - timedelta(seconds=300)
            
            for message in consumer:
                try:
                    data = message.value
                    if data.get('event_type') in ['network_traffic', 'security_alert']:
                        msg_time = datetime.fromisoformat(data.get('timestamp', ''))
                        if msg_time > cutoff_time:
                            network_data.append(data)
                except Exception as e:
                    logger.warning(f"Error parsing network message: {e}")
                    continue
            
            consumer.close()
            
            state.network_data = network_data
            state.messages.append(f"Monitored {len(network_data)} network events")
            
        except Exception as e:
            logger.error(f"Error monitoring network: {e}")
            state.messages.append(f"Network monitoring failed: {str(e)}")
        
        return state
    
    def _identify_threats(self, state: IntrusionResponseState) -> IntrusionResponseState:
        """Identify potential threats and suspicious IPs"""
        if not state.network_data:
            state.messages.append("No network data available for threat identification")
            return state
        
        # Count activities per IP
        ip_counts = Counter()
        ip_severities = {}
        
        for data in state.network_data:
            ip = data.get('source_ip', '')
            severity = data.get('severity', 'low')
            
            if ip:
                ip_counts[ip] += 1
                if ip not in ip_severities:
                    ip_severities[ip] = []
                ip_severities[ip].append(severity)
        
        # Identify suspicious IPs (threshold: 10 activities)
        suspicious_ips = []
        for ip, count in ip_counts.items():
            if count > 10:
                severities = ip_severities.get(ip, [])
                high_severity = sum(1 for s in severities if s in ['high', 'critical'])
                
                risk_score = min(count * 2 + high_severity * 10, 100)
                
                suspicious_ips.append({
                    "ip_address": ip,
                    "activity_count": count,
                    "high_severity_alerts": high_severity,
                    "risk_score": risk_score
                })
        
        # Sort by risk score
        suspicious_ips.sort(key=lambda x: x["risk_score"], reverse=True)
        
        state.suspicious_ips = suspicious_ips
        state.messages.append(f"Identified {len(suspicious_ips)} suspicious IPs")
        
        return state
    
    def _assess_risk(self, state: IntrusionResponseState) -> IntrusionResponseState:
        """Assess overall risk using LLM analysis"""
        try:
            risk_prompt = f"""
            Assess intrusion risk based on network monitoring:
            
            Network Events: {len(state.network_data)}
            Suspicious IPs: {len(state.suspicious_ips)}
            Top Suspicious IPs: {state.suspicious_ips[:3]}
            
            Determine:
            1. Overall threat level (low/medium/high/critical)
            2. Primary attack vectors identified
            3. Immediate risks to system security
            4. Urgency of response required
            
            Be concise and specific.
            """
            
            response = self.llm.invoke(risk_prompt)
            
            # Extract threat level from response
            content = response.content.lower()
            if 'critical' in content:
                state.threat_level = 'critical'
            elif 'high' in content:
                state.threat_level = 'high'
            elif 'medium' in content:
                state.threat_level = 'medium'
            else:
                state.threat_level = 'low'
            
            state.threat_assessment = {
                "analysis": response.content,
                "threat_level": state.threat_level,
                "timestamp": datetime.now().isoformat()
            }
            
            state.messages.append(f"Risk assessment complete: {state.threat_level} threat level")
            
        except Exception as e:
            logger.error(f"Error in risk assessment: {e}")
            state.messages.append(f"Risk assessment failed: {str(e)}")
            state.threat_level = 'unknown'
        
        return state
    
    def _generate_response(self, state: IntrusionResponseState) -> IntrusionResponseState:
        """Generate appropriate response actions"""
        response_actions = []
        
        # Generate actions based on threat level
        if state.threat_level == 'critical':
            response_actions.extend([
                "IMMEDIATE: Activate incident response team",
                "IMMEDIATE: Block top suspicious IPs",
                "IMMEDIATE: Isolate affected network segments"
            ])
        elif state.threat_level == 'high':
            response_actions.extend([
                "URGENT: Investigate suspicious IP activities",
                "URGENT: Enhance monitoring for identified threats",
                "SCHEDULE: Security team notification"
            ])
        elif state.threat_level == 'medium':
            response_actions.extend([
                "MONITOR: Continue observation of suspicious IPs",
                "REVIEW: Analyze attack patterns",
                "UPDATE: Firewall rules if needed"
            ])
        else:
            response_actions.append("ROUTINE: Continue standard monitoring")
        
        # Add IP-specific actions
        for ip_info in state.suspicious_ips[:3]:  # Top 3 IPs
            if ip_info['risk_score'] > 70:
                response_actions.append(f"BLOCK: IP {ip_info['ip_address']} (risk score: {ip_info['risk_score']})")
            elif ip_info['risk_score'] > 50:
                response_actions.append(f"MONITOR: IP {ip_info['ip_address']} closely")
        
        state.response_actions = response_actions
        state.messages.append(f"Generated {len(response_actions)} response actions")
        
        return state
    
    def respond_to_intrusion(self, initial_state: Optional[IntrusionResponseState] = None) -> Dict[str, Any]:
        """Execute the intrusion response workflow"""
        try:
            if initial_state is None:
                initial_state = IntrusionResponseState()
            
            final_state = self.graph.invoke(initial_state)
            
            return {
                "timestamp": datetime.now().isoformat(),
                "threat_level": final_state.threat_level,
                "suspicious_ips_count": len(final_state.suspicious_ips),
                "top_suspicious_ips": final_state.suspicious_ips[:5],
                "threat_assessment": final_state.threat_assessment,
                "response_actions": final_state.response_actions,
                "messages": final_state.messages,
                "network_events_analyzed": len(final_state.network_data),
                "status": "response_complete"
            }
            
        except Exception as e:
            logger.error(f"Error in intrusion response: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "status": "response_failed"
            }

# Create agent instance
intrusion_response_agent = IntrusionResponseAgent()