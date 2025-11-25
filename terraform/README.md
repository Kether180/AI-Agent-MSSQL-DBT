# DataMigrate AI - Terraform Infrastructure

**Author:** Alexander Garcia Angus
**Property of:** OKO Investments

This directory contains Infrastructure as Code (IaC) using Terraform to deploy the DataMigrate AI platform to AWS.

## 📋 Table of Contents

- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Directory Structure](#directory-structure)
- [Modules](#modules)
- [Environments](#environments)
- [Deployment](#deployment)
- [Cost Estimation](#cost-estimation)
- [Security](#security)
- [Troubleshooting](#troubleshooting)

---

## 🏗️ Architecture

### Infrastructure Components:

```
┌─────────────────────────────────────────────────────────────┐
│                        CloudFront CDN                        │
│                    (Vue.js 3 Frontend)                       │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     S3 Static Website                        │
│              (Vue.js build artifacts)                        │
└──────────────────────────────────────────────────────────────┘

                         │ API Calls
                         ▼
┌─────────────────────────────────────────────────────────────┐
│            Application Load Balancer (ALB)                   │
│                     (HTTPS/HTTP)                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   ECS Fargate Cluster                        │
│              (FastAPI Backend - Auto-scaling)                │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│   │  FastAPI     │  │  FastAPI     │  │  FastAPI     │     │
│   │  Container   │  │  Container   │  │  Container   │     │
│   │  (Task 1)    │  │  (Task 2)    │  │  (Task 3)    │     │
│   └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  RDS PostgreSQL 15                           │
│              (Multi-AZ in Production)                        │
│   ┌──────────────────────────────────────────────┐          │
│   │  Database: datamigrate_ai                    │          │
│   │  - Users, API Keys, Migrations, Usage        │          │
│   │  - Automated backups (7 days retention)      │          │
│   │  - Encrypted storage                         │          │
│   └──────────────────────────────────────────────┘          │
└──────────────────────────────────────────────────────────────┘
```

### Network Architecture:

```
VPC (10.0.0.0/16)
├── Public Subnets (10.0.0.0/24, 10.0.1.0/24, 10.0.2.0/24)
│   ├── Internet Gateway
│   ├── NAT Gateways
│   └── Application Load Balancer
│
├── Private Subnets (10.0.10.0/24, 10.0.11.0/24, 10.0.12.0/24)
│   └── ECS Fargate Tasks (FastAPI containers)
│
└── Database Subnets (10.0.20.0/24, 10.0.21.0/24, 10.0.22.0/24)
    └── RDS PostgreSQL (isolated, no internet access)
```

---

## 📦 Prerequisites

### 1. **Install Terraform**

```bash
# macOS
brew install terraform

# Windows (with Chocolatey)
choco install terraform

# Linux
wget https://releases.hashicorp.com/terraform/1.6.6/terraform_1.6.6_linux_amd64.zip
unzip terraform_1.6.6_linux_amd64.zip
sudo mv terraform /usr/local/bin/
```

Verify installation:
```bash
terraform --version
# Should show: Terraform v1.6.0 or higher
```

### 2. **AWS CLI**

```bash
# macOS
brew install awscli

# Windows
choco install awscli

# Linux
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

Configure AWS credentials:
```bash
aws configure
# AWS Access Key ID: <your-access-key>
# AWS Secret Access Key: <your-secret-key>
# Default region: us-east-1
# Default output format: json
```

### 3. **Docker** (for building FastAPI image)

```bash
# macOS/Windows: Install Docker Desktop
# Linux: Install Docker Engine

docker --version
```

### 4. **Required AWS Permissions**

Your IAM user/role needs:
- VPC, Subnet, Route Table, Internet Gateway management
- EC2 (security groups, load balancers)
- ECS (clusters, services, tasks)
- RDS (instances, subnet groups, parameter groups)
- S3 (buckets, bucket policies)
- CloudFront (distributions)
- IAM (roles, policies)
- CloudWatch (logs, alarms)
- ECR (Docker image registry)

---

## 🚀 Quick Start

### Step 1: Initialize Terraform Backend

First, create the S3 bucket and DynamoDB table for Terraform state:

```bash
cd terraform

# Create S3 bucket for state
aws s3api create-bucket \
  --bucket datamigrate-ai-terraform-state \
  --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket datamigrate-ai-terraform-state \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket datamigrate-ai-terraform-state \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'

# Create DynamoDB table for state locking
aws dynamodb create-table \
  --table-name datamigrate-ai-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

### Step 2: Create Environment Variables File

```bash
cd environments/dev
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:
```hcl
# Environment
environment = "dev"
aws_region  = "us-east-1"

# Network
vpc_cidr           = "10.0.0.0/16"
availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]

# Database
db_instance_class = "db.t3.micro"  # Free tier eligible
db_name           = "datamigrate_ai"
db_username       = "admin"
db_password       = "CHANGE_ME_TO_STRONG_PASSWORD"  # Use AWS Secrets Manager in production!

# ECS
fastapi_image      = "<your-aws-account-id>.dkr.ecr.us-east-1.amazonaws.com/datamigrate-ai/fastapi:latest"
fastapi_cpu        = 512   # 0.5 vCPU
fastapi_memory     = 1024  # 1 GB
ecs_desired_count  = 2     # Number of tasks

# Frontend (optional)
domain_name     = ""  # e.g., "app.datamigrate.ai"
certificate_arn = ""  # ACM certificate ARN for HTTPS
```

### Step 3: Build and Push Docker Image

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <your-aws-account-id>.dkr.ecr.us-east-1.amazonaws.com

# Create ECR repository
aws ecr create-repository --repository-name datamigrate-ai/fastapi --region us-east-1

# Build Docker image
cd ../../  # Back to project root
docker build -t datamigrate-ai/fastapi:latest -f Dockerfile.fastapi .

# Tag image
docker tag datamigrate-ai/fastapi:latest \
  <your-aws-account-id>.dkr.ecr.us-east-1.amazonaws.com/datamigrate-ai/fastapi:latest

# Push to ECR
docker push <your-aws-account-id>.dkr.ecr.us-east-1.amazonaws.com/datamigrate-ai/fastapi:latest
```

### Step 4: Deploy Infrastructure

```bash
cd terraform/environments/dev

# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Deploy infrastructure
terraform apply

# Type 'yes' when prompted
```

**Deployment time:** ~15-20 minutes

### Step 5: Get Outputs

```bash
terraform output

# You'll see:
# api_endpoint = "datamigrate-ai-dev-alb-1234567890.us-east-1.elb.amazonaws.com"
# frontend_url = "d1234567890.cloudfront.net"
# database_endpoint = "datamigrate-ai-dev-db.abc123.us-east-1.rds.amazonaws.com:5432"
```

### Step 6: Deploy Frontend

```bash
cd ../../../frontend

# Build Vue.js app
npm run build

# Upload to S3
aws s3 sync dist/ s3://datamigrate-ai-dev-frontend --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id <cloudfront-distribution-id> \
  --paths "/*"
```

---

## 📁 Directory Structure

```
terraform/
├── main.tf                    # Root module - orchestrates all modules
├── variables.tf               # Input variables
├── outputs.tf                 # Output values
├── README.md                  # This file
│
├── modules/                   # Reusable infrastructure modules
│   ├── vpc/                   # VPC, subnets, NAT gateways
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   │
│   ├── security/              # Security groups
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   │
│   ├── rds/                   # PostgreSQL database
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   │
│   ├── ecs/                   # ECS Fargate cluster & services
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   │
│   └── s3_cloudfront/         # Frontend hosting
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
│
└── environments/              # Environment-specific configurations
    ├── dev/
    │   ├── main.tf           # Uses root module
    │   ├── terraform.tfvars  # Dev-specific values
    │   └── backend.tf        # Dev state backend
    │
    ├── staging/
    │   ├── main.tf
    │   ├── terraform.tfvars
    │   └── backend.tf
    │
    └── prod/
        ├── main.tf
        ├── terraform.tfvars
        └── backend.tf
```

---

## 🔧 Modules

### 1. **VPC Module** (`modules/vpc`)

Creates isolated network infrastructure:
- VPC with configurable CIDR
- 3 public subnets (for ALB, NAT Gateways)
- 3 private subnets (for ECS tasks)
- 3 database subnets (isolated, no internet)
- Internet Gateway
- NAT Gateways (one per AZ for high availability)
- Route tables and associations
- VPC Flow Logs for security monitoring

### 2. **Security Module** (`modules/security`)

Defines security groups with least privilege:
- **ALB Security Group**: Allow HTTP/HTTPS from internet
- **ECS Security Group**: Allow traffic from ALB only
- **RDS Security Group**: Allow PostgreSQL from ECS only
- **VPC Endpoints Security Group**: For private AWS service access

### 3. **RDS Module** (`modules/rds`)

PostgreSQL database infrastructure:
- PostgreSQL 15.5
- Encrypted storage (AES-256)
- Automated backups (3-7 days retention)
- Multi-AZ deployment (production)
- Performance Insights
- Enhanced monitoring
- CloudWatch alarms (CPU, memory, storage)
- Auto-scaling storage (20GB → 100GB)

### 4. **ECS Module** (`modules/ecs`)

Containerized FastAPI backend:
- ECS Fargate cluster (serverless containers)
- Application Load Balancer (ALB)
- Auto-scaling (CPU/memory based)
- Health checks
- CloudWatch logs
- IAM roles for task execution
- Secrets management (database credentials)

### 5. **S3 + CloudFront Module** (`modules/s3_cloudfront`)

Static frontend hosting:
- S3 bucket for Vue.js build
- CloudFront CDN distribution
- HTTPS enforcement
- Custom domain support (optional)
- Cache optimization
- OAI (Origin Access Identity) for security

---

## 🌍 Environments

### Development (`environments/dev`)

**Purpose:** Development and testing

**Configuration:**
- `db.t3.micro` (free tier eligible)
- 2 ECS tasks (minimal cost)
- No Multi-AZ RDS
- 3-day backup retention
- Public ALB endpoint

**Monthly Cost:** ~$50-100

---

### Staging (`environments/staging`)

**Purpose:** Pre-production testing

**Configuration:**
- `db.t3.small`
- 2-4 ECS tasks
- No Multi-AZ RDS
- 5-day backup retention
- Custom domain (optional)

**Monthly Cost:** ~$150-250

---

### Production (`environments/prod`)

**Purpose:** Live production environment

**Configuration:**
- `db.t3.medium` or larger
- 4+ ECS tasks (auto-scaling 4-20)
- Multi-AZ RDS (high availability)
- 7-day backup retention
- Performance Insights enabled
- Deletion protection enabled
- Custom domain with HTTPS
- WAF (Web Application Firewall)

**Monthly Cost:** ~$500-1000

---

## 💰 Cost Estimation

### Monthly AWS Costs (Development Environment):

| Service | Configuration | Monthly Cost |
|---------|--------------|--------------|
| **VPC** | NAT Gateways (3) | $32.40 |
| **RDS PostgreSQL** | db.t3.micro, 20GB | $14.00 |
| **ECS Fargate** | 2 tasks (0.5 vCPU, 1GB) | $25.00 |
| **ALB** | Application Load Balancer | $16.00 |
| **S3** | Frontend hosting (<5GB) | $0.50 |
| **CloudFront** | CDN (100GB transfer) | $10.00 |
| **CloudWatch** | Logs & Monitoring | $5.00 |
| **ECR** | Docker image storage | $2.00 |
| **Total** | | **~$105/month** |

### Cost Optimization Tips:

1. **Use NAT Gateway alternatives:**
   - VPC Endpoints (S3, ECR) - saves $32/month
   - Single NAT Gateway instead of 3 - saves $22/month

2. **ECS Auto-scaling:**
   - Scale down to 1 task during off-hours
   - Use spot instances (not available for Fargate, but possible with EC2 launch type)

3. **RDS Reserved Instances:**
   - 1-year commitment: 40% savings
   - 3-year commitment: 60% savings

4. **S3 Intelligent Tiering:**
   - Automatically moves data to cheaper storage tiers

5. **CloudFront Free Tier:**
   - 1TB data transfer/month free for first 12 months

---

## 🔒 Security Best Practices

### 1. **Network Isolation**

✅ Database in private subnets (no internet access)
✅ ECS tasks in private subnets (access via NAT)
✅ ALB in public subnets only
✅ Security groups with least privilege

### 2. **Encryption**

✅ RDS storage encrypted (AES-256)
✅ S3 bucket encryption
✅ HTTPS only (CloudFront, ALB)
✅ Secrets stored in AWS Secrets Manager

### 3. **Access Control**

✅ IAM roles (no hardcoded credentials)
✅ VPC Flow Logs for monitoring
✅ CloudWatch alarms for anomalies
✅ Database credentials rotation (implement with Secrets Manager)

### 4. **Compliance**

✅ Automated backups (7 days retention)
✅ Multi-AZ deployment (production)
✅ Deletion protection (production)
✅ Audit logging (CloudWatch, VPC Flow Logs)

---

## 🛠️ Common Commands

```bash
# Initialize Terraform
terraform init

# Format code
terraform fmt -recursive

# Validate configuration
terraform validate

# Plan changes
terraform plan

# Apply changes
terraform apply

# Destroy infrastructure
terraform destroy

# Show current state
terraform show

# List resources
terraform state list

# Get specific output
terraform output api_endpoint

# Import existing resource
terraform import aws_s3_bucket.frontend datamigrate-ai-dev-frontend

# Refresh state
terraform refresh

# Generate dependency graph
terraform graph | dot -Tpng > graph.png
```

---

## 🐛 Troubleshooting

### Issue: "Error creating VPC: VpcLimitExceeded"

**Solution:** You've hit the AWS VPC limit (5 per region by default). Delete unused VPCs or request a limit increase.

```bash
aws ec2 describe-vpcs --region us-east-1
```

---

### Issue: "Error creating DB Instance: InvalidDBInstanceState"

**Solution:** Snapshot restoration failed. Check if snapshot exists and is in `available` state.

```bash
aws rds describe-db-snapshots --region us-east-1
```

---

### Issue: "Timeout while waiting for load balancer to become ready"

**Solution:** Check security groups, target groups, and health checks.

```bash
aws elbv2 describe-target-health --target-group-arn <arn>
```

---

### Issue: "ECS task keeps restarting"

**Solution:** Check CloudWatch logs for container errors.

```bash
aws logs tail /ecs/datamigrate-ai-dev-fastapi --follow
```

---

### Issue: "Terraform state is locked"

**Solution:** If a previous `terraform apply` was interrupted, the state is locked in DynamoDB.

```bash
# Check lock
aws dynamodb get-item \
  --table-name datamigrate-ai-terraform-locks \
  --key '{"LockID":{"S":"datamigrate-ai-terraform-state/terraform.tfstate"}}' \
  --region us-east-1

# Force unlock (use with caution!)
terraform force-unlock <lock-id>
```

---

## 📚 Additional Resources

- **Terraform AWS Provider:** https://registry.terraform.io/providers/hashicorp/aws/latest/docs
- **AWS ECS Best Practices:** https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/
- **RDS PostgreSQL:** https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_PostgreSQL.html
- **CloudFront Documentation:** https://docs.aws.amazon.com/cloudfront/

---

## 🤝 Contributing

For changes to infrastructure:

1. Create a new branch
2. Make changes to Terraform files
3. Run `terraform fmt` and `terraform validate`
4. Test in `dev` environment first
5. Create PR with plan output
6. Get approval before applying to `prod`

---

## 📝 License & Ownership

**Property of:** OKO Investments
**Author:** Alexander Garcia Angus
**Copyright:** © 2025 OKO Investments. All rights reserved.

This infrastructure code is proprietary and confidential.
