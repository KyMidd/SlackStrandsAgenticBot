import os
import shutil
from mcp import stdio_client, StdioServerParameters
from strands.tools.mcp.mcp_client import MCPClient

TOOLS_PREFIX = "pagerduty"
READ_ONLY_PREFIXES = ["get_", "list_"]


def build_pagerduty_mcp_client(
    pagerduty_api_key, pagerduty_api_url, build_pagerduty_mcp_client="read_only"
):
    """Build PagerDuty MCP client."""

    # Lambda annoyingly makes most of the file system read-only except /tmp
    # Can't directly load stuff into /tmp using Dockerfile because lambda clears /tmp on launch
    # So we copy it from /opt where it lived and put into a new /tmp location lol
    tmp_pagerduty_dir = "/tmp/pagerduty-mcp-server"
    opt_pagerduty_dir = "/opt/pagerduty-mcp-server"

    # Remove any existing copy and copy fresh from /opt
    # Handle warm Lambda invocations where /tmp persists
    if os.path.exists(tmp_pagerduty_dir):
        shutil.rmtree(tmp_pagerduty_dir)
    shutil.copytree(opt_pagerduty_dir, tmp_pagerduty_dir)

    # Define tool filters for read-only mode
    tool_filters = None
    if build_pagerduty_mcp_client == "read_only":
        # Filters are applied AFTER prefix, so add prefix + separator to each read-only prefix
        prefixed_read_only = tuple(
            f"{TOOLS_PREFIX}_{tool_prefix}" for tool_prefix in READ_ONLY_PREFIXES
        )
        tool_filters = {
            "allowed": [lambda tool: tool.tool_name.startswith(prefixed_read_only)]
        }

    # Create PagerDuty MCP client
    pagerduty_mcp_client = MCPClient(
        lambda: stdio_client(
            StdioServerParameters(
                cwd=tmp_pagerduty_dir,
                command=f"{tmp_pagerduty_dir}/.venv/bin/python",
                args=["-m", "pagerduty_mcp", "--enable-write-tools"],
                env={
                    "PAGERDUTY_HOST": pagerduty_api_url,
                    "PAGERDUTY_USER_API_KEY": pagerduty_api_key,
                },
            )
        ),
        tool_filters=tool_filters,
        prefix=TOOLS_PREFIX,
    )

    return pagerduty_mcp_client
