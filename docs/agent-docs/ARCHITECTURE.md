# DataMigrate AI - System Architecture

## Technical Architecture Documentation
**Version:** 1.0.0
**Last Updated:** December 2024

---

## 1. System Overview

DataMigrate AI is a multi-tier, multi-agent AI system designed for enterprise database migrations. The architecture follows microservices principles with clear separation of concerns.

### Design Principles

1. **Agent Specialization** - Each agent has a single responsibility
2. **Loose Coupling** - Services communicate via well-defined APIs
3. **Defense in Depth** - Multiple security layers (MAESTRO)
4. **Self-Healing** - Actor-Critic pattern for automatic error recovery
5. **Observability** - Comprehensive logging, metrics, and tracing

---

## 2. Architectural Layers

### 2.1 Presentation Layer (Frontend)

```
┌─────────────────────────────────────────────────────────────────┐
│                     Vue.js 3 SPA                                │
├─────────────────────────────────────────────────────────────────┤
│  Components        │  Views           │  Services               │
│  ├─ Navbar        │  ├─ Dashboard    │  ├─ api.ts              │
│  ├─ ChatWidget    │  ├─ Migrations   │  └─ Authentication      │
│  └─ Alerts        │  ├─ Agents       │                         │
│                   │  └─ Settings     │                         │
├─────────────────────────────────────────────────────────────────┤
│  State (Pinia)    │  Router          │  i18n (7 languages)     │
└─────────────────────────────────────────────────────────────────┘
```

**Key Technologies:**
- Vue.js 3 with Composition API
- TypeScript for type safety
- Tailwind CSS for styling
- Vite for build tooling

### 2.2 API Gateway Layer (Go Backend)

```
┌─────────────────────────────────────────────────────────────────┐
│                     Gin HTTP Server                             │
├─────────────────────────────────────────────────────────────────┤
│                       Middleware Stack                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │   CORS   │→│   JWT    │→│  Rate    │→│  Logger  │          │
│  │          │ │   Auth   │ │  Limit   │ │          │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
├─────────────────────────────────────────────────────────────────┤
│                       Route Handlers                            │
│  /api/v1/auth/*     - Authentication                           │
│  /api/v1/migrations/* - Migration CRUD                         │
│  /api/v1/connections/* - Database connections                  │
│  /api/v1/chat       - AI support                               │
├─────────────────────────────────────────────────────────────────┤
│                       Services                                  │
│  ├─ AuthService     (JWT, password hashing)                    │
│  ├─ MigrationService (orchestration)                           │
│  ├─ AIServiceClient (Python service proxy)                     │
│  └─ EmailService    (SMTP notifications)                       │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 AI Processing Layer (Python)

```
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Application                         │
├─────────────────────────────────────────────────────────────────┤
│                   LangGraph Orchestrator                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Assessment → Planning → Execution → Testing → Evaluation │  │
│  └──────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                      Agent Pool                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│  │   MSSQL     │ │     dbt     │ │  Validation │              │
│  │  Extractor  │ │  Generator  │ │    Agent    │              │
│  └─────────────┘ └─────────────┘ └─────────────┘              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│  │     dbt     │ │    Data     │ │     RAG     │              │
│  │  Executor   │ │   Quality   │ │   Service   │              │
│  └─────────────┘ └─────────────┘ └─────────────┘              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│  │  Guardian   │ │   DataPrep  │ │   ML Fine   │              │
│  │   Agent     │ │    Agent    │ │   Tuning    │              │
│  └─────────────┘ └─────────────┘ └─────────────┘              │
├─────────────────────────────────────────────────────────────────┤
│                    External Integrations                        │
│  ├─ Anthropic Claude API                                       │
│  ├─ Voyage AI Embeddings                                       │
│  └─ dbt CLI                                                    │
└─────────────────────────────────────────────────────────────────┘
```

### 2.4 Data Layer

```
┌─────────────────────────────────────────────────────────────────┐
│                      PostgreSQL 16                              │
├─────────────────────────────────────────────────────────────────┤
│  Tables                    │  Extensions                       │
│  ├─ users                  │  ├─ pgvector (RAG embeddings)     │
│  ├─ organizations          │  └─ pg_trgm (text search)         │
│  ├─ migrations             │                                   │
│  ├─ connections            │  Indexes                          │
│  ├─ audit_logs             │  ├─ HNSW (vector similarity)      │
│  └─ chat_history           │  └─ B-tree (primary keys)         │
├─────────────────────────────────────────────────────────────────┤
│                      Source Databases                           │
│  ├─ MSSQL Server (via pyodbc)                                  │
│  └─ Other supported sources (future)                           │
├─────────────────────────────────────────────────────────────────┤
│                      Target Warehouses                          │
│  ├─ Snowflake                                                  │
│  ├─ Databricks                                                 │
│  ├─ BigQuery                                                   │
│  ├─ Redshift                                                   │
│  └─ Microsoft Fabric                                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Agent Architecture

