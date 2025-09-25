import os
import requests
from mcp.client.sse import sse_client
from strands.tools.mcp.mcp_client import MCPClient

read_only_tools_permitted_prefixes = (
    "fetch",
    "get",
    "lookup",
    "search",
    "atlassianUserInfo",
)


def get_access_token(refresh_token, client_id):
    """Get fresh access token using refresh token and client ID"""
    if not refresh_token or not client_id:
        raise RuntimeError("Missing ATLASSIAN_REFRESH_TOKEN or ATLASSIAN_CLIENT_ID")

    response = requests.post(
        "https://mcp.atlassian.com/v1/token",
        data={
            "grant_type": "refresh_token",
            "client_id": client_id,
            "refresh_token": refresh_token,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def initial_atlassian_mcp_client(refresh_token, client_id):
    """Create initial Atlassian MCP client with OAuth2 authentication"""
    access_token = get_access_token(refresh_token, client_id)

    return MCPClient(
        lambda: sse_client(
            "https://mcp.atlassian.com/v1/sse",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=300.0,
        ),
        startup_timeout=60,
    )


def build_atlassian_mcp_client(
    refresh_token, client_id, build_atlassian_mcp_client="read_only"
):
    """Build Atlassian MCP client"""

    # Build Atlassian MCP client
    atlassian_mcp_client = initial_atlassian_mcp_client(refresh_token, client_id)

    # Enter to open and leave open
    atlassian_client = atlassian_mcp_client.__enter__()

    # Get tools from Atlassian client
    all_atlassian_tools = atlassian_client.list_tools_sync()

    # If read-only tools requested, only include those tools
    if build_atlassian_mcp_client == "read_only":

        filtered_tools = []
        for tool in all_atlassian_tools:
            tool_name = tool.tool_spec["name"]
            if tool_name.startswith(read_only_tools_permitted_prefixes):
                filtered_tools.append(tool)

        return atlassian_mcp_client, filtered_tools

    # If filtered list of MCP tools is not required, return client and all tools
    else:
        return atlassian_mcp_client, all_atlassian_tools
