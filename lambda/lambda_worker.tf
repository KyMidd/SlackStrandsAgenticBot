###
# General data sources
###

# Current AWS account id
data "aws_caller_identity" "current" {}

# Region
data "aws_region" "current" {}


###
# Fetch secret ARNs from Secrets Manager
###

data "aws_secretsmanager_secret" "secrets" {
  name = var.secret_name
}


###
# IAM Role and policies for GitHubCop Trigger Lambda
###

data "aws_iam_policy_document" "worker_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "worker_role" {
  name               = "${local.lambda_function_name}WorkerRole"
  assume_role_policy = data.aws_iam_policy_document.worker_assume_role.json
}

resource "aws_iam_role_policy" "ReadSecret" {
  name = "ReadSecret"
  role = aws_iam_role.worker_role.id

  policy = jsonencode(
    {
      "Version" : "2012-10-17",
      "Statement" : [
        {
          "Effect" : "Allow",
          "Action" : [
            "secretsmanager:GetResourcePolicy",
            "secretsmanager:GetSecretValue",
            "secretsmanager:DescribeSecret",
            "secretsmanager:ListSecretVersionIds"
          ],
          "Resource" : [
            data.aws_secretsmanager_secret.secrets.arn,
          ]
        },
        {
          "Effect" : "Allow",
          "Action" : "secretsmanager:ListSecrets",
          "Resource" : "*"
        },
      ]
    }
  )
}

resource "aws_iam_role_policy" "Worker_Bedrock" {
  name = "Bedrock"
  role = aws_iam_role.worker_role.id

  policy = jsonencode(
    {
      "Version" : "2012-10-17",
      "Statement" : [
        # Grant permission to invoke bedrock models of any type in us-west-2 region
        {
          "Effect" : "Allow",
          "Action" : [
            "bedrock:InvokeModel",
            "bedrock:InvokeModelStream",
            "bedrock:InvokeModelWithResponseStream",
          ],
          # Both no longer specify region, since Bedrock wants cross-region access
          "Resource" : [
            "arn:aws:bedrock:us-east-1::foundation-model/*",
            "arn:aws:bedrock:us-east-2::foundation-model/*",
            "arn:aws:bedrock:us-west-1::foundation-model/*",
            "arn:aws:bedrock:us-west-2::foundation-model/*",
            "arn:aws:bedrock:us-east-1:${data.aws_caller_identity.current.account_id}:inference-profile/*",
            "arn:aws:bedrock:us-east-2:${data.aws_caller_identity.current.account_id}:inference-profile/*",
            "arn:aws:bedrock:us-west-1:${data.aws_caller_identity.current.account_id}:inference-profile/*",
            "arn:aws:bedrock:us-west-2:${data.aws_caller_identity.current.account_id}:inference-profile/*",
          ]
        },
        # Grant permission to invoke bedrock guardrails of any type in us-west-2 region
        {
          "Effect" : "Allow",
          "Action" : "bedrock:ApplyGuardrail",
          "Resource" : "arn:aws:bedrock:us-west-2:${data.aws_caller_identity.current.account_id}:guardrail/*"
        },
        # Grant permissions to use knowledge bases in us-west-2 region
        {
          "Effect" : "Allow",
          "Action" : [
            "bedrock:Retrieve",
            "bedrock:RetrieveAndGenerate",
          ],
          "Resource" : "arn:aws:bedrock:us-west-2:${data.aws_caller_identity.current.account_id}:knowledge-base/*"
        },
      ]
    }
  )
}

resource "aws_iam_role_policy" "DevOpsBotSlackTrigger_Cloudwatch" {
  name = "Cloudwatch"
  role = aws_iam_role.worker_role.id

  policy = jsonencode(
    {
      "Version" : "2012-10-17",
      "Statement" : [
        {
          "Effect" : "Allow",
          "Action" : "logs:CreateLogGroup",
          "Resource" : "arn:aws:logs:us-east-1:${data.aws_caller_identity.current.id}:*"
        },
        {
          "Effect" : "Allow",
          "Action" : [
            "logs:CreateLogStream",
            "logs:PutLogEvents"
          ],
          "Resource" : [
            "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.id}:log-group:/aws/lambda/${local.lambda_function_name}Worker:*"
          ]
        }
      ]
    }
  )
}

###
# Create lambda layers
###

# Build and push Docker image using null_resource
resource "null_resource" "build_and_push_image" {
  triggers = {
    dockerfile_hash   = filesha256("${path.module}/Dockerfile")
    requirements_hash = filesha256("${path.module}/requirements.txt")
    src_files_hash    = sha256(join("", [for f in fileset("${path.module}/src", "*.py") : filesha256("${path.module}/src/${f}")]))
  }

  provisioner "local-exec" {
    command     = <<EOF
      # Get the login token for ECR
      aws ecr get-login-password --region ${data.aws_region.current.name} | docker login --username AWS --password-stdin ${var.ecr_repository_url}

      # Build the Docker image for ARM64
      docker build --platform linux/arm64 -t ${var.ecr_repository_url}:latest .

      # Push the image to ECR
      docker push ${var.ecr_repository_url}:latest
    EOF
    working_dir = path.module
  }

}

# Data source to get the pushed image URI
data "aws_ecr_image" "worker_container_image" {
  repository_name = var.ecr_name
  image_tag       = "latest"

  depends_on = [null_resource.build_and_push_image]
}

# Lambda function using container image
resource "aws_lambda_function" "worker" {
  function_name = "${local.lambda_function_name}Worker"
  role          = aws_iam_role.worker_role.arn
  package_type  = "Image"
  image_uri     = "${var.ecr_repository_url}@${data.aws_ecr_image.worker_container_image.image_digest}"

  timeout       = 900
  memory_size   = 1024
  architectures = ["arm64"]
  publish       = true

  environment {
    variables = {
      DEBUG_ENABLED     = var.debug_enabled
      KNOWLEDGE_BASE_ID = var.knowledge_base_id
      GUARDRAILS_ID     = var.guardrails_id
      BEDROCK_REGION    = "us-west-2"
      SECRET_NAME       = var.secret_name
      MODEL_ID          = var.model_id
      BOT_NAME          = var.bot_name

      # MCP
      ENABLE_PAGERDUTY_MCP = var.enable_pagerduty_mcp
      PAGERDUTY_API_URL    = var.pagerduty_api_url
      ENABLE_GITHUB_MCP    = var.enable_github_mcp
      ENABLE_ATLASSIAN_MCP = var.enable_atlassian_mcp
    }
  }

  depends_on = [
    null_resource.build_and_push_image,
    data.aws_ecr_image.worker_container_image
  ]
}

# Output the Lambda function ARN
output "worker_function_arn" {
  value = aws_lambda_function.worker.arn
}