import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class CybersecurityConfig:
    """Configuration class for cybersecurity agents"""
    
    # Groq API Configuration
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    GROQ_TEMPERATURE: float = float(os.getenv("GROQ_TEMPERATURE", "0.1"))
    GROQ_MAX_TOKENS: int = int(os.getenv("GROQ_MAX_TOKENS", "1024"))
    
    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    KAFKA_CYBER_ALERTS_TOPIC: str = os.getenv("KAFKA_CYBER_ALERTS_TOPIC", "cyber_alerts")
    KAFKA_THREAT_REPORTS_TOPIC: str = os.getenv("KAFKA_THREAT_REPORTS_TOPIC", "threat_reports")
    KAFKA_INCIDENT_REPORTS_TOPIC: str = os.getenv("KAFKA_INCIDENT_REPORTS_TOPIC", "incident_reports")
    KAFKA_CONSUMER_GROUP: str = os.getenv("KAFKA_CONSUMER_GROUP", "cybersecurity_agents")
    KAFKA_TOPIC_COORDINATOR_COMMANDS: str = "coordinator_commands"
    
    # Agent Configuration
    AGENT_TIMEOUT: int = int(os.getenv("AGENT_TIMEOUT", "30"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    
    # Risk Assessment Thresholds
    LOW_RISK_THRESHOLD: float = float(os.getenv("LOW_RISK_THRESHOLD", "0.3"))
    MEDIUM_RISK_THRESHOLD: float = float(os.getenv("MEDIUM_RISK_THRESHOLD", "0.6"))
    HIGH_RISK_THRESHOLD: float = float(os.getenv("HIGH_RISK_THRESHOLD", "0.8"))
    
    # Network Monitoring Configuration
    NETWORK_SCAN_INTERVAL: int = int(os.getenv("NETWORK_SCAN_INTERVAL", "60"))  # seconds
    SUSPICIOUS_IP_THRESHOLD: int = int(os.getenv("SUSPICIOUS_IP_THRESHOLD", "10"))  # requests per minute
    
    # Data Integrity Configuration
    HASH_ALGORITHM: str = os.getenv("HASH_ALGORITHM", "sha256")
    INTEGRITY_CHECK_INTERVAL: int = int(os.getenv("INTEGRITY_CHECK_INTERVAL", "300"))  # seconds
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate that all required configuration is present"""
        required_fields = [
            "GROQ_API_KEY",
            "KAFKA_BOOTSTRAP_SERVERS"
        ]
        
        for field in required_fields:
            if not getattr(cls, field):
                raise ValueError(f"Missing required configuration: {field}")
        
        return True
    
    @classmethod
    def get_kafka_config(cls) -> Dict[str, Any]:
        """Get Kafka configuration dictionary"""
        return {
            "bootstrap_servers": cls.KAFKA_BOOTSTRAP_SERVERS,
            "consumer_group": cls.KAFKA_CONSUMER_GROUP,
            "topics": {
                "cyber_alerts": cls.KAFKA_CYBER_ALERTS_TOPIC,
                "threat_reports": cls.KAFKA_THREAT_REPORTS_TOPIC,
                "incident_reports": cls.KAFKA_INCIDENT_REPORTS_TOPIC
            }
        }
    
    @classmethod
    def get_groq_config(cls) -> Dict[str, Any]:
        """Get Groq LLM configuration dictionary"""
        return {
            "api_key": cls.GROQ_API_KEY,
            "model": cls.GROQ_MODEL,
            "temperature": cls.GROQ_TEMPERATURE,
            "max_tokens": cls.GROQ_MAX_TOKENS
        }

# Create a singleton instance
config = CybersecurityConfig()