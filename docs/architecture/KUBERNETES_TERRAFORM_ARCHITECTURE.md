# DataMigrate AI - Kubernetes & Terraform Architecture

**Author:** Alexander Garcia Angus
**Property of:** OKO Investments

## 🏗️ Complete Technology Stack

### Infrastructure Layer (Terraform):
- **Amazon EKS** - Kubernetes orchestration
- **Amazon VPC** - Network isolation
- **Amazon RDS PostgreSQL** - Relational database
- **Amazon ElastiCache Redis** - Caching & message broker
- **Amazon ECR** - Docker image registry
- **AWS Secrets Manager** - Secure credential storage
- **Amazon S3** - Object storage & frontend hosting
- **Amazon CloudFront** - CDN for frontend
- **AWS ALB** - Application Load Balancer
- **AWS CloudWatch** - Monitoring & logging
- **AWS Route53** - DNS management (optional)
- **AWS WAF** - Web Application Firewall (optional)

### Application Layer (Kubernetes):
- **FastAPI Backend** - RESTful API (Python 3.12)
- **Vue.js 3 Frontend** - Modern SPA (TypeScript)
- **LangGraph Agents** - Multi-agent AI system
- **Celery Workers** - Background task processing
- **Nginx Ingress** - Kubernetes ingress controller

---

## 📐 Complete Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Internet / Users                                │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     AWS Route53 (DNS) - Optional                         │
│                   app.datamigrate.ai → CloudFront                        │
│                   api.datamigrate.ai → ALB                               │
└────────────────────┬──────────────────────────┬─────────────────────────┘
                     │                          │
         ┌───────────▼───────────┐   ┌─────────▼──────────┐
         │  CloudFront CDN       │   │   AWS WAF          │
         │  (Vue.js Frontend)    │   │ (Security Rules)   │
         └───────────┬───────────┘   └─────────┬──────────┘
                     │                          │
                     ▼                          ▼
         ┌────────────────────────────────────────────────────┐
         │              S3 Static Website                      │
         │         (Vue.js build artifacts)                    │
         └─────────────────────────────────────────────────────┘

                                        ▼
         ┌────────────────────────────────────────────────────┐
         │     Application Load Balancer (ALB)                │
         │           HTTPS/HTTP (Port 443/80)                 │
         └──────────────────┬──────────────────────────────────┘
                            │
         ┌──────────────────▼───────────────────────────────────┐
         │                  Amazon EKS Cluster                   │
         │              (Kubernetes 1.28)                        │
         │                                                       │
         │  ┌─────────────────────────────────────────────────┐ │
         │  │        Nginx Ingress Controller                 │ │
         │  │     (Routes traffic to services)                │ │
         │  └────────┬──────────────────────────┬─────────────┘ │
         │           │                          │                │
         │  ┌────────▼──────────┐    ┌─────────▼──────────┐    │
         │  │  FastAPI Service  │    │ LangGraph Service  │    │
         │  │  (RESTful API)    │    │  (AI Agents)       │    │
         │  │                   │    │                    │    │
         │  │  Deployment:      │    │  Deployment:       │    │
         │  │  - 3 Replicas     │    │  - 2 Replicas      │    │
         │  │  - Auto-scaling   │    │  - GPU support     │    │
         │  │  - Health checks  │    │  - Stateful pods   │    │
         │  └────────┬──────────┘    └──────────┬─────────┘    │
         │           │                          │                │
         │  ┌────────▼───────────────────────────▼──────────┐  │
         │  │        Celery Worker Service                   │  │
         │  │     (Background Tasks & Migrations)            │  │
         │  │                                                │  │
         │  │  Deployment:                                  │  │
         │  │  - 5 Replicas (auto-scaling 2-20)            │  │
         │  │  - Task queue from Redis                     │  │
         │  │  - Long-running migrations                   │  │
         │  └─────────────────────────────────────────────────┘ │
         │                                                       │
         │  ┌─────────────────────────────────────────────────┐ │
         │  │         Kubernetes Node Group                   │ │
         │  │  - t3.medium instances (2-10 nodes)            │ │
         │  │  - Auto-scaling based on CPU/memory            │ │
         │  │  - Spot instances (dev) / On-demand (prod)     │ │
         │  └─────────────────────────────────────────────────┘ │
         └───────────────────────────────────────────────────────┘
                            │
                            │
         ┌──────────────────▼───────────────────────────────────┐
         │           Data & Caching Layer                        │
         │                                                       │
         │  ┌──────────────────────┐  ┌──────────────────────┐ │
         │  │  ElastiCache Redis   │  │  RDS PostgreSQL 15   │ │
         │  │  (Cluster Mode)      │  │  (Multi-AZ)          │ │
         │  │                      │  │                      │ │
         │  │  - Caching           │  │  - Users             │ │
         │  │  - Celery broker     │  │  - Migrations        │ │
         │  │  - Session storage   │  │  - API keys          │ │
         │  │  - 3 nodes (prod)    │  │  - Usage logs        │ │
         │  │  - Encryption        │  │  - Automated backups │ │
         │  └──────────────────────┘  └──────────────────────┘ │
         └───────────────────────────────────────────────────────┘

         ┌─────────────────────────────────────────────────────┐
         │          Supporting AWS Services                     │
         │                                                      │
         │  - ECR (Docker images)                              │
         │  - Secrets Manager (credentials)                    │
         │  - CloudWatch (logs & metrics)                      │
         │  - IAM (IRSA - IAM Roles for Service Accounts)     │
         │  - VPC (network isolation)                          │
         │  - S3 (dbt artifacts, migration state)              │
         └─────────────────────────────────────────────────────┘
