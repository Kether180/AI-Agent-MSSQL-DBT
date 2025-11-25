# DataMigrate AI - Main Terraform Configuration
# Author: Alexander Garcia Angus
# Property of: OKO Investments

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }

  # S3 backend for state management (configure after initial setup)
  backend "s3" {
    bucket         = "datamigrate-ai-terraform-state"
    key            = "terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "datamigrate-ai-terraform-locks"
  }
}

# AWS Provider Configuration
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "DataMigrate AI"
      Owner       = "OKO Investments"
      ManagedBy   = "Terraform"
      Environment = var.environment
    }
  }
}

# Local Variables
locals {
  project_name = "datamigrate-ai"
  common_tags = {
    Application = "DataMigrate AI"
    Author      = "Alexander Garcia Angus"
    Company     = "OKO Investments"
  }
}

# VPC Module
module "vpc" {
  source = "./modules/vpc"

  project_name       = local.project_name
  environment        = var.environment
  vpc_cidr           = var.vpc_cidr
  availability_zones = var.availability_zones

  tags = local.common_tags
}

# Security Module
module "security" {
  source = "./modules/security"

  project_name = local.project_name
  environment  = var.environment
  vpc_id       = module.vpc.vpc_id

  tags = local.common_tags
}

# RDS PostgreSQL Database
module "rds" {
  source = "./modules/rds"

  project_name          = local.project_name
  environment           = var.environment
  vpc_id                = module.vpc.vpc_id
  database_subnets      = module.vpc.database_subnets
  db_security_group_id  = module.security.db_security_group_id

  db_instance_class     = var.db_instance_class
  db_name               = var.db_name
  db_username           = var.db_username
  db_password           = var.db_password

  tags = local.common_tags
}

# ECS Fargate for FastAPI Backend
module "ecs" {
  source = "./modules/ecs"

  project_name           = local.project_name
  environment            = var.environment
  vpc_id                 = module.vpc.vpc_id
  private_subnets        = module.vpc.private_subnets
  public_subnets         = module.vpc.public_subnets
  ecs_security_group_id  = module.security.ecs_security_group_id
  alb_security_group_id  = module.security.alb_security_group_id

  # Database connection
  db_endpoint            = module.rds.db_endpoint
  db_name                = var.db_name
  db_username            = var.db_username
  db_password            = var.db_password

  # Docker image
  fastapi_image          = var.fastapi_image
  fastapi_cpu            = var.fastapi_cpu
  fastapi_memory         = var.fastapi_memory
  desired_count          = var.ecs_desired_count

  tags = local.common_tags
}

# S3 + CloudFront for Vue.js Frontend
module "s3_cloudfront" {
  source = "./modules/s3_cloudfront"

  project_name    = local.project_name
  environment     = var.environment
  domain_name     = var.domain_name
  certificate_arn = var.certificate_arn

  # Backend API endpoint
  api_endpoint    = module.ecs.alb_dns_name

  tags = local.common_tags
}
