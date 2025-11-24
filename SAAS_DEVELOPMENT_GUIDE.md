# SaaS Development Guide

## 🎯 Project Overview

**MSSQL to dbt Migration SaaS Platform**

A production-ready SaaS product that uses AI agents (LangGraph + Claude) to automatically migrate MSSQL databases to dbt models.

### Architecture

```
┌─────────────────────────────────────────────────┐
│         Frontend Layer (Local Dev)              │
├─────────────────────────────────────────────────┤
│  Flask (Port 5000) - Admin Dashboard            │
│  - Login/logout                                 │
│  - Monitor all migrations                       │
│  - Manage users & API keys                      │
│  - View usage statistics                        │
│  - Tailwind CSS styling                         │
└─────────────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
┌───────▼─────────┐    ┌──────────▼──────────┐
│  FastAPI        │    │  Shared Services    │
│  (Port 8000)    │◄───┤  - MigrationService │
│  Public API     │    │  - UsageTracker     │
│  - POST /api/   │    │  - AuthService      │
│    v1/migrations│    └─────────────────────┘
│  - GET /api/v1/ │              │
│    migrations/  │    ┌─────────▼──────────┐
│    {id}         │    │  Database Models   │
│  - API Key Auth │    │  SQLite (dev)      │
└─────────────────┘    │  PostgreSQL (prod) │
         │             └────────────────────┘
         ▼
┌─────────────────────────────────────────────────┐
│     LangGraph Native Agents (Core Engine)       │
├─────────────────────────────────────────────────┤
│  agents/native_nodes.py                         │
│  - assessment_node  (analyzes MSSQL)            │
│  - planner_node     (creates migration plan)    │
│  - executor_node    (generates dbt SQL)         │
│  - tester_node      (validates models)          │
│  - rebuilder_node   (fixes errors)              │
│  - evaluator_node   (final report)              │
└─────────────────────────────────────────────────┘
```

---

## 📦 Installation

### 1. Core Dependencies (Already Installed)

```bash
# LangGraph, LangChain, AWS CDK
pip install -r requirements.txt
```

**Key packages:**
- `langchain>=0.1.0`
- `langchain-anthropic>=0.1.0`
- `langgraph>=0.0.40`
- `pydantic>=2.0.0`

### 2. Web Dependencies (Install Now)

```bash
pip install -r requirements_web.txt
```

**Key packages:**
- Flask 3.0.0 (Admin dashboard)
- FastAPI 0.104.1 (Public API)
- SQLAlchemy 2.0.23 (Database ORM)
- uvicorn (ASGI server)

---

## 🗄️ Database Schema

### Tables

**users**
```sql
- id: Integer (PK)
- email: String (unique)
- password_hash: String
- full_name: String
- is_admin: Boolean
- is_active: Boolean
- created_at: DateTime
- last_login: DateTime
```

**api_keys**
```sql
- id: Integer (PK)
- user_id: Integer (FK → users)
- key: String (unique) - Format: "mk_xxxxx"
- name: String (description)
- is_active: Boolean
- rate_limit: Integer (requests/hour)
- created_at: DateTime
- last_used: DateTime
- expires_at: DateTime (nullable)
```

**migrations**
```sql
- id: Integer (PK)
- user_id: Integer (FK → users)
- api_key_id: Integer (FK → api_keys)
- status: String (pending/running/completed/failed)
- phase: String (assessment/planning/execution/evaluation)
- project_name: String
- project_path: String
- metadata_json: JSON (MSSQL schema)
- state_json: JSON (full LangGraph state)
- total_models: Integer
- completed_models: Integer
- failed_models: Integer
- success_rate: Float
- created_at: DateTime
- started_at: DateTime
- completed_at: DateTime
```

**model_files**
```sql
- id: Integer (PK)
- migration_id: Integer (FK → migrations)
- name: String (model name)
- model_type: String (staging/intermediate/fact)
- status: String
- file_path: String
- sql_code: Text
- validation_score: Float
- attempts: Integer
```

**usage_logs**
```sql
- id: Integer (PK)
- api_key_id: Integer (FK → api_keys)
- endpoint: String
- method: String
- status_code: Integer
- response_time: Float (ms)
- models_generated: Integer
- tokens_used: Integer
- timestamp: DateTime
```