```

---

## 🔄 Request Flow

### 1. Frontend Request (Vue.js)
```
User Browser
  → CloudFront CDN (edge cache)
    → S3 Static Website
      → Downloads: index.html, app.js, app.css
        → User sees Vue.js app
```

### 2. API Request (FastAPI)
```
Vue.js App
  → API call (fetch/axios)
    → ALB (load balancer)
      → Nginx Ingress (Kubernetes)
        → FastAPI Pod (1 of 3 replicas)
          → Checks Redis cache (hit/miss)
            → If miss: Query PostgreSQL
              → Return data to client
```

### 3. Migration Request (LangGraph Agents)
```
User initiates migration
  → FastAPI receives request
    → Creates Celery task
      → Pushes to Redis queue
        → Celery Worker picks up task
          → Spawns LangGraph agent
            → Multi-agent workflow:
              1. Metadata Extraction Agent
              2. Schema Analysis Agent
              3. dbt Model Generator Agent
              4. Validator Agent
              5. Orchestrator Agent
            → Saves results to PostgreSQL
              → Updates migration status
                → Frontend polls for updates
```

### 4. Background Task (Celery)
```
Celery Beat (scheduler)
  → Triggers periodic task
    → Pushes to Redis queue
      → Celery Worker executes
        → Example: cleanup old migrations
        → Example: send usage reports
        → Example: refresh caches
```

---

## 🐳 Docker Images & ECR

### 1. FastAPI Backend
```dockerfile
# Dockerfile.fastapi
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "fastapi_app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Pushed to:** `<aws-account-id>.dkr.ecr.us-east-1.amazonaws.com/datamigrate-ai/dev/fastapi:latest`

### 2. LangGraph Agents
```dockerfile
# Dockerfile.langgraph
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install langgraph langchain anthropic
COPY agents/ ./agents/
CMD ["python", "-m", "agents.orchestrator"]
```

**Pushed to:** `<aws-account-id>.dkr.ecr.us-east-1.amazonaws.com/datamigrate-ai/dev/langgraph-agents:latest`

### 3. Celery Worker
```dockerfile
# Dockerfile.celery
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install celery redis sqlalchemy
COPY . .
CMD ["celery", "-A", "tasks", "worker", "--loglevel=info"]
```

**Pushed to:** `<aws-account-id>.dkr.ecr.us-east-1.amazonaws.com/datamigrate-ai/dev/celery-worker:latest`

---

## ☸️ Kubernetes Deployments

### 1. FastAPI Deployment

