# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is an **AI-Powered Smart Lighting System** with a microservices-based architecture using LangGraph multi-agent workflows. The system consists of three specialized agent services (Cybersecurity, Weather Intelligence, and Power Grid Management) orchestrated by a central Coordinator, all communicating via Kafka.

## Development Commands

### Docker Operations

```bash
# Build all containers (required on first run)
docker-compose build

# Start all services
docker-compose up

# Start specific services
docker-compose up cybersecurity-agent weather-agent power-agent coordinator-agent

# Scale a service
docker-compose up --scale power-agent=2

# View logs for a specific service
docker-compose logs -f cybersecurity-agent
docker-compose logs -f weather-agent
docker-compose logs -f power-agent
docker-compose logs -f coordinator-agent

# Stop all services
docker-compose down
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run development server (port 4000)
npm run dev

# Build production
npm run build

# Run production server
npm start

# Lint code
npm run lint
```

### Service Health Checks

```bash
# Check individual service health
curl http://localhost:8000/health  # Cybersecurity (port 8000)
curl http://localhost:8001/health  # Weather (port 8001)
curl http://localhost:8002/health  # Power Grid (port 8002)
curl http://localhost:8004/health  # Coordinator (port 8004)

# View API documentation (when services are running)
# http://localhost:8000/docs (Cybersecurity)
# http://localhost:8001/docs (Weather)
# http://localhost:8002/docs (Power Grid)
# http://localhost:8004/docs (Coordinator)
```

### Monitoring & Infrastructure

```bash
# Kafka UI: http://localhost:8080
# Prometheus: http://localhost:9090
# Grafana (main): http://localhost:3000 (admin/admin123)
# Grafana (power): http://localhost:3002 (admin/admin123)
```

## Architecture

### Multi-Agent LangGraph Architecture

Each backend service uses **LangGraph** to orchestrate multiple specialized agents in a directed graph workflow:

1. **Coordinator Service** (port 8004)
   - Central decision-making hub that receives data from all services via Kafka
   - Uses `PriorityManager` to determine the most critical concern across all services
   - Uses `DecisionEngine` (LLM-powered) to generate coordinated system-wide commands
   - Graph flow: `priority_manager` → `decision_engine` → END
   - Located in: `backend/coordinator/src/graph/coordinator_graph.py`

2. **Weather Intelligence Service** (port 8001)
   - Master graph coordinates 5 specialized agents with conditional routing
   - Agents: Weather Collection, Environmental Sensor, Impact Analyzer, Disaster Response, Reporting
   - Supports 3 execution modes: `normal`, `emergency`, `maintenance`
   - Complex graph with parallel and conditional execution paths
   - Located in: `backend/weather/src/graph/weather_graph.py`

3. **Power Grid Service** (port 8002)
   - Master graph orchestrates 5 agents with conditional outage handling
   - Agents: Load Forecaster, Outage Detector, Energy Router, Optimizer, Reporter
   - Conditional routing based on outage severity (normal/rerouting/emergency paths)
   - Includes emergency response node for critical situations
   - Located in: `backend/power/src/graph/power_graph.py`

4. **Cybersecurity Service** (port 8000)
   - Sequential graph coordinates 4 agents with coordination analysis
   - Agents: Data Integrity, Threat Detection, Intrusion Response, Reporting
   - Includes a coordination analysis node between intrusion response and reporting
   - Located in: `backend/cybersecurity/src/graph/cybersecurity_graph.py`

### Communication Pattern

```
[Weather Service] ─┐
                   │
[Power Service]   ─┼─→ [Kafka Topics] ─→ [Coordinator Service] ─→ System Commands
                   │
[Cyber Service]   ─┘
```

- Each service publishes alerts/reports to Kafka topics
- Coordinator consumes from all topics and makes unified decisions
- Services also consume coordinator commands to adjust behavior

### Backend Structure (Common Patterns)

Each backend service follows this structure:
```
backend/{service}/
├── src/
│   ├── agents/           # Individual agent implementations
│   ├── graph/            # LangGraph workflow definitions
│   ├── kafka/            # Kafka producer/consumer
│   ├── config/           # Settings and configuration
│   └── main.py           # FastAPI application entry point
├── tests/                # Agent tests
├── Dockerfile
└── requirements.txt
```

