import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel
from kafka import KafkaConsumer
from ..config.settings import config

logger = logging.getLogger(__name__)

class DataIntegrityState(BaseModel):
    """State for data integrity operations"""
    messages: list = []
    sensor_data: list = []
    integrity_results: Dict[str, Any] = {}
    validation_status: str = "pending"
    tampering_detected: bool = False
    recommendations: list = []

class DataIntegrityAgent:
    """
    LangGraph agent for monitoring and validating data integrity across sensors.
    Detects tampering, validates checksums, and ensures data authenticity.
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
        """Create LangGraph workflow for data integrity validation"""
        workflow = StateGraph(DataIntegrityState)
        
        # Add nodes
        workflow.add_node("collect_sensor_data", self._collect_sensor_data)
        workflow.add_node("validate_checksums", self._validate_checksums)
        workflow.add_node("detect_tampering", self._detect_tampering)
        workflow.add_node("analyze_integrity", self._analyze_integrity)
        workflow.add_node("generate_recommendations", self._generate_recommendations)
        
        # Define edges
        workflow.set_entry_point("collect_sensor_data")
        workflow.add_edge("collect_sensor_data", "validate_checksums")
        workflow.add_edge("validate_checksums", "detect_tampering")
        workflow.add_edge("detect_tampering", "analyze_integrity")
        workflow.add_edge("analyze_integrity", "generate_recommendations")
        workflow.add_edge("generate_recommendations", END)
        
        return workflow.compile()
    
    def _collect_sensor_data(self, state: DataIntegrityState) -> DataIntegrityState:
        """Collect sensor data from Kafka"""
        try:
            consumer = KafkaConsumer(
                'cyber_alerts',
                bootstrap_servers=self.kafka_config['bootstrap_servers'],
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                consumer_timeout_ms=3000,
                auto_offset_reset='latest'
            )
            
            sensor_data = []
            cutoff_time = datetime.now() - timedelta(seconds=300)
            
            for message in consumer:
                try:
                    data = message.value
                    if data.get('event_type') == 'sensor_data':
                        msg_time = datetime.fromisoformat(data.get('timestamp', ''))
                        if msg_time > cutoff_time:
                            sensor_data.append(data)
                except Exception as e:
                    logger.warning(f"Error parsing sensor message: {e}")
                    continue
            
            consumer.close()
            
            state.sensor_data = sensor_data
            state.messages.append(f"Collected {len(sensor_data)} sensor data points")
            
        except Exception as e:
            logger.error(f"Error collecting sensor data: {e}")
            state.messages.append(f"Data collection failed: {str(e)}")
        
        return state
    
    def _validate_checksums(self, state: DataIntegrityState) -> DataIntegrityState:
        """Validate data checksums for integrity"""
        if not state.sensor_data:
            state.messages.append("No sensor data available for checksum validation")
            return state
        
        valid_count = 0
        invalid_count = 0
        missing_count = 0
        validation_details = []
        
        for data in state.sensor_data:
            source_id = data.get('source_id', 'unknown')
            provided_checksum = data.get('checksum')
            
            if not provided_checksum:
                missing_count += 1
                validation_details.append({
                    "source_id": source_id,
                    "status": "missing_checksum",
                    "timestamp": data.get('timestamp')
                })
                continue
            
            # Calculate expected checksum (simplified)
            expected_checksum = self._calculate_checksum(data)
            
            if provided_checksum == expected_checksum:
                valid_count += 1
            else:
                invalid_count += 1
                validation_details.append({
                    "source_id": source_id,
                    "status": "invalid_checksum",
                    "timestamp": data.get('timestamp')
                })
        
        integrity_score = (valid_count / len(state.sensor_data) * 100) if state.sensor_data else 0
        
        state.integrity_results["checksum_validation"] = {
            "total_validated": len(state.sensor_data),
            "valid_checksums": valid_count,
            "invalid_checksums": invalid_count,
            "missing_checksums": missing_count,
            "integrity_score": round(integrity_score, 2),
            "validation_details": validation_details[:10]
        }
        
        state.messages.append(f"Checksum validation complete: {integrity_score}% integrity score")
        
        return state
    
    def _detect_tampering(self, state: DataIntegrityState) -> DataIntegrityState:
        """Detect potential data tampering"""
        if not state.sensor_data:
            state.messages.append("No data available for tampering detection")
            return state
        
        tampering_indicators = []
        sources_analyzed = {}
        
        # Group by source
        for data in state.sensor_data:
            source_id = data.get('source_id', 'unknown')
            if source_id not in sources_analyzed:
                sources_analyzed[source_id] = []
            sources_analyzed[source_id].append(data)
        
        # Analyze each source for tampering
        for source_id, source_data in sources_analyzed.items():
            indicators = []
            
            # Check for timestamp anomalies
            timestamps = [d.get('timestamp') for d in source_data if d.get('timestamp')]
            if self._has_timestamp_anomalies(timestamps):
                indicators.append("timestamp_anomalies")
            
            # Check for value anomalies
            if self._has_value_anomalies(source_data):
                indicators.append("value_anomalies")
            
            # Check for checksum patterns
            checksums = [d.get('checksum') for d in source_data if d.get('checksum')]
            if self._has_suspicious_checksums(checksums):
                indicators.append("suspicious_checksums")
            
            if indicators:
                risk_level = "high" if len(indicators) >= 2 else "medium"
                tampering_indicators.append({
                    "source_id": source_id,
                    "indicators": indicators,
                    "risk_level": risk_level,
                    "data_count": len(source_data)
                })
        
        state.tampering_detected = len(tampering_indicators) > 0
        state.integrity_results["tampering_detection"] = {
            "sources_analyzed": len(sources_analyzed),
            "sources_with_indicators": len(tampering_indicators),
            "tampering_indicators": tampering_indicators
        }
        
        state.messages.append(f"Tampering detection complete: {len(tampering_indicators)} suspicious sources found")
        
        return state
    
    def _analyze_integrity(self, state: DataIntegrityState) -> DataIntegrityState:
        """Analyze overall data integrity using LLM"""
        try:
            analysis_prompt = f"""
            Analyze data integrity results:
            
            Checksum Validation: {state.integrity_results.get('checksum_validation', {})}
            Tampering Detection: {state.integrity_results.get('tampering_detection', {})}
            Total Sensor Data Points: {len(state.sensor_data)}
            
            Provide:
            1. Overall integrity assessment (healthy/concerning/critical)
            2. Key findings and concerns
            3. Risk level (low/medium/high/critical)
            4. Priority areas requiring attention
            
            Be concise and actionable.
            """
            
            response = self.llm.invoke(analysis_prompt)
            
            state.integrity_results["llm_analysis"] = {
                "analysis": response.content,
                "timestamp": datetime.now().isoformat()
            }
            
            state.messages.append("LLM integrity analysis completed")
            
        except Exception as e:
            logger.error(f"Error in LLM analysis: {e}")
            state.messages.append(f"LLM analysis failed: {str(e)}")
        
        return state
    
    def _generate_recommendations(self, state: DataIntegrityState) -> DataIntegrityState:
        """Generate actionable recommendations"""
        recommendations = []
        
        checksum_results = state.integrity_results.get('checksum_validation', {})
        tampering_results = state.integrity_results.get('tampering_detection', {})
        
        # Checksum-based recommendations
        integrity_score = checksum_results.get('integrity_score', 0)
        if integrity_score < 95:
            recommendations.append("Investigate sensors with checksum failures")
        if checksum_results.get('missing_checksums', 0) > 0:
            recommendations.append("Configure missing checksum validation on sensors")
        
        # Tampering-based recommendations
        if state.tampering_detected:
            recommendations.append("Immediately investigate sources with tampering indicators")
            recommendations.append("Review physical security of affected sensors")
        
        # General recommendations
        if integrity_score < 80:
            recommendations.append("Consider sensor replacement or recalibration")
            state.validation_status = "critical"
        elif integrity_score < 90:
            recommendations.append("Schedule maintenance for low-performing sensors")
            state.validation_status = "concerning"
        else:
            state.validation_status = "healthy"
        
        if not recommendations:
            recommendations.append("Continue regular integrity monitoring")
        
        state.recommendations = recommendations
        state.messages.append(f"Generated {len(recommendations)} recommendations")
        
        return state
    
    def _calculate_checksum(self, data: Dict[str, Any]) -> str:
        """Calculate simple checksum for data"""
        import hashlib
        # Create data for hashing (exclude checksum and metadata)
        hash_data = {k: v for k, v in data.items() if k not in ['checksum', 'metadata']}
        sorted_data = json.dumps(hash_data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(sorted_data.encode()).hexdigest()[:16]
    
    def _has_timestamp_anomalies(self, timestamps: list) -> bool:
        """Check for timestamp anomalies"""
        if len(timestamps) < 2:
            return False
        
        try:
            dt_timestamps = [datetime.fromisoformat(ts) for ts in timestamps if ts]
            dt_timestamps.sort()
            
            for i in range(1, len(dt_timestamps)):
                if dt_timestamps[i] <= dt_timestamps[i-1]:
                    return True
                gap = (dt_timestamps[i] - dt_timestamps[i-1]).total_seconds()
                if gap > 3600:  # More than 1 hour gap
                    return True
        except Exception:
            return True
        
        return False
    
    def _has_value_anomalies(self, data_list: list) -> bool:
        """Check for value anomalies in sensor data"""
        for data in data_list:
            sensor_values = data.get('data', {})
            for key, value in sensor_values.items():
                if isinstance(value, (int, float)):
                    if key == 'temperature' and (value < -50 or value > 80):
                        return True
                    if key == 'humidity' and (value < 0 or value > 100):
                        return True
        return False
    
    def _has_suspicious_checksums(self, checksums: list) -> bool:
        """Check for suspicious checksum patterns"""
        if len(checksums) < 2:
            return False
        
        # Check for duplicates or too simple checksums
        if len(checksums) != len(set(checksums)):
            return True
        
        for checksum in checksums:
            if isinstance(checksum, str) and (len(checksum) < 8 or checksum == "0" * len(checksum)):
                return True
        
        return False
    
    def validate_data_integrity(self, initial_state: Optional[DataIntegrityState] = None) -> Dict[str, Any]:
        """Execute the data integrity validation workflow"""
        try:
            if initial_state is None:
                initial_state = DataIntegrityState()
            
            final_state = self.graph.invoke(initial_state)
            
            return {
                "timestamp": datetime.now().isoformat(),
                "validation_status": final_state.validation_status,
                "tampering_detected": final_state.tampering_detected,
                "integrity_results": final_state.integrity_results,
                "recommendations": final_state.recommendations,
                "messages": final_state.messages,
                "data_points_analyzed": len(final_state.sensor_data),
                "status": "validation_complete"
            }
            
        except Exception as e:
            logger.error(f"Error in data integrity validation: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "status": "validation_failed"
            }

# Create agent instance
data_integrity_agent = DataIntegrityAgent()