---

## 🚀 Quick Start (Local Development)

### Step 1: Initialize Database

```bash
python -c "from app.database import init_db; init_db()"
```

This creates `mssql_dbt_migration.db` (SQLite) with all tables.

### Step 2: Create Admin User

```python
from app.database import SessionLocal
from app.services import AuthService

db = SessionLocal()
auth = AuthService(db)

# Create admin user
admin = auth.create_user(
    email="admin@example.com",
    password="secure_password",
    full_name="Admin User",
    is_admin=True
)

# Create API key for testing
api_key = auth.create_api_key(
    user_id=admin.id,
    name="Test API Key",
    rate_limit=1000
)

print(f"API Key: {api_key.key}")
```

### Step 3: Run Flask (Admin Dashboard)

```bash
python run_flask.py
```

Access at: http://localhost:5000

### Step 4: Run FastAPI (Public API)

```bash
python run_fastapi.py
```

Access at: http://localhost:8000
API Docs: http://localhost:8000/docs

---

## 🔧 Services Documentation

### MigrationService

**Purpose:** Orchestrates MSSQL to dbt migrations using LangGraph agents.

**Key Methods:**
```python
from app.services import MigrationService

service = MigrationService(db)

# Create migration
migration = service.create_migration(
    user_id=1,
    metadata=mssql_metadata,  # From metadata extractor
    project_name="my_project",
    project_path="./migrations/my_project"
)

# Start migration (runs LangGraph)
service.start_migration(migration.id)

# Get migration status
migration = service.get_migration(migration.id)
print(f"Status: {migration.status}")
print(f"Progress: {migration.completed_models}/{migration.total_models}")

# Get generated models
models = service.get_migration_models(migration.id)
for model in models:
    print(f"{model.name}: {model.status}")
```

**Workflow:**
1. Creates Migration record in database
2. Initializes LangGraph state from metadata
3. Runs StateGraph workflow (6 agents)
4. Updates Migration progress after each step
5. Creates ModelFile records for generated SQL
6. Returns final Migration with results

### UsageTracker

**Purpose:** Track API usage for billing.

**Key Methods:**
```python
from app.services import UsageTracker

tracker = UsageTracker(db)

# Log API request
tracker.log_request(
    api_key_id=1,
    endpoint="/api/v1/migrations",
    method="POST",
    status_code=201,
    response_time=1250.5,  # ms
    models_generated=5
)

# Get usage stats
stats = tracker.get_usage_stats(api_key_id=1, days=30)
print(f"Requests: {stats['total_requests']}")
print(f"Models: {stats['total_models']}")

# Check rate limit
if not tracker.check_rate_limit(api_key_id=1):
    return {"error": "Rate limit exceeded"}
```

### AuthService

**Purpose:** User and API key authentication.

**Key Methods:**
```python
from app.services import AuthService

auth = AuthService(db)

# User authentication (Flask)
user = auth.authenticate_user("user@example.com", "password")
if user:
    # Login successful
    pass

# API key authentication (FastAPI)
api_key = auth.authenticate_api_key("mk_xxxxx...")
if api_key:
    # Valid API key
    pass

# Create API key
api_key = auth.create_api_key(
    user_id=1,
    name="Production Key",
    rate_limit=500,
    expires_in_days=365
)

# Revoke API key
auth.revoke_api_key(api_key_id=1)
```

---

## 🎨 Flask Dashboard (To Be Built)

### Routes

```python
# Home / Login
GET  /                 → Login page or redirect to dashboard
POST /login            → Authenticate user
GET  /logout           → Logout user

# Dashboard
GET  /dashboard        → Overview (stats, recent migrations)

# Migrations
GET  /migrations       → List all migrations
GET  /migrations/<id>  → Migration details
POST /migrations/new   → Create new migration
POST /migrations/<id>/start → Start migration

# Users (Admin only)
GET  /users            → List all users
POST /users/new        → Create user
POST /users/<id>/toggle → Activate/deactivate

# API Keys
GET  /api-keys         → List user's API keys
POST /api-keys/new     → Generate new API key
POST /api-keys/<id>/revoke → Revoke key

# Usage
GET  /usage            → Usage statistics
```

