# Bot stuff
knowledge_base_id = "" # Leave blank to indicate don't use a knowledge base
guardrails_id     = "" # Leave blank to indicate don't use guardrails
debug_enabled     = "True"
model_id          = "us.anthropic.claude-sonnet-4-20250514-v1:0"
bot_name          = "VeraResearch"

# Create this secret before deploying terraform for it to succeed
secret_name = "VeraResearchSecret"

# MCP stuff
pagerduty_api_url    = "https://api.pagerduty.com" # Replace with your PagerDuty API URL
enable_pagerduty_mcp = false                       # Set to true to enable PagerDuty MCP integration, requires PAGERDUTY_API_KEY that is valid PagerDuty token in Secret. 
enable_github_mcp    = false                       # Set to true to enable GitHub MCP integration, requires GITHUB_TOKEN in Secret that is PAT with read access.
enable_atlassian_mcp = false                       # Set to true to enable Atlassian MCP integration, requires ATLASSIAN_CLIENT_ID and ATLASSIAN_REFRESH_TOKEN in Secret.