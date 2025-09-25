# Slack Strands Agentic Bot

A Slack bot powered by AWS Bedrock and the Strands agentic framework, with MCP (Model Context Protocol) integrations for PagerDuty, GitHub, and Atlassian services.

## Overview

This project deploys a Slack bot that can:
- Process messages through AWS Bedrock models (Claude Sonnet 4 by default)
- Use AWS Bedrock Knowledge Base for enhanced responses
- Apply AWS Bedrock Guardrails for content filtering
- Integrate with external services via MCP protocols:
  - PagerDuty for incident management
  - GitHub for repository interactions
  - Atlassian for Jira/Confluence integration
- Run as containerized AWS Lambda functions with ARM64 architecture

## Architecture

The system consists of two AWS Lambda functions:
- **Receiver Lambda**: Handles incoming Slack events and triggers the worker
- **Worker Lambda**: Processes requests using Bedrock models and MCP integrations

## Prerequisites

Before deploying, you must create an AWS Secrets Manager secret containing your Slack bot credentials. The secret should include:
```json
{
  "slack_bot_token": "xoxb-your-bot-token",
  "slack_signing_secret": "your-signing-secret"
}
```

Additional credentials may be required for MCP integrations:
- PagerDuty: API token
- GitHub: Personal access token
- Atlassian: API credentials

## Configuration

### terraform.tfvars Variables

All configuration is managed through the `terraform.tfvars` file. Here are the available variables and their impact:

#### Bot Configuration
- **`bot_name`** (required): The name of your bot (e.g., "VeraResearch")
  - *Impact*: Used in AWS resource naming and bot identification

- **`secret_name`** (required): Name of the AWS Secrets Manager secret containing Slack credentials
  - *Impact*: Must exist before deployment; grants Lambda access to this secret

- **`model_id`** (default: "anthropic.claude-sonnet-4-20250514-v1"): Bedrock model to use
  - *Impact*: Determines the AI model powering your bot responses

- **`debug_enabled`** (default: ""): Enable debug logging in Lambda functions
  - *Impact*: When set to "True", enables verbose logging for troubleshooting
  - *Values*: "True" or leave empty for normal logging

#### AWS Bedrock Features
- **`knowledge_base_id`** (default: ""): AWS Bedrock Knowledge Base ID
  - *Impact*: When provided, enables RAG (Retrieval Augmented Generation) for enhanced responses
  - *Leave empty*: To disable knowledge base integration

- **`guardrails_id`** (default: ""): AWS Bedrock Guardrails ID
  - *Impact*: When provided, applies content filtering and safety checks to responses
  - *Leave empty*: To disable guardrails

#### MCP (Model Context Protocol) Integrations

- **`enable_pagerduty_mcp`** (default: false): Enable PagerDuty integration
  - *Impact*: When true, allows bot to interact with PagerDuty incidents
  - *Requires*: PagerDuty API token in secrets

- **`pagerduty_api_url`** (default: "https://api.pagerduty.com"): PagerDuty API endpoint
  - *Impact*: Defines the PagerDuty API base URL for integration

- **`enable_github_mcp`** (default: false): Enable GitHub integration
  - *Impact*: When true, allows bot to interact with GitHub repositories
  - *Requires*: GitHub personal access token in secrets

- **`enable_atlassian_mcp`** (default: false): Enable Atlassian integration
  - *Impact*: When true, allows bot to interact with Jira/Confluence
  - *Requires*: Atlassian API credentials in secrets

### Example Configuration

```hcl
# Bot Configuration
bot_name    = "VeraResearch"
secret_name = "VeraResearchSecret"
model_id    = "anthropic.claude-sonnet-4-20250514-v1"
debug_enabled = "True"

# AWS Bedrock Features (optional)
knowledge_base_id = "KB123456"  # Leave empty to disable
guardrails_id     = "GR789012"  # Leave empty to disable

# MCP Integrations
pagerduty_api_url    = "https://api.pagerduty.com"
enable_pagerduty_mcp = true
enable_github_mcp    = false
enable_atlassian_mcp = false
```

## Deployment

1. **Create the Secrets Manager secret**:
   ```bash
   aws secretsmanager create-secret --name "VeraResearchSecret" \
     --description "Slack bot credentials" \
     --secret-string '{"slack_bot_token":"xoxb-your-token","slack_signing_secret":"your-secret"}'
   ```

2. **Configure terraform.tfvars** with your desired settings

3. **Deploy with Terraform**:
   ```bash
   terraform init
   terraform plan
   terraform apply
   ```

4. **Configure your Slack app** to use the receiver Lambda URL output by Terraform

## Outputs

After deployment, Terraform provides:
- **`receiver_lambda_arn_for_slack`**: The Function URL to configure as your Slack app's request URL

## Resource Management

### ECR Repository
- Automatically creates an ECR repository for the worker container
- Includes lifecycle policies:
  - Keeps only the latest 10 tagged images
  - Deletes untagged images after 1 day

### Lambda Functions
- **Receiver**: ARM64, 128MB memory, 10s timeout, Python 3.12
- **Worker**: ARM64, 1024MB memory, 900s timeout, containerized

### IAM Permissions
The system creates minimal IAM roles with permissions for:
- Lambda execution
- CloudWatch logging
- Secrets Manager access
- Bedrock model invocation (all regions)
- Bedrock Guardrails (us-west-2)
- Bedrock Knowledge Base (us-west-2)

## MCP Server Integration

The bot includes a containerized PagerDuty MCP server that allows structured interaction with PagerDuty services. Additional MCP servers can be added by modifying the Dockerfile and enabling the corresponding flags.

## Troubleshooting

1. **Lambda timeout issues**: Increase the worker timeout in `lambda_worker.tf`
2. **Memory issues**: Increase the worker memory size
3. **Debug logging**: Set `debug_enabled = "True"` in terraform.tfvars
4. **Secret access issues**: Ensure the secret exists and contains the required keys
5. **ECR issues**: Ensure Docker is running and AWS CLI is configured

## Development

The project structure:
```
├── main.tf              # Root Terraform configuration
├── variables.tf         # Variable definitions
├── terraform.tfvars     # Configuration values
├── ecr.tf              # ECR repository setup
├── data.tf             # Data sources
└── lambda/             # Lambda function code
    ├── main.tf         # Lambda module configuration
    ├── Dockerfile      # Container image definition
    ├── requirements.txt # Python dependencies
    └── src/           # Python source code
```