### Templates (Tailwind CSS)

```
flask_app/templates/
├── base.html           # Base template with Tailwind CDN
├── login.html          # Login form
├── dashboard.html      # Overview dashboard
├── migrations/
│   ├── list.html       # Migration list
│   ├── detail.html     # Migration detail
│   └── new.html        # Create migration form
├── users/
│   ├── list.html       # User management
│   └── new.html        # Create user form
└── api_keys/
    ├── list.html       # API key list
    └── new.html        # Generate API key
```

---

## 🔌 FastAPI Endpoints (To Be Built)

### API Routes

```python
# Migrations
POST   /api/v1/migrations
    Body: {
        "metadata": {...},
        "project_name": "my_project"
    }
    Response: {
        "migration_id": 1,
        "status": "pending"
    }

GET    /api/v1/migrations/{migration_id}
    Response: {
        "id": 1,
        "status": "running",
        "phase": "execution",
        "completed_models": 3,
        "total_models": 10,
        "success_rate": 30.0
    }

GET    /api/v1/migrations/{migration_id}/models
    Response: [
        {
            "name": "stg_customers",
            "status": "completed",
            "validation_score": 0.95
        }
    ]

GET    /api/v1/migrations/{migration_id}/download
    Response: ZIP file with dbt project
```

### Authentication

```python
# Header required for all requests
Authorization: Bearer mk_your_api_key_here

# Example with curl
curl -X POST http://localhost:8000/api/v1/migrations \
  -H "Authorization: Bearer mk_xxxxx" \
  -H "Content-Type: application/json" \
  -d '{"metadata": {...}, "project_name": "test"}'
```

---

## 📊 Monetization Strategy

### Pricing Tiers

**Free Tier**
- 10 migrations/month
- Rate limit: 10 requests/hour
- Support: Email

**Pro Tier** ($49/month)
- 100 migrations/month
- Rate limit: 100 requests/hour
- Support: Priority email

**Enterprise Tier** ($299/month)
- Unlimited migrations
- Rate limit: 1000 requests/hour
- Dedicated support
- SLA guarantee

### Usage Tracking

Track in `usage_logs` table:
- API requests per API key
- Models generated per request
- Response times
- Error rates

### Billing Logic

```python
# Calculate monthly usage
def calculate_monthly_bill(api_key_id):
    logs = db.query(UsageLog).filter(
        UsageLog.api_key_id == api_key_id,
        UsageLog.timestamp >= start_of_month
    ).all()

    total_requests = len(logs)
    total_models = sum(log.models_generated for log in logs)

    # Pricing: $0.10 per migration + $0.01 per model
    cost = (total_requests * 0.10) + (total_models * 0.01)
    return cost
```

---

## 🚀 Scaling Path (Future)

### Phase 1: Local Development (Current)
- SQLite database
- Flask + FastAPI on localhost
- Perfect for learning and testing

**Cost:** $0

### Phase 2: AWS Simple (10-100 customers)
```bash
# Deploy with existing AWS CDK
cd aws
cdk deploy

# Infrastructure:
- API Gateway + Lambda (Flask/FastAPI)
- RDS PostgreSQL
- S3 (model storage)
- Lambda + Step Functions (LangGraph agents)
```

**Cost:** ~$100-500/month

### Phase 3: Kubernetes + Terraform (100-1000 customers)

**Directory Structure:**
```
infrastructure/
├── terraform/
│   ├── main.tf          # EKS cluster
│   ├── rds.tf           # PostgreSQL
│   ├── redis.tf         # ElastiCache
│   └── s3.tf            # Storage
├── kubernetes/
│   ├── deployments/
│   │   ├── flask.yaml   # Flask pods
│   │   ├── fastapi.yaml # FastAPI pods
│   │   └── workers.yaml # Celery workers
│   ├── services/
│   │   ├── flask-svc.yaml
│   │   └── fastapi-svc.yaml
│   └── ingress/
│       └── alb-ingress.yaml
└── helm/
    └── migration-app/   # Helm chart
```

