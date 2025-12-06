# DataMigrate AI - Developer Guide

## Complete Development Documentation
**Version:** 1.0.0
**Last Updated:** December 2024
**Author:** Alexander Garcia Angus (kether180)
**Property of:** OKO Investments

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture](#2-architecture)
3. [Technology Stack](#3-technology-stack)
4. [Getting Started](#4-getting-started)
5. [Agent System](#5-agent-system)
6. [Book Insights Implementation](#6-book-insights-implementation)
7. [API Reference](#7-api-reference)
8. [Testing](#8-testing)
9. [Deployment](#9-deployment)
10. [Development Workflow](#10-development-workflow)

---

## 1. Project Overview

### What is DataMigrate AI?

DataMigrate AI is an enterprise-grade AI-powered platform for automating MSSQL database migrations to dbt (data build tool) projects. It uses a multi-agent AI architecture to:

- Extract metadata from MSSQL databases
- Generate dbt projects with staging, intermediate, and marts layers
- Validate migrations with self-healing capabilities
- Deploy to modern data warehouses (Snowflake, Databricks, BigQuery, Redshift)
- Provide RAG-powered documentation and support

### Key Features

- **11 AI Agents** - Specialized agents for each migration task
- **Actor-Critic Validation** - Self-healing migration validation
- **MAESTRO Security** - 7-layer enterprise security framework
- **Multi-language Support** - 7 languages (EN, ES, FR, DE, DA, NL, PT)
- **Real-time Progress** - Live migration tracking
- **RAG Documentation** - AI-powered contextual help

---

## 2. Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Vue.js 3)                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │Dashboard │ │Migrations│ │  Agents  │ │ Settings │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTP/REST
┌─────────────────────────▼───────────────────────────────────────┐
│                    GO BACKEND (Gin Framework)                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │   JWT    │ │  CORS    │ │ Guardian │ │ Metrics  │           │
│  │   Auth   │ │Middleware│ │ Security │ │Prometheus│           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTP/REST
┌─────────────────────────▼───────────────────────────────────────┐
│                 PYTHON AI SERVICE (FastAPI)                      │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    LangGraph Orchestration                   ││
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           ││
│  │  │ Extract │→│Generate │→│Validate │→│ Execute │           ││
│  │  │  Node   │ │  Node   │ │  Node   │ │  Node   │           ││
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘           ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                      11 AI AGENTS                            ││
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐   ││
│  │  │  MSSQL    │ │    dbt    │ │    dbt    │ │   Data    │   ││
│  │  │ Extractor │ │ Generator │ │ Executor  │ │  Quality  │   ││
│  │  │   95%     │ │    95%    │ │    70%    │ │    60%    │   ││
│  │  └───────────┘ └───────────┘ └───────────┘ └───────────┘   ││
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐   ││
│  │  │Validation │ │    RAG    │ │  DataPrep │ │   Docs    │   ││
│  │  │  Agent    │ │  Service  │ │   Agent   │ │  Agent    │   ││
│  │  │    50%    │ │    85%    │ │    30%    │ │    25%    │   ││
│  │  └───────────┘ └───────────┘ └───────────┘ └───────────┘   ││
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐                 ││
│  │  │    BI     │ │    ML     │ │ Guardian  │                 ││
│  │  │   Agent   │ │Fine-Tuning│ │   Agent   │                 ││
│  │  │    20%    │ │    15%    │ │    40%    │                 ││
│  │  └───────────┘ └───────────┘ └───────────┘                 ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                      DATA LAYER                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  PostgreSQL  │  │   pgvector   │  │    MSSQL     │          │
│  │   (State)    │  │    (RAG)     │  │   (Source)   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
AI-Agent-MSSQL-DBT/
├── agents/                    # Python AI Agents (~12,000 lines)
│   ├── api.py                # FastAPI service (2,500+ lines)
│   ├── mssql_extractor.py    # MSSQL metadata extraction
│   ├── dbt_generator.py      # dbt project generation
│   ├── dbt_executor.py       # dbt command execution
│   ├── validation_agent.py   # Schema validation + Actor-Critic
│   ├── data_quality_agent.py # Data quality scanning
│   ├── rag_service_v2.py     # Advanced RAG with pgvector
│   ├── guardian_agent.py     # MAESTRO security framework
│   ├── dataprep_agent.py     # Data preparation
│   ├── documentation_agent.py# Auto documentation
│   ├── bi_agent.py           # Business intelligence
│   ├── ml_finetuning_agent.py# ML model training
│   ├── graph.py              # LangGraph workflow
│   ├── native_nodes.py       # Graph nodes
│   ├── state.py              # State management
│   ├── guardrails.py         # Security guardrails
│   └── tests/                # Unit tests (40 tests)
│
├── backend/                   # Go API Server
│   ├── cmd/server/           # Entry point
│   └── internal/
│       ├── api/              # REST endpoints
│       ├── db/               # PostgreSQL layer
│       ├── middleware/       # JWT, CORS
│       └── security/         # Guardian Agent (Go)
│
├── frontend/                  # Vue.js 3 Frontend
│   └── src/
│       ├── views/            # 18 page components
│       ├── components/       # Reusable components
│       ├── stores/           # Pinia state
│       ├── services/         # API client
│       └── i18n/             # 7 languages
│
├── dbt_projects/             # Generated migrations
├── docs/                     # Documentation
│   └── agent-docs/           # This folder
├── infrastructure/           # Docker, K8s, Terraform
└── tests/                    # Integration tests
```

---

## 3. Technology Stack

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| Vue.js | 3.5 | UI Framework |
| TypeScript | 5.x | Type Safety |
| Vite | 7.2 | Build Tool |
| Tailwind CSS | 4.1 | Styling |
| Pinia | 3.0 | State Management |
| Vue Router | 4.6 | Routing |
| Vue i18n | 9.14 | Internationalization |
| Axios | 1.13 | HTTP Client |

### Backend (Go)
| Technology | Version | Purpose |
|------------|---------|---------|
| Go | 1.24 | Server Language |
| Gin | 1.11 | Web Framework |
| PostgreSQL | 16 | Database |
| JWT | - | Authentication |
| Prometheus | - | Metrics |

### AI Service (Python)
| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.12 | Language |
| FastAPI | 0.109 | API Framework |
| LangGraph | 0.0.40+ | Agent Orchestration |
| LangChain | 0.1+ | LLM Integration |
| Anthropic | 0.39+ | Claude AI |
| dbt-core | 1.7+ | Data Transformation |
| pyodbc | 5.0 | MSSQL Connection |
| pgvector | - | RAG Embeddings |

### Infrastructure
| Technology | Purpose |
|------------|---------|
| Docker | Containerization |
| Railway | Production Hosting |
| GitHub Actions | CI/CD |
| PostgreSQL + pgvector | Vector Database |

---

## 4. Getting Started

### Prerequisites

```bash
# Required installations
- Python 3.12+
- Go 1.24+
- Node.js 20+
- PostgreSQL 16+ with pgvector
- ODBC Driver 17 for SQL Server
```

### Local Development Setup

```bash
# 1. Clone the repository
git clone https://github.com/Kether180/AI-Agent-MSSQL-DBT.git
cd AI-Agent-MSSQL-DBT

# 2. Set up environment variables
cp .env.example .env
# Edit .env with your API keys and database credentials

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install frontend dependencies
cd frontend && npm install && cd ..

# 5. Install Go dependencies
cd backend && go mod download && cd ..

# 6. Start all services
# Terminal 1: Python AI Service
cd agents && python -m uvicorn api:app --port 8001 --reload

# Terminal 2: Go Backend
cd backend && go run cmd/server/main.go

# Terminal 3: Frontend
cd frontend && npm run dev
```

### Environment Variables

```env
# Required
ANTHROPIC_API_KEY=sk-ant-...
JWT_SECRET=your-secure-jwt-secret
DB_HOST=localhost
DB_PORT=5432
DB_NAME=datamigrate
DB_USER=postgres
DB_PASSWORD=your-password

# Optional
OPENAI_API_KEY=sk-...
VOYAGE_API_KEY=...
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
```

---

## 5. Agent System

### Agent Registry

| Agent | File | Status | Completion |
|-------|------|--------|------------|
| MSSQL Extractor | `mssql_extractor.py` | Production | 95% |
| dbt Generator | `dbt_generator.py` | Production | 95% |
| dbt Executor | `dbt_executor.py` | Beta | 70% |
| Data Quality | `data_quality_agent.py` | Beta | 60% |
| Validation Agent | `validation_agent.py` | Beta | 50% |
| RAG Service | `rag_service_v2.py` | Beta | 85% |
| Guardian Agent | `guardian_agent.py` | Alpha | 40% |
| DataPrep Agent | `dataprep_agent.py` | Alpha | 30% |
| Documentation Agent | `documentation_agent.py` | Alpha | 25% |
| BI Agent | `bi_agent.py` | Alpha | 20% |
| ML Fine-Tuning | `ml_finetuning_agent.py` | Alpha | 15% |

### Agent Workflow

```
┌──────────────┐
│   User       │
│   Request    │
└──────┬───────┘
       │
       ▼
┌──────────────┐     ┌──────────────┐
│   Guardian   │────▶│   Input      │
│   Agent      │     │   Validation │
└──────┬───────┘     └──────────────┘
       │
       ▼
┌──────────────┐
│   MSSQL      │
│   Extractor  │ ──── Extract metadata from source
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   dbt        │
│   Generator  │ ──── Create dbt project
└──────┬───────┘
       │
       ▼
┌──────────────┐     ┌──────────────┐
│   Validation │────▶│ Actor-Critic │
│   Agent      │     │    Loop      │
└──────┬───────┘     └──────────────┘
       │
       ▼
┌──────────────┐
│   dbt        │
│   Executor   │ ──── Deploy to warehouse
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Complete   │
└──────────────┘
```

---

## 6. Book Insights Implementation

### Source
"Building Applications with AI Agents" by Michael Albada (O'Reilly, 2025)

### Implemented Patterns

#### 6.1 Actor-Critic Validation Pattern

**Location:** `agents/validation_agent.py`

**Purpose:** Self-healing migration validation that automatically fixes common issues.

**How it works:**
```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  Actor   │────▶│  Critic  │────▶│  Score   │
│(Generate)│     │(Validate)│     │  Check   │
└──────────┘     └──────────┘     └────┬─────┘
                                       │
                      ┌────────────────┴────────────────┐
                      │                                 │
                      ▼                                 ▼
               Score >= 95%                      Score < 95%
                      │                                 │
                      ▼                                 ▼
               ┌──────────┐                     ┌──────────┐
               │ Approved │                     │ Auto-Fix │
               └──────────┘                     │  Issues  │
                                                └────┬─────┘
                                                     │
                                                     ▼
                                                ┌──────────┐
                                                │ Re-check │
                                                │ (max 3x) │
                                                └──────────┘
```

**Quality Rubric:**
| Dimension | Weight | Threshold |
|-----------|--------|-----------|
| Schema Completeness | 25% | 100% |
| Data Type Accuracy | 20% | 99% |
| Referential Integrity | 15% | 100% |
| dbt Syntax Validity | 20% | 100% |
| Test Coverage | 10% | 80% |
| Documentation Coverage | 10% | 90% |

**Usage:**
```python
from agents.validation_agent import validate_with_actor_critic

result = validate_with_actor_critic(
    project_path="/path/to/dbt/project",
    source_metadata=metadata,
    quality_threshold=0.95,
    max_iterations=3,
    auto_fix=True
)

if result['passed']:
    print("Migration approved!")
else:
    print(f"Needs review: {result['issues_found']}")
```

**API Endpoint:**
```
POST /migrations/{id}/validate-actor-critic
{
    "quality_threshold": 0.95,
    "max_iterations": 3,
    "auto_fix": true
}
```

#### 6.2 MAESTRO Security Framework

**Location:** `agents/guardian_agent.py`

**Purpose:** 7-layer enterprise security model from Cloud Security Alliance.

**Layers:**
```
┌─────────────────────────────────────────────┐
│  Layer 7: Monitoring                        │
│  - Prometheus metrics                       │
│  - Security event alerting                  │
│  - Audit log persistence                    │
├─────────────────────────────────────────────┤
│  Layer 6: Deployment                        │
│  - Railway/Docker security                  │
│  - Environment variable protection          │
│  - Network isolation                        │
├─────────────────────────────────────────────┤
│  Layer 5: Agent Ecosystem                   │
│  - Multi-agent communication security       │
│  - Rate limiting per identifier             │
│  - Organization-based policies              │
├─────────────────────────────────────────────┤
│  Layer 4: Agent Core (Guardian)             │
│  - Prompt injection detection               │
│  - SQL injection prevention                 │
│  - Input/output validation                  │
├─────────────────────────────────────────────┤
│  Layer 3: Agent Framework                   │
│  - LangGraph state isolation                │
│  - Thread safety (locks)                    │
│  - Audit logging                            │
├─────────────────────────────────────────────┤
│  Layer 2: Data Operations                   │
│  - MSSQL connection security                │
│  - Credential encryption                    │
│  - Data exfiltration detection              │
├─────────────────────────────────────────────┤
│  Layer 1: Foundation Models                 │
│  - Anthropic API security                   │
│  - API key management                       │
│  - Model access controls                    │
└─────────────────────────────────────────────┘
```

**Usage:**
```python
from agents.guardian_agent import get_guardian

guardian = get_guardian()
assessment = guardian.maestro_security_assessment()

print(f"Overall Score: {assessment['overall_score']:.1%}")
print(f"Status: {assessment['status']}")
```

**API Endpoints:**
```
GET /security/maestro-assessment
GET /security/stats?period_hours=24
GET /security/audit-logs?limit=100
```

---

## 7. API Reference

### Health & Status

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Service health check |
| `/agents/health` | GET | All agents health status |
| `/agents/status` | GET | Agent completion percentages |
| `/agents/{id}` | GET | Specific agent details |

### Migrations

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/migrations` | GET | List all migrations |
| `/migrations` | POST | Start new migration |
| `/migrations/{id}` | GET | Get migration details |
| `/migrations/{id}/validate` | POST | Validate migration |
| `/migrations/{id}/validate-actor-critic` | POST | Self-healing validation |
| `/migrations/{id}/deploy` | POST | Deploy to warehouse |

### Security

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/security/maestro-assessment` | GET | 7-layer security assessment |
| `/security/stats` | GET | Security statistics |
| `/security/audit-logs` | GET | Audit event logs |

### Chat & Support

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat` | POST | AI support chat |
| `/chat/history` | GET | Chat history |

---

## 8. Testing

### Running Tests

```bash
# Run all Python tests
cd agents && python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_api_endpoints.py -v

# Run with coverage
python -m pytest tests/ --cov=agents --cov-report=html
```

### Test Structure

```
agents/tests/
├── conftest.py              # Shared fixtures
├── test_api_endpoints.py    # API endpoint tests (16 tests)
├── test_dbt_generator.py    # dbt generator tests (12 tests)
└── test_validation_agent.py # Validation tests (12 tests)
```

### Current Test Status

| Test File | Tests | Passing |
|-----------|-------|---------|
| test_api_endpoints.py | 16 | 16 |
| test_dbt_generator.py | 12 | 12 |
| test_validation_agent.py | 12 | 12 |
| **Total** | **40** | **40 (100%)** |

---

## 9. Deployment

### Railway Deployment

The project auto-deploys to Railway when pushing to `main`:

```bash
# Deploy
git push origin main
# Railway detects changes and auto-deploys
```

**Railway Configuration:** `railway.json`
```json
{
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "healthcheckPath": "/health",
    "healthcheckTimeout": 300
  }
}
```

### Docker Local

```bash
# Build and run all services
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop
docker-compose down
```

### Production URLs

- **Live App:** https://datamigrate-ai.up.railway.app
- **API Health:** https://datamigrate-ai.up.railway.app/health

---

## 10. Development Workflow

### Git Workflow

```bash
# 1. Make changes
# 2. Test locally
python -m pytest tests/ -v

# 3. Commit (use descriptive messages)
git add .
git commit -m "Add feature X for Y purpose"

# 4. Push to deploy
git push origin main
```

### Code Style

- **Python:** Follow PEP 8, use type hints
- **TypeScript:** Follow ESLint rules
- **Go:** Follow gofmt

### Adding a New Agent

1. Create `agents/new_agent.py` with class structure:
```python
class NewAgent:
    def __init__(self):
        pass

    def process(self, input_data):
        pass
```

2. Add to `AGENT_REGISTRY` in `api.py`
3. Add API endpoints if needed
4. Write tests in `tests/test_new_agent.py`
5. Update documentation

### Common Commands

```bash
# Start services
python -m uvicorn agents.api:app --port 8001 --reload

# Run tests
python -m pytest tests/ -v

# Check git status
git status

# View logs
docker-compose logs -f ai-service
```

---

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

---

## License & Ownership

**Property of:** OKO Investments
**Copyright:** © 2024-2025 OKO Investments. All rights reserved.

---

*Document generated for DataMigrate AI v1.0.0*
