# Bot stuff
knowledge_base_id = "" # Leave blank to indicate don't use a knowledge base
guardrails_id     = "" # Leave blank to indicate don't use guardrails
debug_enabled     = "True"
model_id          = "anthropic.claude-sonnet-4-20250514-v1"
bot_name          = "VeraResearch"

# Create this secret before deploying terraform for it to succeed
secret_name = "VeraResearchSecret"

# MCP stuff
pagerduty_api_url    = "https://api.pagerduty.com" # Replace with your PagerDuty API URL
enable_pagerduty_mcp = false                       # Set to true to enable PagerDuty MCP integration
enable_github_mcp    = false                       # Set to true to enable GitHub MCP integration
enable_atlassian_mcp = false                       # Set to true to enable Atlassian MCP integration