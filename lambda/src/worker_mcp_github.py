from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp.mcp_client import MCPClient

read_only_tools_permitted_prefixes = ("download_", "get_", "list_", "search_")


# Build GitHub MCP client
def initial_github_mcp_client(github_token):
    return MCPClient(
        lambda: streamablehttp_client(
            "https://api.githubcopilot.com/mcp/",
            headers={"Authorization": f"Bearer {github_token}"},
        )
    )


def build_github_mcp_client(github_token, build_github_mcp_client="read_only"):

    # Build github MCP client
    github_mcp_client = initial_github_mcp_client(github_token)

    # Enter to open and leave open
    github_client = github_mcp_client.__enter__()

    # Get tools from GitHub client
    all_github_tools = github_client.list_tools_sync()

    # If read-only tools requested, only include those tools
    if build_github_mcp_client == "read_only":

        filtered_tools = []
        for tool in all_github_tools:
            tool_name = tool.tool_spec["name"]
            if tool_name.startswith(read_only_tools_permitted_prefixes):
                filtered_tools.append(tool)

        return github_mcp_client, filtered_tools

    # If filtered list of MCP tools is not required, return client and all tools
    else:
        return github_mcp_client, all_github_tools
