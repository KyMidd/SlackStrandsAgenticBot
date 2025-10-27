# Slack Strands Agentic Bot

A Slack bot powered by AWS Bedrock and the Strands agentic framework, with MCP (Model Context Protocol) integrations for PagerDuty, GitHub, Atlassian, Azure, and AWS services.

## Overview

This project deploys a Slack bot that can:
- Process messages through AWS Bedrock models (Claude Sonnet 4 by default)
- Use AWS Bedrock Knowledge Base for enhanced responses
- Apply AWS Bedrock Guardrails for content filtering
- Integrate with external services via MCP protocols:
  - PagerDuty for incident management
  - GitHub for repository interactions
  - Atlassian for Jira/Confluence integration
  - Azure for cloud resource queries
  - AWS CLI for multi-account AWS resource queries
- Run as containerized AWS Lambda functions with ARM64 architecture

## Architecture

The system consists of two AWS Lambda functions:
- **Receiver Lambda**: Handles incoming Slack events and triggers the worker
- **Worker Lambda**: Processes requests using Bedrock models and MCP integrations

## Prerequisites

Before deploying, you must create an AWS Secrets Manager secret containing your Slack bot credentials and any MCP integration credentials. The secret should include:

### Required for all deployments:
```json
{
  "slack_bot_token": "xoxb-your-bot-token",
  "slack_signing_secret": "your-signing-secret"
}
```

### Additional credentials for MCP integrations:

**For PagerDuty MCP** (when `enable_pagerduty_mcp = true`):
```json
{
  "PAGERDUTY_API_KEY": "your-pagerduty-api-token"
}
```

**For GitHub MCP** (when `enable_github_mcp = true`):
```json
{
  "GITHUB_TOKEN": "ghp_your-personal-access-token"
}
```
*Note: GitHub token needs read access to repositories*

**For Atlassian MCP** (when `enable_atlassian_mcp = true`):
```json
{
  "ATLASSIAN_CLIENT_ID": "your-atlassian-client-id",
  "ATLASSIAN_REFRESH_TOKEN": "your-atlassian-refresh-token"
}
```

**For Azure MCP** (when `enable_azure_mcp = true`):
```json
{
  "AZURE_TENANT_ID": "your-azure-tenant-id",
  "AZURE_CLIENT_ID": "your-azure-client-id",
  "AZURE_CLIENT_SECRET": "your-azure-client-secret"
}
```
*Note: Azure MCP requires a service principal with appropriate permissions to query Azure resources*

**For AWS CLI MCP** (when `enable_aws_cli_mcp = true`):
- No secrets required - uses Lambda execution role IAM permissions
- Requires IAM permissions to assume roles in target AWS accounts
- Configure cross-account access via the `aws_config` file

### Complete secret example with all integrations:
```json
{
  "slack_bot_token": "xoxb-your-bot-token",
  "slack_signing_secret": "your-signing-secret",
  "PAGERDUTY_API_KEY": "your-pagerduty-api-token",
  "GITHUB_TOKEN": "ghp_your-personal-access-token",
  "ATLASSIAN_CLIENT_ID": "your-atlassian-client-id",
  "ATLASSIAN_REFRESH_TOKEN": "your-atlassian-refresh-token",
  "AZURE_TENANT_ID": "your-azure-tenant-id",
  "AZURE_CLIENT_ID": "your-azure-client-id",
  "AZURE_CLIENT_SECRET": "your-azure-client-secret"
}
```

## Configuration

### terraform.tfvars Variables

All configuration is managed through the `terraform.tfvars` file. Here are the available variables and their impact:

#### Bot Configuration
- **`bot_name`** (required): The name of your bot (e.g., "VeraResearch")
  - *Impact*: Used in AWS resource naming and bot identification

- **`secret_name`** (required): Name of the AWS Secrets Manager secret containing Slack credentials
  - *Impact*: Must exist before deployment; grants Lambda access to this secret

- **`model_id`** (default: "us.anthropic.claude-sonnet-4-20250514-v1:0"): Bedrock model to use
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
  - *Requires*: `PAGERDUTY_API_KEY` (valid PagerDuty token) in secrets

- **`pagerduty_api_url`** (default: "https://api.pagerduty.com"): PagerDuty API endpoint
  - *Impact*: Defines the PagerDuty API base URL for integration

- **`enable_github_mcp`** (default: false): Enable GitHub integration
  - *Impact*: When true, allows bot to interact with GitHub repositories
  - *Requires*: `GITHUB_TOKEN` (PAT with read access) in secrets

- **`enable_atlassian_mcp`** (default: false): Enable Atlassian integration
  - *Impact*: When true, allows bot to interact with Jira/Confluence
  - *Requires*: `ATLASSIAN_CLIENT_ID` and `ATLASSIAN_REFRESH_TOKEN` in secrets

- **`enable_azure_mcp`** (default: false): Enable Azure integration
  - *Impact*: When true, allows bot to query Azure resources (VMs, storage, subscriptions, etc.)
  - *Requires*: `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, and `AZURE_CLIENT_SECRET` in secrets

- **`enable_aws_cli_mcp`** (default: false): Enable AWS CLI integration
  - *Impact*: When true, allows bot to query AWS resources across multiple accounts
  - *Requires*: IAM permissions for the Lambda execution role to assume cross-account roles
  - *Configuration*: Edit `lambda/aws_config` file to define target AWS accounts and roles

### Example Configuration

```hcl
# Bot Configuration
bot_name    = "VeraResearch"
secret_name = "VeraResearchSecret"
model_id    = "us.anthropic.claude-sonnet-4-20250514-v1:0"
debug_enabled = "True"

# AWS Bedrock Features (optional)
knowledge_base_id = "KB123456"  # Leave empty to disable
guardrails_id     = "GR789012"  # Leave empty to disable

# MCP Integrations
pagerduty_api_url    = "https://api.pagerduty.com"
enable_pagerduty_mcp = true
enable_github_mcp    = false
enable_atlassian_mcp = false
enable_azure_mcp     = false
enable_aws_cli_mcp   = false
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

The bot includes multiple MCP servers for interacting with external services:

- **PagerDuty MCP**: Custom containerized server for incident management
- **GitHub MCP**: Official GitHub MCP server for repository interactions
- **Atlassian MCP**: Official Atlassian MCP server for Jira/Confluence integration
- **Azure MCP**: Official Azure MCP server for querying Azure resources
- **AWS CLI MCP**: AWS Labs MCP server for multi-account AWS resource queries

Each MCP server can be enabled/disabled independently via environment variables. The AWS CLI MCP supports cross-account access using profile-based role assumption - configure target accounts in the `lambda/aws_config` file.

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