### 3.1 Agent Communication Pattern

```
                    ┌─────────────────┐
                    │   API Gateway   │
                    │    (Go/Gin)     │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  FastAPI Router │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │  Agent   │  │  Agent   │  │  Agent   │
        │    A     │  │    B     │  │    C     │
        └────┬─────┘  └────┬─────┘  └────┬─────┘
             │             │             │
             └─────────────┼─────────────┘
                           │
                           ▼
                    ┌─────────────────┐
                    │  Shared State   │
                    │   (LangGraph)   │
                    └─────────────────┘
```

### 3.2 LangGraph State Machine

```python
# State definition (simplified)
class MigrationState(TypedDict):
    migration_id: int
    source_connection: dict
    target_warehouse: str
    metadata: dict
    dbt_project_path: str
    validation_result: dict
    deployment_result: dict
    errors: list
    status: str
```

### 3.3 Agent Lifecycle

```
┌─────────────┐
│   Created   │
└──────┬──────┘
       │ initialize()
       ▼
┌─────────────┐
│    Ready    │◄────────────────┐
└──────┬──────┘                 │
       │ process()              │
       ▼                        │
┌─────────────┐                 │
│  Processing │                 │
└──────┬──────┘                 │
       │                        │
       ├─── success ────────────┤
       │                        │
       └─── error ──────► ┌─────┴─────┐
                          │   Error   │
                          │  Recovery │
                          └───────────┘
```

---

## 4. Security Architecture (MAESTRO)

### 4.1 Seven-Layer Model

```
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 7: MONITORING                                            │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐         │
│  │  Prometheus   │ │    Grafana    │ │   Alerting    │         │
│  │   Metrics     │ │  Dashboards   │ │    Rules      │         │
│  └───────────────┘ └───────────────┘ └───────────────┘         │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 6: DEPLOYMENT                                            │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐         │
│  │   Railway     │ │    Docker     │ │   Network     │         │
│  │   Hardening   │ │   Security    │ │  Isolation    │         │
│  └───────────────┘ └───────────────┘ └───────────────┘         │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 5: AGENT ECOSYSTEM                                       │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐         │
│  │ Organization  │ │     Rate      │ │    Trust      │         │
│  │   Policies    │ │   Limiting    │ │  Boundaries   │         │
│  └───────────────┘ └───────────────┘ └───────────────┘         │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 4: AGENT CORE (Guardian Agent)                           │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐         │
│  │    Prompt     │ │     SQL       │ │    Output     │         │
│  │  Injection    │ │  Injection    │ │   Filtering   │         │
│  │  Detection    │ │  Prevention   │ │               │         │
│  └───────────────┘ └───────────────┘ └───────────────┘         │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 3: AGENT FRAMEWORK                                       │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐         │
│  │    State      │ │   Thread      │ │    Audit      │         │
│  │  Isolation    │ │   Safety      │ │   Logging     │         │
│  └───────────────┘ └───────────────┘ └───────────────┘         │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 2: DATA OPERATIONS                                       │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐         │
│  │  Connection   │ │  Credential   │ │ Exfiltration  │         │
│  │   Security    │ │  Encryption   │ │  Detection    │         │
│  └───────────────┘ └───────────────┘ └───────────────┘         │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 1: FOUNDATION MODELS                                     │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐         │
│  │  Anthropic    │ │   API Key     │ │    Model      │         │
│  │   Security    │ │  Management   │ │   Controls    │         │
│  └───────────────┘ └───────────────┘ └───────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Security Flow

```
Request
   │
   ▼
┌──────────────────┐
│  Rate Limiter    │──── Blocked ────► 429 Too Many Requests
└────────┬─────────┘
         │ Pass
         ▼
┌──────────────────┐
│ Input Sanitizer  │──── Injection ──► 400 Bad Request
└────────┬─────────┘
         │ Pass
         ▼
┌──────────────────┐
│  Policy Check    │──── Violation ──► 403 Forbidden
└────────┬─────────┘
         │ Pass
         ▼
┌──────────────────┐
│  Agent Process   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Output Validator │──── PII/Leak ───► Sanitized Response
└────────┬─────────┘
         │ Pass
         ▼
┌──────────────────┐
│  Audit Logger    │
└────────┬─────────┘
         │
         ▼
      Response
```

---

## 5. Data Flow Architecture

### 5.1 Migration Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    EXTRACTION PHASE                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  MSSQL Database                                                 │
│       │                                                         │
│       ▼                                                         │
│  ┌──────────────────┐                                          │
│  │  MSSQL Extractor │                                          │
│  │  - Tables        │                                          │
│  │  - Columns       │                                          │
│  │  - Foreign Keys  │                                          │
│  │  - Indexes       │                                          │
│  │  - Row Counts    │                                          │
│  └────────┬─────────┘                                          │
│           │                                                     │
│           ▼                                                     │
│  ┌──────────────────┐                                          │
│  │  Metadata JSON   │                                          │
│  └────────┬─────────┘                                          │
└───────────┼─────────────────────────────────────────────────────┘
            │
┌───────────┼─────────────────────────────────────────────────────┐
│           ▼         GENERATION PHASE                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐                                          │
│  │  dbt Generator   │                                          │
│  └────────┬─────────┘                                          │
│           │                                                     │
│           ▼                                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  dbt Project                                              │  │
│  │  ├── dbt_project.yml                                     │  │
│  │  ├── profiles.yml                                        │  │
│  │  └── models/                                             │  │
│  │      ├── staging/                                        │  │
│  │      │   ├── _sources.yml                               │  │
│  │      │   ├── _schema.yml                                │  │
│  │      │   └── stg_*.sql                                  │  │
│  │      ├── intermediate/                                   │  │
│  │      └── marts/                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────┬─────────────────────────────────────────────────────┘
            │
┌───────────┼─────────────────────────────────────────────────────┐
│           ▼         VALIDATION PHASE                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐      ┌──────────────────┐                │
│  │ Validation Agent │──────│ Actor-Critic Loop│                │
│  └────────┬─────────┘      └──────────────────┘                │
│           │                                                     │
│           ├── Schema Check                                      │
│           ├── Data Type Mapping                                 │
│           ├── Referential Integrity                             │
│           ├── SQL Syntax                                        │
│           └── Test Coverage                                     │
│                                                                 │
│  Score >= 95% ────► Approved                                   │
│  Score < 95%  ────► Auto-fix ────► Re-validate                 │
└───────────┬─────────────────────────────────────────────────────┘
            │
┌───────────┼─────────────────────────────────────────────────────┐
│           ▼         DEPLOYMENT PHASE                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐                                          │
│  │   dbt Executor   │                                          │
│  └────────┬─────────┘                                          │
│           │                                                     │
│           ├── dbt deps                                          │
│           ├── dbt compile                                       │
│           ├── dbt run                                           │
│           └── dbt test                                          │
│                                                                 │
│           ▼                                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Target Warehouse                                         │  │
│  │  (Snowflake / Databricks / BigQuery / Redshift)          │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Deployment Architecture

### 6.1 Railway Production

```
┌─────────────────────────────────────────────────────────────────┐
│                        Railway Platform                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Service: web                          │   │
│  │  ┌─────────────────────────────────────────────────────┐│   │
│  │  │  Docker Container                                    ││   │
│  │  │  ┌─────────────────┐ ┌─────────────────┐           ││   │
│  │  │  │   Go Backend    │ │ Vue.js Static   │           ││   │
│  │  │  │   (API + Auth)  │ │   (Frontend)    │           ││   │
│  │  │  │   Port: 8080    │ │   (served by Go)│           ││   │
│  │  │  └─────────────────┘ └─────────────────┘           ││   │
│  │  └─────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   Service: ai-service                    │   │
│  │  ┌─────────────────────────────────────────────────────┐│   │
│  │  │  Docker Container                                    ││   │
│  │  │  ┌─────────────────────────────────────────────────┐││   │
│  │  │  │  Python FastAPI + AI Agents                     │││   │
│  │  │  │  Port: 8001                                     │││   │
│  │  │  └─────────────────────────────────────────────────┘││   │
│  │  └─────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   Service: postgres                      │   │
│  │  ┌─────────────────────────────────────────────────────┐│   │
│  │  │  PostgreSQL 16 + pgvector                           ││   │
│  │  └─────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Local Docker Compose

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16
    ports: ["5432:5432"]

  backend:
    build: ./backend
    ports: ["8080:8080"]
    depends_on: [postgres]

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    depends_on: [backend]

  ai-service:
    build:
      dockerfile: Dockerfile.agents
    ports: ["8001:8001"]
    depends_on: [postgres]
