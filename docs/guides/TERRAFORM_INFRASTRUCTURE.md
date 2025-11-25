# Terraform Infrastructure as Code Guide

**Author:** Alexander Garcia Angus
**Property of:** OKO Investments

## Overview

DataMigrate AI uses **Terraform** to manage all AWS infrastructure as code. This provides version control, reproducibility, and team collaboration for infrastructure changes.

## Why Terraform?

### ✅ Benefits:

1. **Infrastructure as Code (IaC)**
   - Infrastructure defined in version-controlled files
   - Track changes over time with Git
   - Review infrastructure changes like code reviews

2. **Reproducible Environments**
   - Identical dev, staging, and production environments
   - No configuration drift
   - Easy disaster recovery

3. **Multi-Cloud Support**
   - Works with AWS, Azure, GCP, and 100+ providers
   - Future flexibility for OKO Investments

4. **Team Collaboration**
   - State managed in S3 + DynamoDB
   - Prevent concurrent modifications (state locking)
   - Clear ownership and change history

5. **Cost Transparency**
   - See exactly what resources are deployed
   - Easy to tear down unused environments
   - Estimate costs before deployment

## Architecture Deployed

Terraform deploys a **production-ready, scalable architecture**:

```
┌─────────────────────────────────────────────────────┐
│  CloudFront CDN (Vue.js Frontend)                   │
│  ↓                                                   │
│  S3 Static Website                                  │
└─────────────────────────────────────────────────────┘
                        ↓ API Calls
┌─────────────────────────────────────────────────────┐
│  Application Load Balancer (HTTPS)                  │
│  ↓                                                   │
│  ECS Fargate Cluster (FastAPI Backend)              │
│    - Auto-scaling (2-20 tasks)                      │
│    - Health checks                                  │
│    - CloudWatch logs                                │
│  ↓                                                   │
│  RDS PostgreSQL 15                                  │
│    - Multi-AZ (production)                          │
│    - Encrypted storage                              │
│    - Automated backups (7 days)                     │
└─────────────────────────────────────────────────────┘
```

### Network Architecture:

- **VPC** with 3 availability zones
- **Public Subnets**: ALB, NAT Gateways
- **Private Subnets**: ECS tasks (FastAPI containers)
- **Database Subnets**: RDS (isolated, no internet)
- **Security Groups**: Least privilege access control

## Quick Start

### 1. Prerequisites

```bash
# Install Terraform
brew install terraform  # macOS
choco install terraform # Windows

# Install AWS CLI
brew install awscli     # macOS
choco install awscli    # Windows

# Configure AWS credentials
aws configure
```

### 2. Deploy Infrastructure

```bash
cd terraform

# Create environment variables
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values

# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Deploy
terraform apply
```

**Time to deploy:** 15-20 minutes

### 3. Get Endpoints

```bash
terraform output

# Outputs:
# api_endpoint = "https://api.datamigrate.ai"
# frontend_url = "https://app.datamigrate.ai"
# database_endpoint = "db.abc123.us-east-1.rds.amazonaws.com"
```

## Modules

Terraform code is organized into **reusable modules**:

| Module | Purpose | Resources Created |
|--------|---------|-------------------|
| **vpc** | Network infrastructure | VPC, Subnets, NAT Gateways, Route Tables |
| **security** | Security groups | ALB SG, ECS SG, RDS SG |
| **rds** | PostgreSQL database | RDS instance, Parameter group, Backups, Alarms |
| **ecs** | FastAPI backend | ECS cluster, Service, Tasks, ALB, Auto-scaling |
| **s3_cloudfront** | Vue.js frontend | S3 bucket, CloudFront CDN, SSL certificate |

## Environments

### Development
- **Cost:** ~$50-100/month
- **RDS:** db.t3.micro (free tier eligible)
- **ECS:** 2 tasks (0.5 vCPU, 1GB RAM each)
- **Backups:** 3 days retention

### Staging
- **Cost:** ~$150-250/month
- **RDS:** db.t3.small
- **ECS:** 2-4 tasks with auto-scaling
- **Backups:** 5 days retention

### Production
- **Cost:** ~$500-1000/month
- **RDS:** db.t3.medium+ with Multi-AZ
- **ECS:** 4-20 tasks with auto-scaling
- **Backups:** 7 days retention
- **Features:** Performance Insights, Deletion Protection, WAF

## Cost Breakdown (Development)

| Service | Monthly Cost |
|---------|--------------|
| NAT Gateways (3) | $32.40 |
| RDS PostgreSQL | $14.00 |
| ECS Fargate | $25.00 |
| Application Load Balancer | $16.00 |
| S3 + CloudFront | $10.50 |
| CloudWatch Logs | $5.00 |
| **Total** | **~$105/month** |

