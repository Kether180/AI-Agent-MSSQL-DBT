# ECR (Elastic Container Registry) Module
# Author: Alexander Garcia Angus
# Property of: OKO Investments

# ECR Repository for FastAPI Backend
resource "aws_ecr_repository" "fastapi" {
  name                 = "${var.project_name}/${var.environment}/fastapi"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = merge(
    var.tags,
    {
      Name        = "${var.project_name}-${var.environment}-fastapi"
      Application = "FastAPI Backend"
    }
  )
}

# ECR Repository for LangGraph Agents
resource "aws_ecr_repository" "langgraph_agents" {
  name                 = "${var.project_name}/${var.environment}/langgraph-agents"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = merge(
    var.tags,
    {
      Name        = "${var.project_name}-${var.environment}-langgraph-agents"
      Application = "LangGraph Multi-Agent System"
    }
  )
}

# ECR Repository for Celery Workers
resource "aws_ecr_repository" "celery_worker" {
  name                 = "${var.project_name}/${var.environment}/celery-worker"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = merge(
    var.tags,
    {
      Name        = "${var.project_name}-${var.environment}-celery-worker"
      Application = "Celery Background Tasks"
    }
  )
}

# Lifecycle Policy - Keep last 10 images
resource "aws_ecr_lifecycle_policy" "fastapi" {
  repository = aws_ecr_repository.fastapi.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 10 images"
      selection = {
        tagStatus     = "any"
        countType     = "imageCountMoreThan"
        countNumber   = 10
      }
      action = {
        type = "expire"
      }
    }]
  })
}

resource "aws_ecr_lifecycle_policy" "langgraph_agents" {
  repository = aws_ecr_repository.langgraph_agents.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 10 images"
      selection = {
        tagStatus     = "any"
        countType     = "imageCountMoreThan"
        countNumber   = 10
      }
      action = {
        type = "expire"
      }
    }]
  })
}

resource "aws_ecr_lifecycle_policy" "celery_worker" {
  repository = aws_ecr_repository.celery_worker.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 10 images"
      selection = {
        tagStatus     = "any"
        countType     = "imageCountMoreThan"
        countNumber   = 10
      }
      action = {
        type = "expire"
      }
    }]
  })
}

# ECR Repository Policy (allow pull from EKS nodes)
data "aws_iam_policy_document" "ecr_policy" {
  statement {
    sid    = "AllowPull"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }

    actions = [
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
      "ecr:BatchCheckLayerAvailability"
    ]
  }
}

resource "aws_ecr_repository_policy" "fastapi" {
  repository = aws_ecr_repository.fastapi.name
  policy     = data.aws_iam_policy_document.ecr_policy.json
}

resource "aws_ecr_repository_policy" "langgraph_agents" {
  repository = aws_ecr_repository.langgraph_agents.name
  policy     = data.aws_iam_policy_document.ecr_policy.json
}

resource "aws_ecr_repository_policy" "celery_worker" {
  repository = aws_ecr_repository.celery_worker.name
  policy     = data.aws_iam_policy_document.ecr_policy.json
}