```yaml
# k8s/fastapi-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi
  namespace: datamigrate-ai
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fastapi
  template:
    metadata:
      labels:
        app: fastapi
    spec:
      containers:
      - name: fastapi
        image: <ecr-repo>/fastapi:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: connection-string
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-credentials
              key: connection-string
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: fastapi-service
  namespace: datamigrate-ai
spec:
  selector:
    app: fastapi
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fastapi-hpa
  namespace: datamigrate-ai
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fastapi
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### 2. Celery Worker Deployment

```yaml
# k8s/celery-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: celery-worker
  namespace: datamigrate-ai
spec:
  replicas: 5
  selector:
    matchLabels:
      app: celery-worker
  template:
    metadata:
      labels:
        app: celery-worker
    spec:
      containers:
      - name: celery-worker
        image: <ecr-repo>/celery-worker:latest
        env:
        - name: CELERY_BROKER_URL
          valueFrom:
            secretKeyRef:
              name: redis-credentials
              key: connection-string
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: connection-string
        resources:
          requests:
            memory: "1Gi"
            cpu: "1000m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: celery-worker-hpa
  namespace: datamigrate-ai
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: celery-worker
  minReplicas: 2
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 75
```

### 3. Nginx Ingress

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: datamigrate-ingress
  namespace: datamigrate-ai
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - api.datamigrate.ai
    secretName: api-tls
  rules:
  - host: api.datamigrate.ai
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: fastapi-service
            port:
              number: 80
```

---

## 🔒 Secrets Management

### AWS Secrets Manager

```bash
# Create database secret
aws secretsmanager create-secret \
  --name datamigrate-ai/dev/database \
  --secret-string '{
    "username": "admin",
    "password": "STRONG_PASSWORD_HERE",
    "host": "datamigrate-ai-dev-db.abc123.us-east-1.rds.amazonaws.com",
    "port": 5432,
    "database": "datamigrate_ai"
  }'

# Create Redis secret
aws secretsmanager create-secret \
  --name datamigrate-ai/dev/redis \
  --secret-string '{
    "auth_token": "REDIS_AUTH_TOKEN_16_CHARS",
    "endpoint": "datamigrate-ai-dev-redis.abc123.cache.amazonaws.com",
    "port": 6379
  }'
```

### Kubernetes ExternalSecrets Operator

```yaml
# k8s/external-secrets.yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: db-credentials
  namespace: datamigrate-ai
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: db-credentials
    creationPolicy: Owner
  data:
  - secretKey: connection-string
    remoteRef:
      key: datamigrate-ai/dev/database
      property: connection_string
```

---

## 📊 Monitoring & Logging

### CloudWatch Dashboards

**1. EKS Cluster Dashboard**
- CPU utilization per node
- Memory utilization per node
- Pod count
- Network I/O

**2. Application Dashboard**
- API request rate
- API error rate
- Response times (p50, p95, p99)
- Active database connections

**3. Migration Dashboard**
- Migrations in progress
- Migrations completed (last 24h)
- Migration success rate
- Average migration time

### CloudWatch Alarms

```hcl
# Terraform alarm example
resource "aws_cloudwatch_metric_alarm" "api_error_rate" {
  alarm_name          = "datamigrate-ai-api-error-rate-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "5xxErrorRate"
  namespace           = "AWS/ApplicationELB"
  period              = "300"
  statistic           = "Average"
  threshold           = "5"
  alarm_description   = "API error rate is too high"

  dimensions = {
    LoadBalancer = aws_lb.main.arn_suffix
  }
}
```

---

## 💰 Cost Breakdown (with Kubernetes)

### Development Environment (~$250/month):

| Service | Configuration | Monthly Cost |
|---------|--------------|--------------|
| **EKS Control Plane** | 1 cluster | $73.00 |
| **EKS Worker Nodes** | 2x t3.medium | $60.00 |
| **RDS PostgreSQL** | db.t3.micro | $14.00 |
| **ElastiCache Redis** | cache.t3.micro | $12.00 |
| **NAT Gateways** | 3x NAT | $32.40 |
| **ALB** | Application Load Balancer | $16.00 |
| **S3 + CloudFront** | Frontend | $10.00 |
| **ECR** | Docker images | $3.00 |
| **CloudWatch** | Logs & Metrics | $15.00 |
| **Secrets Manager** | 5 secrets | $2.50 |
| **Data Transfer** | Estimated | $20.00 |
| **Total** | | **~$258/month** |