**Deployment:**
```bash
# 1. Provision infrastructure
cd infrastructure/terraform
terraform init
terraform apply

# 2. Deploy Kubernetes resources
kubectl apply -f kubernetes/

# 3. Or use Helm
helm install migration-app ./helm/migration-app
```

**Cost:** ~$500-2000/month (scales with load)

### Phase 4: Multi-Region (1000+ customers)

**Architecture:**
- EKS clusters in multiple regions
- Global load balancer
- Read replicas for database
- CDN for static assets
- Auto-scaling (0-1000 pods)

**Cost:** ~$2000-10000/month

---

## 📚 Learning Resources

### Kubernetes
- [Kubernetes Basics](https://kubernetes.io/docs/tutorials/kubernetes-basics/)
- [EKS Workshop](https://www.eksworkshop.com/)
- [Kubernetes Patterns](https://k8spatterns.io/)

### Terraform
- [Terraform AWS Tutorial](https://developer.hashicorp.com/terraform/tutorials/aws-get-started)
- [AWS EKS with Terraform](https://developer.hashicorp.com/terraform/tutorials/kubernetes/eks)

### AWS
- [AWS Free Tier](https://aws.amazon.com/free/)
- [AWS CDK Workshop](https://cdkworkshop.com/)
- [Step Functions Workshop](https://catalog.workshops.aws/stepfunctions/)

---

## 🔍 Testing

### Unit Tests (To Be Added)

```python
# tests/test_services.py
def test_create_migration():
    service = MigrationService(db)
    migration = service.create_migration(...)
    assert migration.status == 'pending'

# tests/test_api.py
def test_create_migration_endpoint():
    response = client.post('/api/v1/migrations', json={...})
    assert response.status_code == 201
```

### Integration Tests

```bash
# Test full migration flow
python test_langgraph_migration.py

# Test Flask app
pytest tests/test_flask.py

# Test FastAPI
pytest tests/test_fastapi.py
```

---

## 📝 Next Steps

**Immediate (This Session):**
1. ✅ Install web dependencies
2. ⏳ Build Flask admin app
3. ⏳ Build FastAPI public API
4. ⏳ Test locally

**Short Term (Next Week):**
1. Add user registration flow
2. Add email notifications
3. Add webhook support
4. Create landing page

**Medium Term (1-2 Months):**
1. Deploy to AWS (CDK)
2. Set up CI/CD pipeline
3. Add monitoring (Prometheus/Grafana)
4. Launch beta program

**Long Term (3-6 Months):**
1. Migrate to Kubernetes
2. Add Terraform infrastructure
3. Multi-region deployment
4. Enterprise features

---

## 💡 Tips for Learning K8s + Terraform

### Start Small
1. Deploy a simple app to local Minikube
2. Learn kubectl commands
3. Understand pods, services, deployments
4. Graduate to AWS EKS

### Hands-On Projects
1. Containerize this Flask app (Dockerfile)
2. Deploy to local Kubernetes
3. Add persistence (volumes)
4. Add load balancing (ingress)

### Use This Project
Once comfortable with K8s:
1. Create `Dockerfile` for Flask/FastAPI
2. Write Kubernetes manifests
3. Deploy to EKS with Terraform
4. Scale based on metrics

---

## 🎓 Summary

**What You Have:**
- ✅ Native LangGraph agents (working)
- ✅ Database models (User, APIKey, Migration)
- ✅ Services (MigrationService, UsageTracker, AuthService)
- ✅ AWS CDK infrastructure (ready to deploy)

**What's Next:**
- ⏳ Flask admin dashboard (Tailwind CSS)
- ⏳ FastAPI public API (with auth)
- ⏳ Local testing
- ⏳ Production deployment guide

**Learning Path:**
1. Master Flask + FastAPI (this week)
2. Learn Docker (containerize apps)
3. Learn Kubernetes (deploy locally)
4. Learn Terraform (AWS infrastructure)
5. Deploy to production (EKS + RDS)

**Your Advantage:**
Starting local lets you understand the entire stack before scaling. When you're ready for K8s + Terraform, you'll know exactly what you're deploying!
