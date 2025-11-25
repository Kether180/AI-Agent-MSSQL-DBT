# DataMigrate AI - Terraform Outputs
# Author: Alexander Garcia Angus
# Property of: OKO Investments

output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "database_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = module.rds.db_endpoint
  sensitive   = true
}

output "api_endpoint" {
  description = "FastAPI backend endpoint (ALB DNS)"
  value       = module.ecs.alb_dns_name
}

output "api_url" {
  description = "Full API URL"
  value       = "https://${module.ecs.alb_dns_name}"
}

output "frontend_url" {
  description = "Frontend CloudFront URL"
  value       = module.s3_cloudfront.cloudfront_domain_name
}

output "frontend_bucket" {
  description = "S3 bucket for frontend"
  value       = module.s3_cloudfront.s3_bucket_name
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = module.ecs.cluster_name
}

output "ecs_service_name" {
  description = "ECS service name"
  value       = module.ecs.service_name
}

output "deployment_summary" {
  description = "Summary of deployed resources"
  value = {
    environment     = var.environment
    region          = var.aws_region
    vpc_id          = module.vpc.vpc_id
    api_endpoint    = module.ecs.alb_dns_name
    frontend_url    = module.s3_cloudfront.cloudfront_domain_name
    database        = "PostgreSQL on RDS"
    backend         = "FastAPI on ECS Fargate"
    frontend        = "Vue.js on S3 + CloudFront"
  }
}
