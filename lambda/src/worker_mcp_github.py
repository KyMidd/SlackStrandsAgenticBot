from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp.mcp_client import MCPClient

TOOLS_PREFIX = "github"
READ_ONLY_PREFIXES = ["download_", "get_", "list_", "search_"]


def build_github_mcp_client(github_token, build_github_mcp_client="read_only"):
    """Build GitHub MCP client."""

    # Define tool filters for read-only mode
    tool_filters = None
    if build_github_mcp_client == "read_only":
        # Filters are applied AFTER prefix, so add prefix + separator to each read-only prefix
        prefixed_read_only = tuple(
            f"{TOOLS_PREFIX}_{tool_prefix}" for tool_prefix in READ_ONLY_PREFIXES
        )
        tool_filters = {
            "allowed": [lambda tool: tool.tool_name.startswith(prefixed_read_only)]
        }

    # Create GitHub MCP client
    github_mcp_client = MCPClient(
        lambda: streamablehttp_client(
            "https://api.githubcopilot.com/mcp/",
            headers={"Authorization": f"Bearer {github_token}"},
        ),
        tool_filters=tool_filters,
        prefix=TOOLS_PREFIX,
    )

    return github_mcp_client