### Production Environment (~$1,200-2,000/month):

| Service | Configuration | Monthly Cost |
|---------|--------------|--------------|
| **EKS Control Plane** | 1 cluster | $73.00 |
| **EKS Worker Nodes** | 4-10x t3.large (avg 6) | $375.00 |
| **RDS PostgreSQL** | db.t3.large Multi-AZ | $280.00 |
| **ElastiCache Redis** | cache.m5.large (3 nodes) | $260.00 |
| **NAT Gateways** | 3x NAT | $32.40 |
| **ALB** | Application Load Balancer | $16.00 |
| **S3 + CloudFront** | Frontend (high traffic) | $50.00 |
| **ECR** | Docker images | $10.00 |
| **CloudWatch** | Logs & Metrics | $80.00 |
| **Secrets Manager** | 10 secrets | $5.00 |
| **Data Transfer** | Estimated | $100.00 |
| **WAF** | Optional security | $50.00 |
| **Total** | | **~$1,331/month** |

**Cost Optimization:**
- Use Reserved Instances for RDS (40% savings)
- Use Spot Instances for non-critical workers (70% savings)
- Implement auto-scaling (scale down during off-hours)
- Use VPC Endpoints to eliminate NAT costs

---

## 🚀 Deployment Workflow

### 1. Build Docker Images

```bash
# Build all images
docker build -t fastapi:latest -f Dockerfile.fastapi .
docker build -t langgraph-agents:latest -f Dockerfile.langgraph .
docker build -t celery-worker:latest -f Dockerfile.celery .

# Tag for ECR
docker tag fastapi:latest <ecr-repo>/fastapi:latest
docker tag langgraph-agents:latest <ecr-repo>/langgraph-agents:latest
docker tag celery-worker:latest <ecr-repo>/celery-worker:latest

# Push to ECR
docker push <ecr-repo>/fastapi:latest
docker push <ecr-repo>/langgraph-agents:latest
docker push <ecr-repo>/celery-worker:latest
```

### 2. Deploy Infrastructure (Terraform)

```bash
cd terraform/environments/dev
terraform init
terraform plan
terraform apply
```

### 3. Configure kubectl

```bash
# Get EKS cluster credentials
aws eks update-kubeconfig \
  --region us-east-1 \
  --name datamigrate-ai-dev-eks

# Verify connection
kubectl get nodes
```

### 4. Deploy Kubernetes Resources

```bash
# Create namespace
kubectl create namespace datamigrate-ai

# Apply secrets
kubectl apply -f k8s/external-secrets.yaml

# Deploy applications
kubectl apply -f k8s/fastapi-deployment.yaml
kubectl apply -f k8s/celery-deployment.yaml
kubectl apply -f k8s/ingress.yaml

# Check status
kubectl get pods -n datamigrate-ai
kubectl get services -n datamigrate-ai
```

### 5. Deploy Frontend

```bash
cd frontend
npm run build
aws s3 sync dist/ s3://datamigrate-ai-dev-frontend --delete
aws cloudfront create-invalidation --distribution-id <id> --paths "/*"
```

---

## ✅ Technology Stack Summary

| Category | Technology | Purpose |
|----------|------------|---------|
| **IaC** | Terraform | Infrastructure as Code |
| **Orchestration** | Kubernetes (EKS) | Container orchestration |
| **Container Registry** | Amazon ECR | Docker images |
| **Frontend** | Vue.js 3 + TypeScript | SPA framework |
| **Backend** | FastAPI + Python 3.12 | REST API |
| **AI Agents** | LangGraph + LangChain | Multi-agent system |
| **Task Queue** | Celery + Redis | Background jobs |
| **Database** | PostgreSQL 15 (RDS) | Relational data |
| **Cache** | Redis (ElastiCache) | Caching + message broker |
| **CDN** | CloudFront | Frontend delivery |
| **Load Balancer** | AWS ALB | Traffic distribution |
| **Monitoring** | CloudWatch | Logs + metrics |
| **Secrets** | AWS Secrets Manager | Credential storage |
| **CI/CD** | GitHub Actions | Automated deployment |

---

**This is an enterprise-grade, production-ready architecture designed for OKO Investments!**

