output "fastapi_repository_url" {
  description = "FastAPI ECR repository URL"
  value       = aws_ecr_repository.fastapi.repository_url
}

output "fastapi_repository_arn" {
  description = "FastAPI ECR repository ARN"
  value       = aws_ecr_repository.fastapi.arn
}

output "langgraph_repository_url" {
  description = "LangGraph agents ECR repository URL"
  value       = aws_ecr_repository.langgraph_agents.repository_url
}

output "langgraph_repository_arn" {
  description = "LangGraph agents ECR repository ARN"
  value       = aws_ecr_repository.langgraph_agents.arn
}

output "celery_repository_url" {
  description = "Celery worker ECR repository URL"
  value       = aws_ecr_repository.celery_worker.repository_url
}

output "celery_repository_arn" {
  description = "Celery worker ECR repository ARN"
  value       = aws_ecr_repository.celery_worker.arn
}
