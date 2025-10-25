import json
import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from kafka import KafkaProducer
from kafka.errors import KafkaError
from ..config.settings import config

logger = logging.getLogger(__name__)

class CybersecurityKafkaProducer:
    """
    Kafka producer for cybersecurity data publishing.
    Publishes security events, alerts, reports, and agent results.
    """
    
    def __init__(self):
        self.kafka_config = config.get_kafka_config()
        self.producer = None
        self._initialize_producer()
    
    def _initialize_producer(self):
        """Initialize Kafka producer"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.kafka_config['bootstrap_servers'],
                value_serializer=lambda x: json.dumps(x).encode('utf-8'),
                key_serializer=lambda x: x.encode('utf-8') if x else None,
                acks='all',  # Wait for all replicas
                retries=3,
                max_in_flight_requests_per_connection=1,
                enable_idempotence=True,
                compression_type=None
            )
            logger.info("Cybersecurity Kafka producer initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            raise
    
    def publish_security_alert(self, alert_data: Dict[str, Any], severity: str = "medium") -> bool:
        """Publish security alert to cyber_alerts topic"""
        try:
            message = {
                "event_type": "security_alert",
                "alert_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "severity": severity,
                "data": alert_data,
                "source": "cybersecurity_system"
            }
            
            key = f"alert_{message['alert_id']}"
            
            future = self.producer.send('cyber_alerts', key=key, value=message)
            record_metadata = future.get(timeout=10)
            
            logger.info(f"Security alert published: {key} to partition {record_metadata.partition}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish security alert: {e}")
            return False
    
    def publish_threat_detection(self, threat_type: str, confidence: str, 
                               source_ip: Optional[str] = None, details: Dict[str, Any] = None) -> bool:
        """Publish threat detection event"""
        try:
            message = {
                "event_type": "threat_detection",
                "detection_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "threat_type": threat_type,
                "confidence": confidence,
                "source_ip": source_ip,
                "severity": "high" if confidence == "high" else "medium",
                "data": details or {},
                "source": "threat_detection_agent"
            }
            
            key = f"threat_{message['detection_id']}"
            
            future = self.producer.send('cyber_alerts', key=key, value=message)
            record_metadata = future.get(timeout=10)
            
            logger.info(f"Threat detection published: {threat_type} ({confidence} confidence)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish threat detection: {e}")
            return False
    
    def publish_integrity_violation(self, source_id: str, violation_type: str, 
                                  checksum_failed: bool = False, details: Dict[str, Any] = None) -> bool:
        """Publish data integrity violation"""
        try:
            message = {
                "event_type": "data_integrity_violation",
                "violation_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "source_id": source_id,
                "violation_type": violation_type,
                "checksum_failed": checksum_failed,
                "severity": "high" if checksum_failed else "medium",
                "data": details or {},
                "source": "data_integrity_agent"
            }
            
            key = f"violation_{source_id}_{message['violation_id']}"
            
            future = self.producer.send('cyber_alerts', key=key, value=message)
            record_metadata = future.get(timeout=10)
            
            logger.info(f"Integrity violation published: {violation_type} for {source_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish integrity violation: {e}")
            return False
    
    def publish_network_event(self, source_ip: str, event_type: str, 
                            suspicious: bool = False, details: Dict[str, Any] = None) -> bool:
        """Publish network traffic event"""
        try:
            message = {
                "event_type": "network_traffic",
                "event_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "source_ip": source_ip,
                "network_event_type": event_type,
                "suspicious": suspicious,
                "severity": "high" if suspicious else "low",
                "data": details or {},
                "source": "network_monitor"
            }
            
            key = f"network_{source_ip}_{message['event_id']}"
            
            future = self.producer.send('network_events', key=key, value=message)
            record_metadata = future.get(timeout=10)
            
            logger.info(f"Network event published: {event_type} from {source_ip}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish network event: {e}")
            return False
    
    def publish_sensor_data(self, source_id: str, sensor_values: Dict[str, Any], 
                          checksum: Optional[str] = None, tampered: bool = False) -> bool:
        """Publish sensor data event"""
        try:
            message = {
                "event_type": "sensor_data",
                "data_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "source_id": source_id,
                "checksum": checksum,
                "tampered": tampered,
                "checksum_failed": tampered,  # For compatibility
                "severity": "high" if tampered else "low",
                "data": sensor_values,
                "source": "sensor_network"
            }
            
            key = f"sensor_{source_id}_{message['data_id']}"
            
            future = self.producer.send('sensor_data', key=key, value=message)
            record_metadata = future.get(timeout=10)
            
            logger.debug(f"Sensor data published: {source_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish sensor data: {e}")
            return False
    
    def publish_incident_report(self, incident_id: str, report_data: Dict[str, Any]) -> bool:
        """Publish incident report"""
        try:
            message = {
                "report_type": "incident_report",
                "incident_id": incident_id,
                "timestamp": datetime.now().isoformat(),
                "report_data": report_data,
                "source": "reporting_agent"
            }
            
            key = f"incident_{incident_id}"
            
            future = self.producer.send('incident_reports', key=key, value=message)
            record_metadata = future.get(timeout=10)
            
            logger.info(f"Incident report published: {incident_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish incident report: {e}")
            return False
    
    def publish_executive_summary(self, summary_data: Dict[str, Any]) -> bool:
        """Publish executive summary report"""
        try:
            message = {
                "report_type": "executive_summary",
                "summary_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "summary_data": summary_data,
                "source": "reporting_agent"
            }
            
            key = f"summary_{message['summary_id']}"
            
            future = self.producer.send('executive_reports', key=key, value=message)
            record_metadata = future.get(timeout=10)
            
            logger.info(f"Executive summary published: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish executive summary: {e}")
            return False
    
    def publish_knowledge_update(self, knowledge_data: Dict[str, Any]) -> bool:
        """Publish knowledge base update for RAG system"""
        try:
            message = {
                "knowledge_type": "cybersecurity_knowledge",
                "update_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "knowledge_data": knowledge_data,
                "source": "cybersecurity_agents"
            }
            
            key = f"knowledge_{message['update_id']}"
            
            future = self.producer.send('rag_knowledge_updates', key=key, value=message)
            record_metadata = future.get(timeout=10)
            
            logger.info(f"Knowledge update published: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish knowledge update: {e}")
            return False
    
    def publish_batch_events(self, events: List[Dict[str, Any]]) -> Dict[str, int]:
        """Publish multiple events in batch"""
        results = {"success": 0, "failed": 0}
        
        for event in events:
            try:
                event_type = event.get("event_type", "unknown")
                
                if event_type == "security_alert":
                    success = self.publish_security_alert(event.get("data", {}), event.get("severity", "medium"))
                elif event_type == "threat_detection":
                    success = self.publish_threat_detection(
                        event.get("threat_type", "unknown"),
                        event.get("confidence", "low"),
                        event.get("source_ip"),
                        event.get("data", {})
                    )
                elif event_type == "network_traffic":
                    success = self.publish_network_event(
                        event.get("source_ip", "unknown"),
                        event.get("network_event_type", "unknown"),
                        event.get("suspicious", False),
                        event.get("data", {})
                    )
                elif event_type == "sensor_data":
                    success = self.publish_sensor_data(
                        event.get("source_id", "unknown"),
                        event.get("data", {}),
                        event.get("checksum"),
                        event.get("tampered", False)
                    )
                else:
                    logger.warning(f"Unknown event type for batch publish: {event_type}")
                    success = False
                
                if success:
                    results["success"] += 1
                else:
                    results["failed"] += 1
                    
            except Exception as e:
                logger.error(f"Error in batch event publish: {e}")
                results["failed"] += 1
        
        logger.info(f"Batch publish complete: {results['success']} success, {results['failed']} failed")
        return results
    
    def flush(self):
        """Flush all pending messages"""
        try:
            self.producer.flush(timeout=30)
            logger.info("Producer flushed successfully")
        except Exception as e:
            logger.error(f"Error flushing producer: {e}")
    
    def close(self):
        """Close the producer"""
        try:
            if self.producer:
                self.producer.flush(timeout=10)
                self.producer.close(timeout=10)
                logger.info("Kafka producer closed")
        except Exception as e:
            logger.error(f"Error closing producer: {e}")
    
    def get_producer_status(self) -> Dict[str, Any]:
        """Get current producer status"""
        return {
            "producer_active": self.producer is not None,
            "config": {
                "bootstrap_servers": self.kafka_config['bootstrap_servers'],
                "compression": "gzip",
                "acks": "all"
            },
            "timestamp": datetime.now().isoformat()
        }

# Create producer instance
cybersecurity_producer = CybersecurityKafkaProducer()