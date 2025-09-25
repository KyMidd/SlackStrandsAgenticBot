# ECR Repository for Lambda container images
resource "aws_ecr_repository" "worker_container" {
  name                 = "${lower(var.bot_name)}-slack-worker"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  lifecycle {
    prevent_destroy = false
  }

  tags = {
    Name = "${var.bot_name}SlackWorker"
  }
}

# ECR Lifecycle Policy to keep only the latest 10 images
resource "aws_ecr_lifecycle_policy" "worker_container_lifecycle" {
  repository = aws_ecr_repository.worker_container.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep only the latest 10 images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["latest"]
          countType     = "imageCountMoreThan"
          countNumber   = 10
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description  = "Delete untagged images older than 1 day"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 1
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# ECR Repository Policy to allow Lambda to pull images
resource "aws_ecr_repository_policy" "worker_container_policy" {
  repository = aws_ecr_repository.worker_container.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowLambdaPull"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = [
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:BatchCheckLayerAvailability"
        ]
      },
      {
        Sid    = "AllowAccountAccess"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action = [
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:BatchCheckLayerAvailability",
          "ecr:PutImage",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload",
          "ecr:GetAuthorizationToken"
        ]
      }
    ]
  })
}

# Output the ECR repository URL
output "ecr_repository_url" {
  value       = aws_ecr_repository.worker_container.repository_url
  description = "ECR repository URL for the worker container"
}