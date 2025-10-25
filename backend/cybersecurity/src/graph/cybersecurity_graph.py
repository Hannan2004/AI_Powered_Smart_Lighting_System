import logging
from typing import Dict, Any
from datetime import datetime
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from pydantic import BaseModel
from src.agents.data_integrity_agent import data_integrity_agent, DataIntegrityState
from src.agents.threat_detection_agent import threat_detection_agent, ThreatDetectionState
from src.agents.intrusion_response_agent import intrusion_response_agent, IntrusionResponseState
from src.agents.reporting_agent import reporting_agent, ReportingState
from src.config.settings import config

logger = logging.getLogger(__name__)

class CybersecurityGraphState(BaseModel):
    """Combined state for the cybersecurity multi-agent graph"""
    messages: list = []
    
    # Agent-specific states
    integrity_results: Dict[str, Any] = {}
    threat_results: Dict[str, Any] = {}
    intrusion_results: Dict[str, Any] = {}
    reporting_results: Dict[str, Any] = {}
    
    # Overall analysis
    overall_status: str = "processing"
    risk_level: str = "unknown"
    priority_actions: list = []
    
    # Coordination flags
    integrity_complete: bool = False
    threat_complete: bool = False
    intrusion_complete: bool = False
    reporting_complete: bool = False

