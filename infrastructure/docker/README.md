# DataMigrate AI - Docker Infrastructure (Terraform)

Infrastructure as Code for local Docker development environment.

**Author:** Alexander Garcia Angus
**Property of:** OKO Investments

---

## Prerequisites

1. **Docker Desktop** - Running on Windows
2. **Terraform** - Located at `C:\terraform\terraform.exe`
   - Download AMD64 from: https://developer.hashicorp.com/terraform/downloads
   - Extract to `C:\terraform\`
   - Add to PATH or use full path

---

## Quick Start (First Time Setup)

```powershell
# 1. Make sure Docker Desktop is running

# 2. Navigate to infrastructure directory
cd C:\Users\gag_a\Desktop\AI-Agent-MSSQL-DBT\infrastructure\docker

# 3. Create secrets.tfvars with your passwords (this file is gitignored)
# Create file: secrets.tfvars with contents:
#   postgres_password      = "your-secure-password"
#   grafana_admin_password = "your-secure-password"

# 4. Initialize Terraform (downloads Docker provider)
C:\terraform\terraform.exe init

# 5. Create all infrastructure (loads both var files)
C:\terraform\terraform.exe apply -var-file="variables.tfvars" -var-file="secrets.tfvars" -auto-approve

# 6. Verify container is running
docker ps
```

---

## Daily Developer Commands

### Terraform Commands

```powershell
# Navigate to infrastructure directory first
cd C:\Users\gag_a\Desktop\AI-Agent-MSSQL-DBT\infrastructure\docker

# View current infrastructure state
C:\terraform\terraform.exe show

# List all managed resources
C:\terraform\terraform.exe state list

# See what changes would be made
C:\terraform\terraform.exe plan -var-file="variables.tfvars"

# Apply changes
C:\terraform\terraform.exe apply -var-file="variables.tfvars"

# Destroy all infrastructure (careful!)
C:\terraform\terraform.exe destroy -var-file="variables.tfvars"

# Recreate from scratch
C:\terraform\terraform.exe destroy -var-file="variables.tfvars" -auto-approve
C:\terraform\terraform.exe apply -var-file="variables.tfvars" -auto-approve
```

### Docker Commands

```powershell
# Check container status
docker ps

# View PostgreSQL logs
docker logs datamigrate-postgres-dev

# Follow logs in real-time
docker logs -f datamigrate-postgres-dev

# Connect to PostgreSQL CLI
docker exec -it datamigrate-postgres-dev psql -U datamigrate -d datamigrate

# List all tables
docker exec datamigrate-postgres-dev psql -U datamigrate -d datamigrate -c "\dt"

# Check pgvector extension
docker exec datamigrate-postgres-dev psql -U datamigrate -d datamigrate -c "\dx vector"

# View RAG tables schema
docker exec datamigrate-postgres-dev psql -U datamigrate -d datamigrate -c "\d schema_embeddings"

# Stop container (preserves data)
docker stop datamigrate-postgres-dev

# Start container
docker start datamigrate-postgres-dev

# Restart container
docker restart datamigrate-postgres-dev
```

### Backend Commands

```powershell
# Start backend (from project root)
cd C:\Users\gag_a\Desktop\AI-Agent-MSSQL-DBT\backend
go run cmd/server/main.go

# Backend will automatically:
# - Connect to Docker PostgreSQL
# - Run migrations
# - Create RAG tables with pgvector
```

---

## What Gets Created

| Resource | Name | Description |
|----------|------|-------------|
| Network | `datamigrate-network-dev` | Bridge network for containers |
| Volume | `datamigrate-pgdata-dev` | Persistent storage for PostgreSQL |
| Volume | `datamigrate-prometheus-dev` | Persistent storage for Prometheus metrics |
| Volume | `datamigrate-grafana-dev` | Persistent storage for Grafana dashboards |
| Container | `datamigrate-postgres-dev` | PostgreSQL 16 with pgvector |
| Container | `datamigrate-prometheus-dev` | Prometheus metrics collector |
| Container | `datamigrate-grafana-dev` | Grafana dashboards |
| Extension | `pgvector 0.8.1` | Vector similarity search |
| Tables | 15 tables | Including 4 RAG tables with vector columns |

### RAG Tables (pgvector)

| Table | Purpose |
|-------|---------|
| `schema_embeddings` | Schema pattern embeddings for learning |
| `transformation_embeddings` | SQL transformation patterns |
| `knowledge_embeddings` | dbt best practices knowledge base |
| `rag_query_cache` | Query cache for performance |

---

## Monitoring (Prometheus + Grafana)

### Access URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| **Prometheus** | http://localhost:9090 | No auth required |
| **Grafana** | http://localhost:3001 | admin / datamigrate123 |

### Prometheus Features
- Metrics collection every 15 seconds
- Scrapes Go backend at `/metrics` endpoint
- Self-monitoring enabled
- Data persisted in Docker volume

### Grafana Features
- Pre-configured Prometheus datasource
- Auto-provisions dashboards
- Persistent dashboard storage
- Dark theme enabled by default

### Monitoring Commands

```powershell
# View Prometheus logs
docker logs datamigrate-prometheus-dev

