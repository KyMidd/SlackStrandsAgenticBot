# Agent execution functions
import os
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.tools.mcp.mcp_client import MCPClient
from strands.models import BedrockModel
from strands.types.tools import AgentTool
from worker_inputs import (
    model_id,
    guardrailIdentifier,
    guardrailTracing,
    guardrailVersion,
    token_budget,
    system_prompt,
    enable_pagerduty_mcp,
    enable_github_mcp,
    enable_atlassian_mcp,
    enable_azure_mcp,
    enable_aws_cli_mcp,
    pagerduty_api_url,
)


def execute_agent(secrets_json, conversation):
    """Execute agent with MCP clients - keeps clients open during execution"""

    # Set up MCP clients and collect tools (opens connections)
    # Ensure AWS region is set for retrieve tool (knowledge base is in us-west-2)
    bedrock_region = os.environ.get("BEDROCK_REGION", "us-west-2")
    os.environ["AWS_DEFAULT_REGION"] = bedrock_region
    os.environ["AWS_REGION"] = bedrock_region

    ###
    # MCP section
    ###

    # Initialize tools list and opened_clients dictionary
    tools = []
    opened_clients = {}

    # Built-in tools
    from strands_tools import calculator, current_time, retrieve

    tools.extend([calculator, current_time, retrieve])

    ##
    # GitHub MCP
    ##

    if enable_github_mcp:

        try:
            from worker_mcp_github import build_github_mcp_client

            # Build GitHub MCP client with only read-only tools
            github_mcp_client = build_github_mcp_client(
                secrets_json["GITHUB_TOKEN"], "read_only"
            )
            opened_clients["GitHub"] = github_mcp_client
            tools.append(github_mcp_client)
        except Exception as error:
            print(f"Error setting up GitHub MCP client: {str(error)}")

    ##
    # Atlassian MCP
    ##

    if enable_atlassian_mcp:
        try:
            from worker_mcp_atlassian import build_atlassian_mcp_client

            # Build Atlassian MCP client with only read-only tools
            atlassian_mcp_client = build_atlassian_mcp_client(
                secrets_json["ATLASSIAN_REFRESH_TOKEN"],
                secrets_json["ATLASSIAN_CLIENT_ID"],
                "read_only",
            )
            opened_clients["Atlassian"] = atlassian_mcp_client
            tools.append(atlassian_mcp_client)
        except Exception as error:
            print(f"Error setting up Atlassian MCP client: {str(error)}")

    ##
    # PagerDuty MCP
    ##

    if enable_pagerduty_mcp:

        try:
            from worker_mcp_pagerduty import build_pagerduty_mcp_client

            # Build PagerDuty MCP client with only read-only tools
            pagerduty_mcp_client = build_pagerduty_mcp_client(
                secrets_json["PAGERDUTY_API_KEY"],
                pagerduty_api_url,
                "read_only",
            )
            opened_clients["PagerDuty"] = pagerduty_mcp_client
            tools.append(pagerduty_mcp_client)
        except Exception as error:
            print(f"Error setting up PagerDuty MCP client: {str(error)}")

    ##
    # Azure MCP
    ##

    if enable_azure_mcp:
        try:
            from worker_mcp_azure import build_azure_mcp_client

            # Build Azure MCP client
            azure_mcp_client = build_azure_mcp_client(
                secrets_json["AZURE_TENANT_ID"],
                secrets_json["AZURE_CLIENT_ID"],
                secrets_json["AZURE_CLIENT_SECRET"],
            )
            opened_clients["Azure"] = azure_mcp_client
            tools.append(azure_mcp_client)
        except Exception as error:
            print(f"Error setting up Azure MCP client: {str(error)}")

    ##
    # AWS CLI MCP
    ##

    if enable_aws_cli_mcp:
        try:
            from worker_mcp_aws_cli import build_aws_cli_mcp_client

            # Build AWS CLI MCP client
            aws_cli_mcp_client = build_aws_cli_mcp_client(
                aws_region="us-east-1",
            )
            opened_clients["AWS_CLI"] = aws_cli_mcp_client
            tools.append(aws_cli_mcp_client)
        except Exception as error:
            print(f"Error setting up AWS CLI MCP client: {str(error)}")

    ###
    # Build agent
    ###

    # Create agent with all collected tools
    agent = Agent(
        model=BedrockModel(
            model_id=model_id,
            guardrail_id=guardrailIdentifier,
            guardrail_trace=guardrailTracing,
            guardrail_version=guardrailVersion,
            additional_request_fields={
                "thinking": {"type": "enabled", "budget_tokens": token_budget}
            },
        ),
        system_prompt=system_prompt,
        tools=tools,
    )

    # Execute agent while all MCP clients remain open
    response = agent(conversation)

    # Extract text from AgentResult object
    return str(response)
