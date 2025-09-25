# Agent execution functions
import os
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.tools.mcp.mcp_client import MCPClient
from strands.models import BedrockModel
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

            ### Build GitHub MCP client with only read-only tools
            github_mcp_client, github_tools = build_github_mcp_client(
                secrets_json["GITHUB_TOKEN"], "read_only"  # Only build read-only tools
            )
            # Append github to opened clients
            opened_clients["GitHub"] = github_mcp_client
            # Extend tools list with provided github tools
            tools.extend(github_tools)
        except Exception as e:
            print(f"Error setting up GitHub MCP client: {str(e)}")

    ##
    # Atlassian MCP
    ##

    if enable_atlassian_mcp:
        try:
            from worker_mcp_atlassian import build_atlassian_mcp_client

            ### Build Atlassian MCP client with only read-only tools (if credentials available)
            atlassian_mcp_client, atlassian_tools = build_atlassian_mcp_client(
                secrets_json["ATLASSIAN_REFRESH_TOKEN"],
                secrets_json["ATLASSIAN_CLIENT_ID"],
                "read_only",  # Only build read-only tools
            )
            # Append atlassian to opened clients
            opened_clients["Atlassian"] = atlassian_mcp_client
            # Extend tools list with provided atlassian tools
            tools.extend(atlassian_tools)
        except Exception as e:
            print(f"Error setting up Atlassian MCP client: {str(e)}")

    ##
    # PagerDuty MCP
    ##

    if enable_pagerduty_mcp:
        
        try:
            from worker_mcp_pagerduty import build_pagerduty_mcp_client

            ### Build PagerDuty MCP client with only read-only tools (if credentials available)
            pagerduty_mcp_client, pagerduty_tools = build_pagerduty_mcp_client(
                secrets_json["PAGERDUTY_API_KEY"],
                pagerduty_api_url,
            )
            # Append pagerduty to opened clients
            opened_clients["PagerDuty"] = pagerduty_mcp_client
            # Extend tools list with provided pagerduty tools
            tools.extend(pagerduty_tools)
        except Exception as e:
            print(f"Error setting up PagerDuty MCP client: {str(e)}")

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