### Frontend Architecture

- **Framework**: Next.js 16 (React 19) with TypeScript
- **State Management**: Zustand (`frontend/src/store/useDashboardStore.ts`)
- **Styling**: Tailwind CSS v4
- **Component Structure**:
  - `components/shared/`: Reusable UI components (Card, LoadingSpinner)
  - `components/layout/`: Layout components (Header, Sidebar)
  - `components/dashboard/`: Agent-specific displays
  - `components/overview/`: System overview dashboard
- **API Layer**: `frontend/src/utils/api/` - Organized by service (weather, power, cybersecurity)

## Key Technologies

- **AI Framework**: LangChain + LangGraph for multi-agent orchestration
- **LLM Provider**: Groq (with llama3-8b-8192 model primarily)
- **API Framework**: FastAPI (async)
- **Message Broker**: Apache Kafka + Zookeeper
- **Databases**: PostgreSQL (shared), Redis (caching)
- **Monitoring**: Prometheus + Grafana
- **Frontend**: Next.js 16, React 19, TypeScript, Tailwind CSS v4

## Important Implementation Notes

### LangGraph State Management

- Each service defines a custom state class (TypedDict or Pydantic BaseModel)
- State flows through graph nodes and is updated immutably
- Weather and Power graphs use dict-based states
- Cybersecurity graph uses Pydantic BaseModel for state validation
- Coordinator graph uses TypedDict for simple state structure

### Kafka Topics

Services communicate via Kafka topics with this pattern:
- `{service}_alerts`: Critical alerts (e.g., `cyber_alerts`, `weather_alerts`, `power_alerts`)
- `{service}_reports`: Regular reports (e.g., `cyber_reports`, `weather_reports`, `power_reports`)
- `coordinator_commands`: System-wide commands from coordinator

### Configuration

- **Environment Variables**: Each service uses `.env` files
- **Required Keys**: `GROQ_API_KEY`, `WEATHERAPI_API_KEY` (for weather service)
- **Kafka Config**: `KAFKA_BOOTSTRAP_SERVERS` (default: `kafka:29092` in Docker)
- **Service Ports**: See docker-compose.yml for port mappings

### Common Utilities

The `backend/common/` directory contains shared utilities (currently placeholders):
- `config.py`: Shared configuration
- `database.py`: Database utilities
- `kafka_utils.py`: Kafka helpers
- `logger.py`: Logging configuration
- `metrics.py`: Prometheus metrics
- `schemas.py`: Shared data schemas

**Note**: These files exist but are empty - implementations are currently service-specific.

### Coordinator Decision Logic

The DecisionEngine uses an LLM to make system-wide decisions based on:
1. **Primary Concern** from PriorityManager (e.g., CYBER_CRITICAL, POWER_OUTAGE)
2. **Full System State** from all services

Command priority hierarchy:
- CYBER_CRITICAL → Immediate lockdown (overrides everything)
- POWER_OUTAGE → Emergency power mode (critical zones only)
- WEATHER_DISASTER → Max visibility for public safety
- POWER_OPTIMIZATION → Energy efficiency (nominal conditions)
- NOMINAL_OPERATION → Standard adaptive operation

## Development Workflow

1. **Start Infrastructure**: `docker-compose up kafka zookeeper redis postgres prometheus grafana`
2. **Start Backend Services**: `docker-compose up cybersecurity-agent weather-agent power-agent coordinator-agent`
3. **Start Frontend**: `cd frontend && npm run dev`
4. **Monitor**: Check Grafana dashboards, Kafka UI, and Prometheus metrics

## Testing

Individual agent tests are located in `backend/{service}/tests/test_agent.py`. Run tests within the Docker container or set up a local Python environment with the service's `requirements.txt`.

## Git Workflow

- **Main Branch**: `main`
- Current status: Clean working tree
- Recent commits focus on health checks, frontend connectivity, agent functionality, and microservice architecture

## API Integration

All services expose FastAPI endpoints with automatic OpenAPI documentation at `/docs`. The frontend consumes these APIs through the abstraction layer in `frontend/src/utils/api/`.
