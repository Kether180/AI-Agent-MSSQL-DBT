# Go + Python Hybrid Architecture

**Project:** DataMigrate AI
**Author:** Alexander Garcia Angus
**Date:** November 27, 2025

---

## Architecture Overview

DataMigrate AI uses a **hybrid microservices architecture** where Go handles high-frequency API operations (95% of requests) and Python handles AI agent orchestration (5% of requests).

```
┌─────────────────────────────────────────────────────────────────┐
│                         Users / Frontend                         │
│                    (Vue.js 3 + TypeScript)                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS (Port 443)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              Application Load Balancer (ALB)                     │
│              - SSL Termination                                   │
│              - Health Checks                                     │
│              - Request Routing                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │
              ┌───────────────┴───────────────┐
              │                               │
              ▼                               ▼
┌─────────────────────────────┐   ┌──────────────────────────────┐
│    Go API Service           │   │   Python Agent Service        │
│    (Gin Framework)          │   │   (FastAPI + LangGraph)       │
│    Port: 8000               │   │   Port: 8001                  │
│                             │   │                               │
│  Handles 95% of traffic:    │   │  Handles 5% of traffic:       │
│  ✓ POST /api/v1/login       │   │  ✓ POST /run-agents          │
│  ✓ GET /api/v1/migrations   │   │  ✓ LangGraph orchestration   │
│  ✓ GET /api/v1/migrations/:id│  │  ✓ Claude API integration    │
│  ✓ POST /api/v1/api-keys    │   │  ✓ State management          │
│  ✓ All CRUD operations      │   │  ✓ Checkpoint system         │
│                             │   │                               │
│  Performance:               │   │  Performance:                 │
│  - Latency: 50-100ms        │   │  - Duration: 5-30 minutes    │
│  - Memory: 50MB per pod     │   │  - Memory: 200MB per pod     │
│  - Concurrency: 10k+ req/s  │   │  - Concurrency: 1-5 concurrent│
└─────────────────────────────┘   └──────────────────────────────┘
              │                               │
              │                               │
              └───────────────┬───────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Shared Data Layer                             │
│                                                                  │
│  ┌──────────────────────┐    ┌───────────────────────┐         │
│  │  PostgreSQL RDS      │    │  Redis ElastiCache    │         │
│  │  - Users             │    │  - Session storage    │         │
│  │  - API Keys          │    │  - API rate limiting  │         │
│  │  - Migrations        │    │  - Celery broker      │         │
│  │  - Model Files       │    │  - Cache layer        │         │
│  │  - Usage Logs        │    └───────────────────────┘         │
│  └──────────────────────┘                                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Request Flow Examples

### **Example 1: User Login (Go handles 100%)**

```
1. POST /api/v1/login
   ↓
2. Go API receives request (8ms)
   ↓
3. Query PostgreSQL for user (15ms)
   ↓
4. Verify password with bcrypt (30ms)
   ↓
5. Generate JWT token (5ms)
   ↓
6. Return token to user (2ms)

