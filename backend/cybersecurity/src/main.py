import logging
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from prometheus_fastapi_instrumentator import Instrumentator
import json

from src.graph.cybersecurity_graph import cybersecurity_graph
from src.kafka.kafka_consumer import cybersecurity_consumer
from src.kafka.kafka_producer import cybersecurity_producer
from src.agents.data_integrity_agent import data_integrity_agent
from src.agents.threat_detection_agent import threat_detection_agent
from src.agents.intrusion_response_agent import intrusion_response_agent
from src.agents.reporting_agent import reporting_agent
from src.config.settings import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.last_update_data = {
            "status": None,
            "metrics": None,
            "last_analysis": None
        }

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
        
        # Send current data immediately
        if self.last_update_data["status"]:
            await websocket.send_text(json.dumps({
                "type": "status_update",
                "data": self.last_update_data["status"],
                "timestamp": datetime.now().isoformat()
            }))
        
        if self.last_update_data["metrics"]:
            await websocket.send_text(json.dumps({
                "type": "metrics_update", 
                "data": self.last_update_data["metrics"],
                "timestamp": datetime.now().isoformat()
            }))

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast_status_update(self, status_data: Dict[str, Any]):
        self.last_update_data["status"] = status_data
        message = json.dumps({
            "type": "status_update",
            "data": status_data,
            "timestamp": datetime.now().isoformat()
        })
        
        for connection in self.active_connections.copy():
            try:
                await connection.send_text(message)
            except:
                # Remove disconnected connections
                self.active_connections.remove(connection)

    async def broadcast_metrics_update(self, metrics_data: Dict[str, Any]):
        self.last_update_data["metrics"] = metrics_data
        message = json.dumps({
            "type": "metrics_update",
            "data": metrics_data,
            "timestamp": datetime.now().isoformat()
        })
        
        for connection in self.active_connections.copy():
            try:
                await connection.send_text(message)
            except:
                # Remove disconnected connections
                self.active_connections.remove(connection)

    async def broadcast_analysis_result(self, analysis_data: Dict[str, Any]):
        self.last_update_data["last_analysis"] = analysis_data
        message = json.dumps({
            "type": "analysis_result",
            "data": analysis_data,
            "timestamp": datetime.now().isoformat()
        })
        
        for connection in self.active_connections.copy():
            try:
                await connection.send_text(message)
            except:
                # Remove disconnected connections
                self.active_connections.remove(connection)

# Global connection manager
manager = ConnectionManager()

# Request/Response Models
class SecurityAnalysisRequest(BaseModel):
    analysis_type: str = "full"  # full, integrity, threats, intrusion, reporting
    time_window: int = 300
    priority: str = "normal"  # normal, high, critical

class ThreatAlertRequest(BaseModel):
    threat_type: str
    confidence: str
    source_ip: Optional[str] = None
    details: Dict[str, Any] = {}

class IntegrityCheckRequest(BaseModel):
    source_id: Optional[str] = None
    time_window: int = 300

class NetworkEventRequest(BaseModel):
    source_ip: str
    event_type: str
    suspicious: bool = False
    details: Dict[str, Any] = {}

class BatchEventsRequest(BaseModel):
    events: list
    priority: str = "normal"

