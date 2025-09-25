# Bot stuff
variable "debug_enabled" {
  description = "Enable debug mode for Lambda function"
  type        = string
  default     = ""
}
variable "knowledge_base_id" {
  description = "Knowledge base ID for the Lambda function"
  type        = string
  default     = ""
}
variable "guardrails_id" {
  description = "Guardrails ID for the Lambda function"
  type        = string
  default     = ""
}
variable "secret_name" {
  description = "Name of the secret in AWS Secrets Manager"
  type        = string
}
variable "model_id" {
  description = "Model ID for the Lambda function"
  type        = string
  default     = "anthropic.claude-sonnet-4-20250514-v1"
}
variable "bot_name" {
  description = "Name of the bot"
  type        = string
}
variable "pagerduty_api_url" {
  description = "PagerDuty API URL for MCP integration"
  type        = string
}

# MCP
variable "enable_pagerduty_mcp" {
  description = "Enable PagerDuty MCP integration"
  type        = bool
}
variable "enable_github_mcp" {
  description = "Enable GitHub MCP integration"
  type        = bool
}
variable "enable_atlassian_mcp" {
  description = "Enable Atlassian MCP integration"
  type        = bool
}