# View Grafana logs
docker logs datamigrate-grafana-dev

# Reload Prometheus config (without restart)
curl -X POST http://localhost:9090/-/reload

# Access Prometheus targets
# Open: http://localhost:9090/targets
```

### Disable Monitoring

To disable monitoring and save resources:

```powershell
# Edit variables.tfvars
enable_monitoring = false

# Apply changes
C:\terraform\terraform.exe apply -var-file="variables.tfvars"
```

---

## Environment Variables

The Terraform configuration uses these variables (defined in `variables.tfvars`):

| Variable | Default | Description |
|----------|---------|-------------|
| `environment` | dev | Environment name (dev, staging, prod) |
| `postgres_user` | datamigrate | Database username |
| `postgres_password` | datamigrate123 | Database password |
| `postgres_db` | datamigrate | Database name |
| `postgres_port` | 5432 | Exposed port on host |
| `enable_monitoring` | true | Enable Prometheus + Grafana |
| `prometheus_port` | 9090 | Prometheus exposed port |
| `grafana_port` | 3001 | Grafana exposed port |
| `grafana_admin_password` | datamigrate123 | Grafana admin password |

### Backend .env Configuration

Ensure `backend/.env` matches Terraform variables:

```env
DB_HOST=127.0.0.1
DB_PORT=5432
DB_USER=datamigrate
DB_PASSWORD=datamigrate123
DB_NAME=datamigrate
DB_SSL_MODE=disable
```

---

## Troubleshooting

### Port 5432 Already in Use

```powershell
# Check what's using the port
netstat -ano | findstr :5432

# If it's local PostgreSQL, stop it (Run as Admin)
Stop-Service postgresql-x64-16
```

### Container Won't Start

```powershell
# Check Docker logs
docker logs datamigrate-postgres-dev

# Remove and recreate
C:\terraform\terraform.exe destroy -var-file="variables.tfvars" -auto-approve
C:\terraform\terraform.exe apply -var-file="variables.tfvars" -auto-approve
```

### Terraform State Issues

```powershell
# Force refresh state from Docker
C:\terraform\terraform.exe refresh -var-file="variables.tfvars"

# If container exists but not in state, import it
C:\terraform\terraform.exe import docker_container.postgres <container_id>
```

---

## Migrating from Manual Docker

If you have a manually created container:

```powershell
# Stop and remove the old container
docker stop datamigrate-postgres
docker rm datamigrate-postgres

# Initialize Terraform
cd infrastructure\docker
C:\terraform\terraform.exe init

# Apply to create Terraform-managed container
C:\terraform\terraform.exe apply -var-file="variables.tfvars" -auto-approve
```

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           Docker Desktop                                  │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                    datamigrate-network-dev                         │  │
│  │                                                                    │  │
│  │  ┌─────────────────────┐  ┌─────────────────┐  ┌────────────────┐  │  │
│  │  │ datamigrate-        │  │ datamigrate-    │  │ datamigrate-   │  │  │
│  │  │ postgres-dev        │  │ prometheus-dev  │  │ grafana-dev    │  │  │
│  │  │ PostgreSQL 16       │  │ Prometheus      │  │ Grafana        │  │  │
│  │  │ + pgvector 0.8.1    │  │ Port: 9090      │  │ Port: 3001     │  │  │
│  │  │ Port: 5432          │  │                 │  │                │  │  │
│  │  └─────────────────────┘  └─────────────────┘  └────────────────┘  │  │
│  │           │                       │                    │           │  │
│  └───────────┼───────────────────────┼────────────────────┼───────────┘  │
└──────────────┼───────────────────────┼────────────────────┼──────────────┘
               │                       │                    │
               │ localhost:5432        │ localhost:9090     │ localhost:3001
               ▼                       ▼                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                            Go Backend                                     │
│                        (cmd/server/main.go)                               │
│                            Port: 8080                                     │
│                         /metrics endpoint ────────────────► Prometheus    │
└──────────────────────────────────────────────────────────────────────────┘
```

---

**Last Updated:** December 2025
**Copyright:** OKO Investments. All rights reserved.