# Lifespan manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Cybersecurity FastAPI Server")
    
    try:
        # Start Kafka consumer
        cybersecurity_consumer.start_consuming()
        logger.info("Kafka consumer started")
        
        # Verify producer
        status = cybersecurity_producer.get_producer_status()
        logger.info(f"Kafka producer status: {status['producer_active']}")
        
        # Start background task for periodic updates
        asyncio.create_task(periodic_updates())
        logger.info("Background periodic updates started")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Cybersecurity Server")
    
    try:
        cybersecurity_consumer.stop_consuming()
        cybersecurity_producer.close()
        logger.info("Kafka connections closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# Background task for periodic updates
async def periodic_updates():
    """Send periodic status and metrics updates to WebSocket clients"""
    while True:
        try:
            # Update agent status
            status_data = {
                "agents": {
                    "data_integrity": "active",
                    "threat_detection": "active", 
                    "intrusion_response": "active",
                    "reporting": "active"
                },
                "graph": "active",
                "timestamp": datetime.now().isoformat()
            }
            await manager.broadcast_status_update(status_data)
            
            # Update metrics
            metrics_data = {
                "metrics": {
                    "total_analyses": "tracked_in_production",
                    "threats_detected": "tracked_in_production",
                    "incidents_resolved": "tracked_in_production",
                    "average_response_time": "tracked_in_production"
                },
                "current_status": {
                    "threat_level": "normal",
                    "active_incidents": 0,
                    "system_health": "good"
                },
                "timestamp": datetime.now().isoformat()
            }
            await manager.broadcast_metrics_update(metrics_data)
            
        except Exception as e:
            logger.error(f"Error in periodic updates: {e}")
        
        # Wait 30 seconds before next update
        await asyncio.sleep(30)

# Create FastAPI app
app = FastAPI(
    title="Cybersecurity AI Agent Service",
    description="Multi-agent cybersecurity system with threat detection, intrusion response, and reporting",
    version="1.0.0",
    lifespan=lifespan
)

# Add Prometheus metrics instrumentation
Instrumentator().instrument(app).expose(app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "cybersecurity-agent",
        "timestamp": datetime.now().isoformat()
    }

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle any incoming messages
            data = await websocket.receive_text()
            # Echo back for ping/pong or handle specific commands
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# Main analysis endpoints
@app.post("/analyze/security")
async def analyze_security(request: SecurityAnalysisRequest, background_tasks: BackgroundTasks):
    """Execute comprehensive security analysis"""
    try:
        logger.info(f"Security analysis requested: {request.analysis_type}")
        
        if request.analysis_type == "full":
            # Run full multi-agent analysis
            result = cybersecurity_graph.execute_cybersecurity_analysis()
        else:
            # Run targeted analysis
            result = cybersecurity_graph.execute_targeted_analysis(request.analysis_type)
        
        # Publish results in background
        if result.get("status") == "multi_agent_analysis_complete":
            background_tasks.add_task(
                cybersecurity_producer.publish_knowledge_update,
                {"analysis_result": result, "analysis_type": request.analysis_type}
            )
        
        # Broadcast analysis result to WebSocket clients
        analysis_response = {
            "analysis_id": f"ANALYSIS_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "request": request.dict(),
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        background_tasks.add_task(manager.broadcast_analysis_result, analysis_response)
        
        return analysis_response
        
    except Exception as e:
        logger.error(f"Error in security analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/analyze/integrity")
async def check_data_integrity(request: IntegrityCheckRequest):
    """Check data integrity for specific source or all sources"""
    try:
        logger.info(f"Data integrity check requested for: {request.source_id or 'all sources'}")
        
        result = data_integrity_agent.validate_data_integrity()
        
        return {
            "check_id": f"INTEGRITY_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "source_id": request.source_id,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in integrity check: {e}")
        raise HTTPException(status_code=500, detail=f"Integrity check failed: {str(e)}")

@app.post("/analyze/threats")
async def detect_threats():
    """Detect and analyze current threats"""
    try:
        logger.info("Threat detection requested")
        
        result = threat_detection_agent.detect_threats()
        
        return {
            "detection_id": f"THREAT_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in threat detection: {e}")
        raise HTTPException(status_code=500, detail=f"Threat detection failed: {str(e)}")

@app.post("/respond/intrusion")
async def respond_to_intrusion():
    """Execute intrusion response analysis"""
    try:
        logger.info("Intrusion response requested")
        
        result = intrusion_response_agent.respond_to_intrusion()
        
        return {
            "response_id": f"INTRUSION_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in intrusion response: {e}")
        raise HTTPException(status_code=500, detail=f"Intrusion response failed: {str(e)}")

@app.post("/reports/generate")
async def generate_report():
    """Generate comprehensive security report"""
    try:
        logger.info("Security report generation requested")
        
        result = reporting_agent.generate_security_report()
        
        return {
            "report_id": f"REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in report generation: {e}")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

# Event publishing endpoints
@app.post("/events/threat")
async def publish_threat_alert(request: ThreatAlertRequest):
    """Publish threat detection event"""
    try:
        success = cybersecurity_producer.publish_threat_detection(
            request.threat_type,
            request.confidence,
            request.source_ip,
            request.details
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to publish threat alert")
        
        return {
            "event_id": f"THREAT_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "published": True,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error publishing threat alert: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to publish threat: {str(e)}")

@app.post("/events/network")
async def publish_network_event(request: NetworkEventRequest):
    """Publish network event"""
    try:
        success = cybersecurity_producer.publish_network_event(
            request.source_ip,
            request.event_type,
            request.suspicious,
            request.details
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to publish network event")
        
        return {
            "event_id": f"NETWORK_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "published": True,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error publishing network event: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to publish network event: {str(e)}")

@app.post("/events/batch")
async def publish_batch_events(request: BatchEventsRequest):
    """Publish multiple events in batch"""
    try:
        results = cybersecurity_producer.publish_batch_events(request.events)
        
        return {
            "batch_id": f"BATCH_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "results": results,
            "total_events": len(request.events),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in batch publish: {e}")
        raise HTTPException(status_code=500, detail=f"Batch publish failed: {str(e)}")

# Status and monitoring endpoints
@app.get("/status/agents")
async def get_agents_status():
    """Get status of all agents"""
    return {
        "agents": {
            "data_integrity": "active",
            "threat_detection": "active", 
            "intrusion_response": "active",
            "reporting": "active"
        },
        "graph": "active",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/status/kafka")
async def get_kafka_status():
    """Get Kafka consumer and producer status"""
    return {
        "consumer": cybersecurity_consumer.get_consumer_status(),
        "producer": cybersecurity_producer.get_producer_status(),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/metrics/security")
async def get_security_metrics():
    """Get security metrics and statistics"""
    try:
        # This could be enhanced with actual metrics from a database
        return {
            "metrics": {
                "total_analyses": "tracked_in_production",
                "threats_detected": "tracked_in_production",
                "incidents_resolved": "tracked_in_production",
                "average_response_time": "tracked_in_production"
            },
            "current_status": {
                "threat_level": "normal",
                "active_incidents": 0,
                "system_health": "good"
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting security metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")

# Emergency endpoints
@app.post("/emergency/analysis")
async def emergency_analysis(background_tasks: BackgroundTasks):
    """Trigger emergency security analysis"""
    try:
        logger.warning("Emergency security analysis triggered")
        
        # Run immediate full analysis
        result = cybersecurity_graph.execute_cybersecurity_analysis()
        
        # Publish emergency alert
        background_tasks.add_task(
            cybersecurity_producer.publish_security_alert,
            {"emergency_analysis": result},
            "critical"
        )
        
        return {
            "emergency_id": f"EMERGENCY_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "result": result,
            "alert_published": True,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in emergency analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Emergency analysis failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )