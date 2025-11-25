# Project Architecture

## Architecture Type: **Modular Monolith → Microservices Ready**

This project is built as a **modular monolith** with clear service boundaries, making it easy to transition to microservices when needed.

### Current State: Modular Monolith
- Single codebase with distinct modules
- Shared database (SQLite/PostgreSQL)
- Two separate web applications (Flask + FastAPI)
- Service layer provides clear boundaries

### Future State: Microservices (When scaling needed)
- Each module becomes an independent service
- Separate databases per service
- API Gateway for routing
- Message queue for inter-service communication

---

## Architecture Pattern: **Layered Architecture + Service-Oriented**

```
┌─────────────────────────────────────────────────────┐
│                 Presentation Layer                   │
│  ┌────────────────────┐  ┌────────────────────────┐ │
│  │  Flask (Port 5000) │  │  FastAPI (Port 8000)   │ │
│  │  Admin Dashboard   │  │  Public REST API       │ │
│  │  - Jinja Templates │  │  - OpenAPI Docs        │ │
│  │  - Tailwind CSS    │  │  - JSON Responses      │ │
│  └────────────────────┘  └────────────────────────┘ │
└─────────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼─────────────────────────────┐
│                   Service Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │ AuthService  │  │ UsageTracker │  │ Migration   │ │
│  │              │  │              │  │ Service     │ │
│  │ - User auth  │  │ - API usage  │  │ - LangGraph │ │
│  │ - API keys   │  │ - Billing    │  │ - Agents    │ │
│  └──────────────┘  └──────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼─────────────────────────────┐
│                  Domain Layer                          │
│  ┌──────────────────────────────────────────────────┐ │
│  │         LangGraph Multi-Agent System             │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐      │ │
│  │  │Assessment│  │ Planner  │  │ Executor │      │ │
│  │  └──────────┘  └──────────┘  └──────────┘      │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐      │ │
│  │  │  Tester  │  │Rebuilder │  │Evaluator │      │ │
│  │  └──────────┘  └──────────┘  └──────────┘      │ │
│  └──────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼─────────────────────────────┐
│                 Data Access Layer                      │
│  ┌──────────────────────────────────────────────────┐ │
│  │          SQLAlchemy ORM Models                   │ │
│  │  - User, APIKey, Migration                       │ │
│  │  - ModelFile, UsageLog                           │ │
│  └──────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼─────────────────────────────┐
│                   Database Layer                       │
│         SQLite (Dev) / PostgreSQL (Prod)               │
└─────────────────────────────────────────────────────┘
```

---

## Design Patterns & Principles Applied

### 1. **Layered Architecture**
- **Presentation Layer**: Flask + FastAPI
- **Service Layer**: Business logic services
- **Domain Layer**: LangGraph agents (core business domain)
- **Data Access Layer**: SQLAlchemy models
- **Database Layer**: SQLite/PostgreSQL

**Benefits**:
- Clear separation of concerns
- Easy to test each layer independently
- Can swap implementations (e.g., change database)

### 2. **Service-Oriented Architecture (SOA)**
Each service has a single responsibility:
- **AuthService**: Authentication & authorization
- **UsageTracker**: Usage monitoring & billing
- **MigrationService**: Orchestrates LangGraph workflows

**Benefits**:
- High cohesion, low coupling
- Easy to understand and maintain
- Can evolve into microservices

### 3. **Repository Pattern**
SQLAlchemy models act as repositories for data access.

**Benefits**:
- Abstracts database operations
- Easy to mock for testing
- Database-agnostic code

### 4. **Dependency Injection**
Services receive database sessions via parameters:
```python
class MigrationService:
    def __init__(self, db: Session):
        self.db = db
```

**Benefits**:
- Testable (can inject mock DB)
- Flexible (can change DB implementation)
- Clear dependencies

### 5. **Multi-Agent Pattern (LangGraph)**
Specialized agents work together in a workflow:
- Each agent has one job
- State passed between agents
- Conditional routing based on results

**Benefits**:
- Parallelizable
- Resumable workflows
- Easy to add/modify agents

### 6. **API Gateway Pattern** (FastAPI)
Single entry point for all API requests:
- Authentication middleware
- Rate limiting
- Request logging

**Benefits**:
- Centralized security
- Easy monitoring
- Scalable

### 7. **Factory Pattern**
Flask app factory for configuration:
```python
def create_app():
    app = Flask(__name__)
    # Configure and return
    return app
```

**Benefits**:
- Multiple app instances
- Easy testing
- Configuration flexibility

---

## SOLID Principles Applied

### **S - Single Responsibility Principle** ✅
- Each service has one job
- Each agent has one purpose
- Each route file handles one resource

### **O - Open/Closed Principle** ✅
- Services extend functionality without modifying core code
- New agents can be added without changing orchestrator
- New routes added via blueprints

### **L - Liskov Substitution Principle** ✅
- SQLAlchemy models can be swapped
- Database can be changed (SQLite → PostgreSQL)

### **I - Interface Segregation Principle** ✅
- Small, focused service interfaces
- Agents implement specific node interface
- Routes use specific dependencies

### **D - Dependency Inversion Principle** ✅
- Services depend on abstractions (Session), not concrete DB
- FastAPI depends on dependency injection
- Flask uses blueprints for loose coupling

---

## Code Quality Principles

### 1. **DRY (Don't Repeat Yourself)**
- Shared services layer used by both Flask and FastAPI
- Reusable authentication dependencies
- Common database models

### 2. **KISS (Keep It Simple, Stupid)**
- Simple service interfaces
- Clear function names
- Straightforward logic

### 3. **YAGNI (You Aren't Gonna Need It)**
- Build only what's needed now
- No premature optimization
- Add features when required

### 4. **Separation of Concerns**
- Flask = Admin UI
- FastAPI = Public API
- Services = Business logic
- Models = Data structure
- Agents = Domain logic

---

## Modularity Features

### 1. **Independent Modules**
```
agents/       → Can run standalone
app/          → Shared by both web apps
flask_app/    → Independent web app
fastapi_app/  → Independent web app
```

### 2. **Loose Coupling**
- Services don't know about web frameworks
- Web apps don't know about agent internals
- Agents don't know about database

### 3. **High Cohesion**
- All authentication logic in AuthService
- All agent logic in agents/ folder
- All database models in app/models.py

### 4. **Pluggable Components**
Can replace:
- Database (SQLite → PostgreSQL)
- Web framework (Flask → FastAPI)
- Authentication (Local → OAuth)
- Agents (Add/remove as needed)

---

## Scalability Path

### Phase 1: Modular Monolith (Current)
```
┌─────────────────────────────────┐
│     Single Application          │
│  Flask + FastAPI + Services     │
│         + Agents                │
│    Shared Database (SQLite)     │
└─────────────────────────────────┘
```

**Best for**: 0-100 users, local development

### Phase 2: Microservices (Future)
```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Flask Service│  │FastAPI Service│  │Agent Service │
│              │  │              │  │              │
│  Users DB    │  │Migrations DB │  │  State DB    │
└──────────────┘  └──────────────┘  └──────────────┘
        │                 │                 │
        └─────────────────┴─────────────────┘
                     │
              ┌──────▼──────┐
              │ API Gateway │
              └─────────────┘
```

**Best for**: 100+ users, need to scale independently

---

## Why This Architecture?

### ✅ Advantages

1. **Easy to Develop**
   - Single codebase
   - Shared services
   - Simple deployment

2. **Easy to Test**
   - Clear boundaries
   - Mockable services
   - Independent modules

3. **Easy to Scale**
   - Can split into microservices later
   - Service boundaries already defined
   - Database per service ready

4. **Production Ready**
   - Proper separation of concerns
   - Industry-standard patterns
   - Scalable architecture

5. **Maintainable**
   - Clear structure
   - Well-documented
   - Follows best practices

### ⚠️ Trade-offs

1. **Shared Database**
   - Pro: Simple to develop and deploy
   - Con: Can't scale database independently (yet)

2. **Monolithic Deployment**
   - Pro: Easy to deploy as one unit
   - Con: Can't deploy services independently

3. **In-Memory State**
   - Pro: Fast agent execution
   - Con: Need persistent state for distributed systems

---

## Technology Choices Rationale

### **Python 3.12**
- Async/await support
- Type hints
- Great for AI/ML

### **LangGraph**
- Native multi-agent support
- Checkpointing for resumability
- Production-ready

### **Flask (Admin)**
- Simple, proven
- Great for server-rendered HTML
- Large ecosystem

### **FastAPI (Public API)**
- Async support
- Auto-generated docs
- Fast performance
- Type validation

### **SQLAlchemy**
- Database agnostic
- ORM + raw SQL
- Migrations support

### **PostgreSQL (Production)**
- JSONB for agent state
- pgvector for embeddings
- Production-proven

### **SQLite (Development)**
- Zero config
- File-based
- Perfect for learning

---

## Conclusion

This is a **well-architected modular monolith** that:
- ✅ Follows SOLID principles
- ✅ Uses industry-standard patterns
- ✅ Ready for production
- ✅ Can scale to microservices
- ✅ Maintainable and testable

**Perfect for**: SaaS MVP → Production → Scale