Total: 60ms (vs Python's 200ms)
```

### **Example 2: List Migrations (Go handles 100%)**

```
1. GET /api/v1/migrations?limit=50
   ↓
2. Go API validates JWT (5ms)
   ↓
3. Query PostgreSQL with pagination (20ms)
   ↓
4. Serialize to JSON (5ms)
   ↓
5. Return to user (2ms)

Total: 32ms (vs Python's 150ms)
```

### **Example 3: Create Migration (Go 90% + Python 10%)**

```
1. POST /api/v1/migrations
   ↓
2. Go API receives request (5ms)
   ↓
3. Validate input (Go validation: 8ms)
   ↓
4. Save to PostgreSQL (15ms)
   ↓
5. Return migration object to user immediately (2ms)

   User sees response: 30ms ✓

   Meanwhile (async, in background):
   ↓
6. Go spawns goroutine to call Python service
   ↓
7. HTTP POST http://python-service:8001/run-agents
   {
     "migration_id": 123,
     "metadata_json": "..."
   }
   ↓
8. Python service receives request
   ↓
9. Initialize LangGraph state
   ↓
10. Run 6-agent workflow:
    - Assessment Agent (2 min)
    - Planner Agent (3 min)
    - Executor Agent (8 min)
    - Tester Agent (5 min)
    - Rebuilder Agent (4 min)
    - Evaluator Agent (2 min)
   ↓
11. Save generated dbt models to PostgreSQL
   ↓
12. Update migration status to "completed"

   Total background time: 24 minutes
```

**Key Point:** User gets response in 30ms, not 24 minutes!

---

## Service Communication

### **Go → Python Communication**

```go
// Go API calls Python service asynchronously

package main

import (
    "bytes"
    "encoding/json"
    "net/http"
    "time"
)

// AgentRequest is the payload sent to Python service
type AgentRequest struct {
    MigrationID  uint   `json:"migration_id"`
    MetadataJSON string `json:"metadata_json"`
    UserID       uint   `json:"user_id"`
}

// callPythonAgents sends request to Python service
func callPythonAgents(migration Migration) error {
    payload := AgentRequest{
        MigrationID:  migration.ID,
        MetadataJSON: migration.MetadataJSON,
        UserID:       migration.UserID,
    }

    jsonData, err := json.Marshal(payload)
    if err != nil {
        return err
    }

    // HTTP POST to Python service
    client := &http.Client{
        Timeout: 30 * time.Second, // 30 sec timeout for connection
    }

    resp, err := client.Post(
        "http://python-service:8001/run-agents",
        "application/json",
        bytes.NewBuffer(jsonData),
    )

    if err != nil {
        log.Printf("Failed to call Python service: %v", err)
        // Update migration status to "failed"
        db.Model(&migration).Update("status", "failed")
        return err
    }
    defer resp.Body.Close()

    if resp.StatusCode != 200 {
        log.Printf("Python service returned error: %d", resp.StatusCode)
        return fmt.Errorf("agent execution failed")
    }

    log.Printf("Agents started for migration %d", migration.ID)
    return nil
}
```

### **Python Service Endpoint**

```python
# Python service receives requests from Go API

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agents.orchestrator import run_langgraph_workflow

app = FastAPI()

class AgentRequest(BaseModel):
    migration_id: int
    metadata_json: str
    user_id: int

@app.post("/run-agents")
async def run_agents(request: AgentRequest):
    """
    Run LangGraph agents for migration.
    This is your EXISTING code - no changes needed!
    """
    try:
        # Load migration from database
        migration = db.query(Migration).filter(
            Migration.id == request.migration_id
        ).first()

        if not migration:
            raise HTTPException(status_code=404, detail="Migration not found")

        # Update status to "running"
        migration.status = "running"
        migration.started_at = datetime.utcnow()
        db.commit()

        # Run LangGraph workflow (YOUR EXISTING CODE)
        result = await run_langgraph_workflow(
            migration_id=request.migration_id,
            metadata_json=request.metadata_json
        )

        # Update status to "completed"
        migration.status = "completed"
        migration.completed_at = datetime.utcnow()
        migration.success_rate = result.get("success_rate", 0)
        db.commit()

        return {
            "status": "success",
            "migration_id": request.migration_id,
            "models_generated": len(result.get("models", []))
        }

    except Exception as e:
        # Update status to "failed"
        migration.status = "failed"
        migration.error = str(e)
        db.commit()

        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
```

---

## Database Access Pattern

Both services access the **same PostgreSQL database** but for different purposes:

### **Go Service Database Usage:**

```go
// Go handles fast CRUD operations

// Read operations (99% of Go's DB queries)
func getMigrations(userID uint) []Migration {
    var migrations []Migration
    db.Where("user_id = ?", userID).
       Order("created_at DESC").
       Limit(50).
       Find(&migrations)
    return migrations  // 20ms query
}

func getMigrationStatus(id uint) Migration {
    var migration Migration
    db.First(&migration, id)
    return migration  // 5ms query
}

// Write operations (1% of Go's DB queries)
func createMigration(req MigrationRequest) Migration {
    migration := Migration{
        Name:         req.Name,
        Status:       "pending",
        MetadataJSON: req.MetadataJSON,
        UserID:       req.UserID,
    }
    db.Create(&migration)
    return migration  // 15ms insert
}
```

### **Python Service Database Usage:**

```python
# Python handles complex state updates

async def run_langgraph_workflow(migration_id: int, metadata_json: str):
    """
    Python updates migration state throughout the workflow
    """
    migration = db.query(Migration).filter(Migration.id == migration_id).first()

    # Update status after each agent completes
    migration.status = "running"
    migration.phase = "assessment"
    db.commit()

    # Assessment agent runs (2 minutes)
    assessment_result = await assessment_agent.run(metadata_json)

    migration.phase = "planning"
    db.commit()

    # Planner agent runs (3 minutes)
    plan = await planner_agent.run(assessment_result)

    migration.phase = "execution"
    db.commit()

    # ... continue for all 6 agents

    # Save generated dbt models
    for model in generated_models:
        db_model = ModelFile(
            migration_id=migration_id,
            name=model.name,
            sql_code=model.sql,
            status="completed"
        )
        db.add(db_model)

    migration.status = "completed"
    migration.completed_at = datetime.utcnow()
    db.commit()
```

---

## Deployment Configuration

### **Docker Compose (Development)**

```yaml
version: '3.8'

services:
  go-api:
    build:
      context: ./go-api
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://user:pass@postgres:5432/datamigrate
      REDIS_URL: redis://redis:6379
      PYTHON_SERVICE_URL: http://python-service:8001
    depends_on:
      - postgres
      - redis
      - python-service

  python-service:
    build:
      context: ./python-service
      dockerfile: Dockerfile
    ports:
      - "8001:8001"
    environment:
      DATABASE_URL: postgresql://user:pass@postgres:5432/datamigrate
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
    depends_on:
      - postgres

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: datamigrate
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

### **Kubernetes Deployment (Production)**

```yaml
# go-api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: go-api
spec:
  replicas: 3  # 3 replicas for high availability
  selector:
    matchLabels:
      app: go-api
  template:
    metadata:
      labels:
        app: go-api
    spec:
      containers:
      - name: go-api
        image: datamigrate-ai/go-api:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "128Mi"  # Go uses very little memory!
            cpu: "250m"
          limits:
            memory: "256Mi"
            cpu: "500m"
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secrets
              key: connection-string
        - name: PYTHON_SERVICE_URL
          value: "http://python-service:8001"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
# python-service-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: python-service
spec:
  replicas: 2  # Fewer replicas since it handles less traffic
  selector:
    matchLabels:
      app: python-service
  template:
    metadata:
      labels:
        app: python-service
    spec:
      containers:
      - name: python-service
        image: datamigrate-ai/python-service:latest
        ports:
        - containerPort: 8001
        resources:
          requests:
            memory: "512Mi"  # Python needs more memory
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secrets
              key: connection-string
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: anthropic-key
```

---

## Performance Comparison

| Metric | Python (FastAPI) Monolith | Go + Python Hybrid |
|--------|---------------------------|-------------------|
| **API Latency (p50)** | 200ms | 50ms (4x faster) |
| **API Latency (p95)** | 500ms | 100ms (5x faster) |
| **Memory per Pod** | 200MB | Go: 50MB, Python: 200MB |
| **Concurrent Requests** | 1,000 req/s | 10,000 req/s (10x better) |
| **Startup Time** | 3 seconds | Go: 100ms, Python: 3s |
| **Container Size** | 400MB | Go: 20MB, Python: 400MB |

---

## Benefits Summary

### **Performance Benefits:**
- ✅ 4-5x faster API response times
- ✅ 10x higher concurrent request capacity
- ✅ 50% lower memory usage for API pods

### **Cost Benefits:**
- ✅ Fewer replicas needed (Go handles more traffic per pod)
- ✅ Smaller container images (Go binaries are tiny)
- ✅ Lower AWS costs due to resource efficiency

### **Development Benefits:**
- ✅ Keep existing Python LangGraph code (no rewrite!)
- ✅ Go is easier to learn than Rust (1-2 weeks)
- ✅ Clear separation of concerns (API vs agents)

### **Operational Benefits:**
- ✅ Independent scaling (scale API and agents separately)
- ✅ Independent deployment (deploy Go without touching Python)
- ✅ Easier debugging (logs separated by service)

---

**Author:** Alexander Garcia Angus
**Company:** OKO Investments
**Date:** November 27, 2025
