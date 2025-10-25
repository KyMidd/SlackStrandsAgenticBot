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


class PrefixedMCPTool(AgentTool):
    """Wrapper that adds a prefix to an MCP tool's name."""

    def __init__(self, tool, prefix):
        super().__init__()
        self._original_tool = tool
        self._prefix = prefix
        # Cache the prefixed tool spec
        original_spec = tool.tool_spec
        self._prefixed_spec = original_spec.copy()
        self._prefixed_spec["name"] = f"{prefix}{original_spec['name']}"

    @property
    def tool_spec(self):
        return self._prefixed_spec

    @property
    def tool_name(self):
        return self._prefixed_spec["name"]

    @property
    def tool_type(self):
        return self._original_tool.tool_type

    def stream(self, tool_use, *args, **kwargs):
        # Delegate to the original tool with all arguments
        return self._original_tool.stream(tool_use, *args, **kwargs)


def add_prefix_to_mcp_tools(tools, prefix):
    """Add a prefix to all MCP tool names to avoid collisions between MCP servers.

    Args:
        tools: List of MCP tools
        prefix: Prefix to add to tool names (e.g., "github")

    Returns:
        List of wrapped tools with prefixed names
    """
    # Add underscore to prefix
    prefix = f"{prefix}_"
    return [PrefixedMCPTool(tool, prefix) for tool in tools]


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
            # Prefix tool names
            github_tools = add_prefix_to_mcp_tools(github_tools, "github")
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
            # Prefix tool names
            atlassian_tools = add_prefix_to_mcp_tools(atlassian_tools, "atlassian")
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
            # Prefix tool names
            pagerduty_tools = add_prefix_to_mcp_tools(pagerduty_tools, "pagerduty")
            # Extend tools list with provided pagerduty tools
            tools.extend(pagerduty_tools)
        except Exception as e:
            print(f"Error setting up PagerDuty MCP client: {str(e)}")

    ##
    # Azure MCP
    ##

    if enable_azure_mcp:
        try:
            from worker_mcp_azure import build_azure_mcp_client

            ### Build Azure MCP client (if credentials available)
            azure_mcp_client, azure_tools = build_azure_mcp_client(
                secrets_json["AZURE_TENANT_ID"],
                secrets_json["AZURE_CLIENT_ID"],
                secrets_json["AZURE_CLIENT_SECRET"],
            )
            # Append azure to opened clients
            opened_clients["Azure"] = azure_mcp_client
            # Prefix tool names
            azure_tools = add_prefix_to_mcp_tools(azure_tools, "azure")
            # Extend tools list with provided azure tools
            tools.extend(azure_tools)
        except Exception as e:
            print(f"Error setting up Azure MCP client: {str(e)}")

    ##
    # AWS CLI MCP
    ##

    if enable_aws_cli_mcp:
        try:
            from worker_mcp_aws_cli import build_aws_cli_mcp_client

            ### Build AWS CLI MCP client
            aws_cli_mcp_client, aws_cli_tools = build_aws_cli_mcp_client(
                aws_region="us-east-1",
            )
            # Append aws_cli to opened clients
            opened_clients["AWS_CLI"] = aws_cli_mcp_client
            # Prefix tool names
            aws_cli_tools = add_prefix_to_mcp_tools(aws_cli_tools, "aws")
            # Extend tools list with provided aws_cli tools
            tools.extend(aws_cli_tools)
        except Exception as e:
            print(f"Error setting up AWS CLI MCP client: {str(e)}")

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