### Cost Optimization:
- Use VPC Endpoints (saves $32/month on NAT)
- RDS Reserved Instances (40-60% savings)
- Scale down ECS tasks during off-hours
- S3 Intelligent Tiering

## Security Features

✅ **Network Isolation**
- Database in private subnets (no internet access)
- ECS tasks in private subnets
- ALB in public subnets only

✅ **Encryption**
- RDS storage encrypted (AES-256)
- S3 bucket encryption
- HTTPS only (CloudFront, ALB)

✅ **Access Control**
- IAM roles (no hardcoded credentials)
- Security groups with least privilege
- VPC Flow Logs for monitoring

✅ **Compliance**
- Automated backups
- Multi-AZ deployment (production)
- Deletion protection
- Audit logging

## Common Commands

```bash
# Initialize (first time or after adding modules)
terraform init

# Preview changes
terraform plan

# Apply changes
terraform apply

# Destroy all resources
terraform destroy

# Show current state
terraform show

# Get specific output
terraform output api_endpoint

# Format code
terraform fmt -recursive

# Validate configuration
terraform validate
```

## Troubleshooting

### Terraform State is Locked

**Cause:** Previous `terraform apply` was interrupted.

**Solution:**
```bash
# Check lock in DynamoDB
aws dynamodb get-item \
  --table-name datamigrate-ai-terraform-locks \
  --key '{"LockID":{"S":"datamigrate-ai-terraform-state/terraform.tfstate"}}'

# Force unlock (use with caution!)
terraform force-unlock <lock-id>
```

### ECS Tasks Keep Restarting

**Solution:** Check CloudWatch logs:
```bash
aws logs tail /ecs/datamigrate-ai-dev-fastapi --follow
```

### RDS Connection Timeout

**Cause:** Security groups not configured correctly.

**Solution:** Verify ECS security group can access RDS:
```bash
aws ec2 describe-security-groups --group-ids <ecs-sg-id>
aws ec2 describe-security-groups --group-ids <rds-sg-id>
```

## Best Practices

### 1. **Never Commit Secrets**
- Use AWS Secrets Manager for database passwords
- Never put credentials in `terraform.tfvars`
- `.tfvars` files are gitignored

### 2. **Use Remote State**
- State stored in S3 (team collaboration)
- State locking with DynamoDB (prevent conflicts)
- Versioning enabled on S3 bucket

### 3. **Test in Dev First**
- Always apply changes to `dev` environment first
- Verify everything works before staging/prod
- Use `terraform plan` to preview changes

### 4. **Tag Everything**
- All resources tagged with Environment, Project, Owner
- Easy cost tracking and resource management
- Automated tagging via `default_tags`

### 5. **Use Modules**
- DRY principle (Don't Repeat Yourself)
- Reusable infrastructure components
- Easier to maintain and update

## Integration with DataMigrate AI

### Database Connection

Terraform outputs the RDS endpoint. Configure FastAPI to use it:

```bash
# Get database endpoint
export DB_HOST=$(terraform output -raw database_endpoint)

# Update FastAPI environment variables
DATABASE_URL=postgresql://admin:password@${DB_HOST}:5432/datamigrate_ai
```

### Frontend Deployment

After Terraform creates S3 + CloudFront:

```bash
# Build Vue.js app
cd frontend
npm run build

# Deploy to S3
aws s3 sync dist/ s3://$(terraform output -raw frontend_bucket) --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id $(terraform output -raw cloudfront_distribution_id) \
  --paths "/*"
```

### Backend Deployment

ECS automatically pulls from ECR:

```bash
# Build and push Docker image
docker build -t datamigrate-ai/fastapi:latest .
docker tag datamigrate-ai/fastapi:latest <ecr-repo-url>:latest
docker push <ecr-repo-url>:latest

# ECS will auto-deploy new image
aws ecs update-service \
  --cluster $(terraform output -raw ecs_cluster_name) \
  --service $(terraform output -raw ecs_service_name) \
  --force-new-deployment
```

## Next Steps

1. ✅ **Terraform infrastructure created**
2. ⏭️ **Build and push Docker image to ECR**
3. ⏭️ **Deploy infrastructure to AWS**
4. ⏭️ **Configure CI/CD pipeline (GitHub Actions)**
5. ⏭️ **Set up monitoring and alerts**
6. ⏭️ **Configure custom domain**

## Additional Resources

- **Terraform Documentation:** https://www.terraform.io/docs
- **AWS Provider Docs:** https://registry.terraform.io/providers/hashicorp/aws/latest/docs
- **Terraform Best Practices:** https://www.terraform-best-practices.com/
- **Project Terraform README:** [../terraform/README.md](../../terraform/README.md)

---

**For detailed Terraform setup instructions, see:** [terraform/README.md](../../terraform/README.md)
