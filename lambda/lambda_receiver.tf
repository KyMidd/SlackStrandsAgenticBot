###
# IAM Role and policies for Message Receiver Lambda
###

data "aws_iam_policy_document" "receiver_assume_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "receiver_role" {
  name               = "${local.lambda_function_name}ReceiverRole"
  assume_role_policy = data.aws_iam_policy_document.receiver_assume_role.json
}

resource "aws_iam_role_policy" "lambda" {
  name = "InvokeLambda"
  role = aws_iam_role.receiver_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction",
          "lambda:InvokeAsync"
        ]
        Resource = [aws_lambda_function.worker.arn]
      }
    ]
  })
}

resource "aws_iam_role_policy" "cloudwatch" {
  name = "Cloudwatch"
  role = aws_iam_role.receiver_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "logs:CreateLogGroup"
        Resource = "arn:aws:logs:us-east-1:${data.aws_caller_identity.current.id}:*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = [
          "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.id}:log-group:/aws/lambda/${local.lambda_function_name}Receiver:*"
        ]
      }
    ]
  })
}

###
# Build receiver lambda
###

data "archive_file" "receiver_lambda" {
  type        = "zip"
  source_file = "${path.module}/src/receiver.py"
  output_path = "${path.module}/receiver.zip"
}

resource "aws_lambda_function" "receiver" {
  filename      = "${path.module}/receiver.zip"
  function_name = "${local.lambda_function_name}Receiver"
  role          = aws_iam_role.receiver_role.arn
  handler       = "receiver.lambda_handler"
  timeout       = 10
  memory_size   = 128
  runtime       = "python3.12"
  architectures = ["arm64"]

  source_code_hash = data.archive_file.receiver_lambda.output_base64sha256

  environment {
    variables = {
      PROCESSOR_FUNCTION_NAME = aws_lambda_function.worker.function_name
      BOT_NAME                = var.bot_name
    }
  }
}

# Publish alias of new version
resource "aws_lambda_alias" "receiver_alias" {
  name             = "Newest"
  function_name    = aws_lambda_function.receiver.arn
  function_version = aws_lambda_function.receiver.version

  # Add ignore for routing_configuration
  lifecycle {
    ignore_changes = [
      routing_config, # This sometimes has a race condition, so ignore changes to it
    ]
  }
}

# Point lambda function url at new version
resource "aws_lambda_function_url" "Receiver_Slack_Trigger_FunctionUrl" {
  function_name      = aws_lambda_function.receiver.function_name
  qualifier          = aws_lambda_alias.receiver_alias.name
  authorization_type = "NONE"
}

# Print the URL we can use to trigger the bot
output "Receiver_Slack_Trigger_FunctionUrl" {
  value = aws_lambda_function_url.Receiver_Slack_Trigger_FunctionUrl.function_url
}