```

---

## 7. Scalability Considerations

### 7.1 Horizontal Scaling

```
                         Load Balancer
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
        ┌──────────┐   ┌──────────┐   ┌──────────┐
        │ Backend  │   │ Backend  │   │ Backend  │
        │ Instance │   │ Instance │   │ Instance │
        │    1     │   │    2     │   │    3     │
        └────┬─────┘   └────┬─────┘   └────┬─────┘
             │              │              │
             └──────────────┼──────────────┘
                            │
                   ┌────────┴────────┐
                   │                 │
                   ▼                 ▼
              ┌──────────┐     ┌──────────┐
              │ AI Pool  │     │PostgreSQL│
              │ (Python) │     │ Primary  │
              └──────────┘     └──────────┘
```

### 7.2 Performance Optimizations

| Component | Optimization |
|-----------|--------------|
| API Gateway | Connection pooling, response caching |
| AI Service | Agent pooling, async processing |
| Database | pgvector HNSW indexes, query optimization |
| Frontend | CDN for static assets, lazy loading |

---

## 8. Monitoring & Observability

### 8.1 Metrics Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                         Grafana                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Dashboard: DataMigrate AI                                │ │
│  │  ├── Migration Success Rate                               │ │
│  │  ├── Agent Performance                                    │ │
│  │  ├── API Latency (P95, P99)                              │ │
│  │  └── Security Events                                      │ │
│  └───────────────────────────────────────────────────────────┘ │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────┼──────────────────────────────────┐
│                         Prometheus                              │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Targets:                                                 │ │
│  │  ├── go-backend:8080/metrics                             │ │
│  │  └── ai-service:8001/metrics                             │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 Key Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `migrations_total` | Counter | Total migrations started |
| `migrations_successful` | Counter | Successful completions |
| `agent_invocations` | Counter | Agent call count |
| `agent_latency_seconds` | Histogram | Agent processing time |
| `security_events_total` | Counter | Security events by type |
| `validation_score` | Gauge | Latest validation scores |

---

## 9. Future Architecture Considerations

### 9.1 Planned Enhancements

1. **GraphRAG Integration** - Knowledge graph for complex queries
2. **Kubernetes Deployment** - For enterprise scaling
3. **Multi-Region Support** - Geo-distributed deployment
4. **Real-time Streaming** - WebSocket migration progress
5. **Agent Fine-Tuning** - Custom model training pipeline

### 9.2 Technology Roadmap

| Phase | Technology | Purpose |
|-------|------------|---------|
| v1.1 | WebSockets | Real-time updates |
| v1.2 | Redis | Caching layer |
| v2.0 | GraphRAG | Knowledge graphs |
| v2.1 | Kubernetes | Container orchestration |
| v3.0 | Custom Models | Fine-tuned agents |

---

*Architecture Document - DataMigrate AI v1.0.0*
*Property of OKO Investments*
