# Define Terraform provider
terraform {
  required_version = "~> 1.7"

  required_providers {
    aws = {
      version = "~> 5.77"
      source  = "hashicorp/aws"
    }
  }
}

# Download AWS provider
provider "aws" {
  region = "us-east-1"
}

# Provider in AI region
provider "aws" {
  alias  = "west2"
  region = "us-west-2"
}

# Build lambda
module "lambda" {
  source = "./lambda"

  # Pass ECR info for container builds
  ecr_repository_url = aws_ecr_repository.worker_container.repository_url
  ecr_name           = aws_ecr_repository.worker_container.name

  # Pass variables
  debug_enabled     = var.debug_enabled
  knowledge_base_id = var.knowledge_base_id
  guardrails_id     = var.guardrails_id
  secret_name       = var.secret_name
  bot_name          = var.bot_name
  model_id          = var.model_id

  # MCP
  pagerduty_api_url    = var.pagerduty_api_url
  enable_pagerduty_mcp = var.enable_pagerduty_mcp
  enable_github_mcp    = var.enable_github_mcp
  enable_atlassian_mcp = var.enable_atlassian_mcp

  # Pass providers
  providers = {
    aws       = aws
    aws.west2 = aws.west2
  }
}

output "receiver_lambda_arn_for_slack" {
  value = module.lambda.Receiver_Slack_Trigger_FunctionUrl
}