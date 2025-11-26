# Kubernetes Manifests - DataMigrate AI

**Author:** Alexander Garcia Angus
**Property of:** OKO Investments

## Directory Structure

```
k8s/
├── base/                      # Base Kubernetes manifests
│   ├── namespace.yaml        # Namespace definition
│   ├── fastapi/              # FastAPI deployment & service
│   ├── celery/               # Celery worker deployment
│   ├── langgraph/            # LangGraph agents deployment
│   └── ingress.yaml          # Nginx ingress configuration
│
└── overlays/                  # Environment-specific overlays (Kustomize)
    ├── dev/                  # Development environment
    ├── staging/              # Staging environment
    └── prod/                 # Production environment
```

## Prerequisites

1. **EKS Cluster Running** (deployed via Terraform)
2. **kubectl** configured to access EKS
3. **Docker images** pushed to ECR

## Quick Start

### 1. Configure kubectl

```bash
# Get EKS cluster credentials
aws eks update-kubeconfig \
  --region us-east-1 \
  --name datamigrate-ai-dev-eks

# Verify connection
kubectl get nodes
```

### 2. Deploy to Development

```bash
# Create namespace
kubectl apply -f base/namespace.yaml

# Deploy all resources
kubectl apply -k overlays/dev/

# Check status
kubectl get pods -n datamigrate-ai
kubectl get services -n datamigrate-ai
kubectl get ingress -n datamigrate-ai
```

### 3. Monitor Deployments

```bash
# Watch pods
kubectl get pods -n datamigrate-ai --watch

# Check logs
kubectl logs -f deployment/fastapi -n datamigrate-ai

# Describe pod
kubectl describe pod <pod-name> -n datamigrate-ai
```

## Deployment Commands

### FastAPI Backend

```bash
kubectl apply -f base/fastapi/deployment.yaml
kubectl apply -f base/fastapi/service.yaml
kubectl apply -f base/fastapi/hpa.yaml
```

### Celery Workers

```bash
kubectl apply -f base/celery/deployment.yaml
kubectl apply -f base/celery/hpa.yaml
```

### LangGraph Agents

```bash
kubectl apply -f base/langgraph/deployment.yaml
kubectl apply -f base/langgraph/service.yaml
```

### Ingress

```bash
kubectl apply -f base/ingress.yaml
```

## Scaling

### Manual Scaling

```bash
# Scale FastAPI to 5 replicas
kubectl scale deployment fastapi --replicas=5 -n datamigrate-ai

# Scale Celery workers to 10 replicas
kubectl scale deployment celery-worker --replicas=10 -n datamigrate-ai
```

### Auto-Scaling (HPA)

HPA (Horizontal Pod Autoscaler) is configured for:
- **FastAPI**: 3-20 replicas (70% CPU, 80% memory)
- **Celery**: 2-20 replicas (75% CPU)

## Secrets

Secrets are managed via AWS Secrets Manager and External Secrets Operator:

```bash
# Install External Secrets Operator
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets -n external-secrets-system --create-namespace

# Apply secret configuration
kubectl apply -f base/secrets/
```

## Troubleshooting

### Pods not starting

```bash
# Check pod events
kubectl describe pod <pod-name> -n datamigrate-ai

# Check logs
kubectl logs <pod-name> -n datamigrate-ai

# Check image pull
kubectl get events -n datamigrate-ai
```

### Service not accessible

```bash
# Check service
kubectl get service fastapi-service -n datamigrate-ai

# Check endpoints
kubectl get endpoints fastapi-service -n datamigrate-ai

# Port-forward for testing
kubectl port-forward service/fastapi-service 8000:80 -n datamigrate-ai
```

### Ingress not working

```bash
# Check ingress
kubectl describe ingress datamigrate-ingress -n datamigrate-ai

# Check ingress controller
kubectl get pods -n ingress-nginx
```

## Useful Commands

```bash
# Get all resources
kubectl get all -n datamigrate-ai

# Delete all resources
kubectl delete -k overlays/dev/

# Restart deployment
kubectl rollout restart deployment/fastapi -n datamigrate-ai

# View rollout status
kubectl rollout status deployment/fastapi -n datamigrate-ai

# View rollout history
kubectl rollout history deployment/fastapi -n datamigrate-ai

# Rollback to previous version
kubectl rollout undo deployment/fastapi -n datamigrate-ai

# Execute command in pod
kubectl exec -it <pod-name> -n datamigrate-ai -- /bin/bash

# Copy files from pod
kubectl cp <pod-name>:/app/logs.txt ./logs.txt -n datamigrate-ai
```

## CI/CD Integration

See `.github/workflows/deploy.yml` for GitHub Actions deployment pipeline.

## Documentation

- [Kubernetes Terraform Architecture](../docs/architecture/KUBERNETES_TERRAFORM_ARCHITECTURE.md)
- [Terraform README](../terraform/README.md)