class CybersecurityGraph:
    """
    Multi-agent cybersecurity graph that coordinates all 4 specialized agents.
    Orchestrates data integrity validation, threat detection, intrusion response, and reporting.
    """
    
    def __init__(self):
        self.llm = ChatGroq(
            temperature=0,
            model_name="llama3-8b-8192",
            groq_api_key=config.GROQ_API_KEY
        )
        
        self.graph = self._create_graph()
    
    def _create_graph(self):
        """Create the multi-agent cybersecurity graph"""
        workflow = StateGraph(CybersecurityGraphState)
        
        # Add agent nodes
        workflow.add_node("data_integrity_agent", self._run_data_integrity)
        workflow.add_node("threat_detection_agent", self._run_threat_detection)
        workflow.add_node("intrusion_response_agent", self._run_intrusion_response)
        workflow.add_node("coordination_analysis", self._coordination_analysis)
        workflow.add_node("reporting_agent", self._run_reporting)
        
        # Define parallel execution for initial agents
        workflow.set_entry_point("data_integrity_agent")
        workflow.add_edge("data_integrity_agent", "threat_detection_agent")
        workflow.add_edge("threat_detection_agent", "intrusion_response_agent")
        workflow.add_edge("intrusion_response_agent", "coordination_analysis")
        workflow.add_edge("coordination_analysis", "reporting_agent")
        workflow.add_edge("reporting_agent", END)
        
        return workflow.compile()
    
    def _run_data_integrity(self, state: CybersecurityGraphState) -> CybersecurityGraphState:
        """Execute data integrity agent"""
        try:
            logger.info("Running Data Integrity Agent")
            
            # Create initial state for data integrity agent
            integrity_state = DataIntegrityState()
            
            # Run the data integrity validation
            result = data_integrity_agent.validate_data_integrity(integrity_state)
            
            state.integrity_results = result
            state.integrity_complete = True
            state.messages.append("Data integrity validation completed")
            
        except Exception as e:
            logger.error(f"Error in data integrity agent: {e}")
            state.messages.append(f"Data integrity agent failed: {str(e)}")
            state.integrity_results = {"error": str(e), "status": "failed"}
        
        return state
    
    def _run_threat_detection(self, state: CybersecurityGraphState) -> CybersecurityGraphState:
        """Execute threat detection agent"""
        try:
            logger.info("Running Threat Detection Agent")
            
            # Create initial state for threat detection agent
            threat_state = ThreatDetectionState()
            
            # Run threat detection
            result = threat_detection_agent.detect_threats(threat_state)
            
            state.threat_results = result
            state.threat_complete = True
            state.messages.append("Threat detection completed")
            
        except Exception as e:
            logger.error(f"Error in threat detection agent: {e}")
            state.messages.append(f"Threat detection agent failed: {str(e)}")
            state.threat_results = {"error": str(e), "status": "failed"}
        
        return state
    
    def _run_intrusion_response(self, state: CybersecurityGraphState) -> CybersecurityGraphState:
        """Execute intrusion response agent"""
        try:
            logger.info("Running Intrusion Response Agent")
            
            # Create initial state for intrusion response agent
            intrusion_state = IntrusionResponseState()
            
            # Run intrusion response
            result = intrusion_response_agent.respond_to_intrusion(intrusion_state)
            
            state.intrusion_results = result
            state.intrusion_complete = True
            state.messages.append("Intrusion response completed")
            
        except Exception as e:
            logger.error(f"Error in intrusion response agent: {e}")
            state.messages.append(f"Intrusion response agent failed: {str(e)}")
            state.intrusion_results = {"error": str(e), "status": "failed"}
        
        return state
    
    def _coordination_analysis(self, state: CybersecurityGraphState) -> CybersecurityGraphState:
        """Coordinate and analyze results from all agents using LLM"""
        try:
            logger.info("Running coordination analysis")
            
            # Prepare analysis data
            analysis_data = {
                "integrity_status": state.integrity_results.get("validation_status", "unknown"),
                "tampering_detected": state.integrity_results.get("tampering_detected", False),
                "threat_level": state.threat_results.get("alert_level", "unknown"),
                "detected_threats": len(state.threat_results.get("detected_threats", [])),
                "intrusion_threat_level": state.intrusion_results.get("threat_level", "unknown"),
                "suspicious_ips": state.intrusion_results.get("suspicious_ips_count", 0)
            }
            
            coordination_prompt = f"""
            Analyze cybersecurity situation based on multi-agent results:
            
            Data Integrity: {analysis_data['integrity_status']} (tampering: {analysis_data['tampering_detected']})
            Threat Detection: {analysis_data['threat_level']} ({analysis_data['detected_threats']} threats)
            Intrusion Response: {analysis_data['intrusion_threat_level']} ({analysis_data['suspicious_ips']} suspicious IPs)
            
            Determine:
            1. Overall risk level (low/medium/high/critical)
            2. Most critical issues requiring immediate attention
            3. Top 3 priority actions for security team
            4. Overall security posture assessment
            
            Be specific and actionable.
            """
            
            response = self.llm.invoke(coordination_prompt)
            
            # Extract overall risk level
            content = response.content.lower()
            if 'critical' in content:
                state.risk_level = 'critical'
            elif 'high' in content:
                state.risk_level = 'high'
            elif 'medium' in content:
                state.risk_level = 'medium'
            else:
                state.risk_level = 'low'
            
            # Extract priority actions
            priority_actions = []
            lines = response.content.split('\n')
            for line in lines:
                if any(keyword in line.lower() for keyword in ['priority', 'immediate', 'action', 'critical']):
                    if len(line.strip()) > 10:
                        priority_actions.append(line.strip())
            
            state.priority_actions = priority_actions[:3]
            state.overall_status = "analysis_complete"
            state.messages.append(f"Coordination analysis complete: {state.risk_level} risk level")
            
        except Exception as e:
            logger.error(f"Error in coordination analysis: {e}")
            state.messages.append(f"Coordination analysis failed: {str(e)}")
            state.overall_status = "analysis_failed"
            state.risk_level = "unknown"
        
        return state
    
    def _run_reporting(self, state: CybersecurityGraphState) -> CybersecurityGraphState:
        """Execute reporting agent with coordinated results"""
        try:
            logger.info("Running Reporting Agent")
            
            # Create enhanced reporting state with coordination results
            reporting_state = ReportingState()
            
            # Add coordination results to reporting context
            reporting_state.messages.append(f"Overall risk level: {state.risk_level}")
            reporting_state.messages.append(f"Priority actions: {len(state.priority_actions)}")
            
            # Run reporting
            result = reporting_agent.generate_security_report(reporting_state)
            
            # Enhance report with coordination analysis
            if "executive_summary" in result:
                result["executive_summary"]["coordination_analysis"] = {
                    "overall_risk_level": state.risk_level,
                    "priority_actions": state.priority_actions,
                    "multi_agent_status": {
                        "integrity_complete": state.integrity_complete,
                        "threat_complete": state.threat_complete,
                        "intrusion_complete": state.intrusion_complete
                    }
                }
            
            state.reporting_results = result
            state.reporting_complete = True
            state.overall_status = "complete"
            state.messages.append("Comprehensive reporting completed")
            
        except Exception as e:
            logger.error(f"Error in reporting agent: {e}")
            state.messages.append(f"Reporting agent failed: {str(e)}")
            state.reporting_results = {"error": str(e), "status": "failed"}
            state.overall_status = "reporting_failed"
        
        return state
    
    def execute_cybersecurity_analysis(self) -> Dict[str, Any]:
        """Execute the complete cybersecurity multi-agent analysis"""
        try:
            logger.info("Starting cybersecurity multi-agent analysis")
            
            # Initialize state
            initial_state = CybersecurityGraphState()
            
            # Execute the graph
            final_state = self.graph.invoke(initial_state)
            
            # Compile comprehensive results
            return {
                "timestamp": datetime.now().isoformat(),
                "overall_status": final_state.overall_status,
                "risk_level": final_state.risk_level,
                "priority_actions": final_state.priority_actions,
                "agent_results": {
                    "data_integrity": final_state.integrity_results,
                    "threat_detection": final_state.threat_results,
                    "intrusion_response": final_state.intrusion_results,
                    "reporting": final_state.reporting_results
                },
                "completion_status": {
                    "integrity_complete": final_state.integrity_complete,
                    "threat_complete": final_state.threat_complete,
                    "intrusion_complete": final_state.intrusion_complete,
                    "reporting_complete": final_state.reporting_complete
                },
                "messages": final_state.messages,
                "status": "multi_agent_analysis_complete"
            }
            
        except Exception as e:
            logger.error(f"Error in cybersecurity graph execution: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "status": "multi_agent_analysis_failed"
            }
    
    def execute_targeted_analysis(self, focus_area: str) -> Dict[str, Any]:
        """Execute analysis focused on specific area"""
        try:
            if focus_area == "integrity":
                result = data_integrity_agent.validate_data_integrity()
            elif focus_area == "threats":
                result = threat_detection_agent.detect_threats()
            elif focus_area == "intrusion":
                result = intrusion_response_agent.respond_to_intrusion()
            elif focus_area == "reporting":
                result = reporting_agent.generate_security_report()
            else:
                return self.execute_cybersecurity_analysis()
            
            return {
                "timestamp": datetime.now().isoformat(),
                "focus_area": focus_area,
                "result": result,
                "status": "targeted_analysis_complete"
            }
            
        except Exception as e:
            logger.error(f"Error in targeted analysis: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "status": "targeted_analysis_failed"
            }

# Create graph instance
cybersecurity_graph = CybersecurityGraph()