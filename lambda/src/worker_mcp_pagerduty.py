import os
import shutil
from mcp import stdio_client, StdioServerParameters
from strands.tools.mcp.mcp_client import MCPClient

read_only_tools_permitted_prefixes = ("get_", "list_")


# Build PagerDuty MCP client
def initial_pagerduty_mcp_client(pagerduty_api_key, pagerduty_api_url):

    # Lambda annoyingly makes most of the file system read-only except /tmp
    # Can't directly load stuff into /tmp using Dockerfile because lambda clears /tmp on launch
    # So we copy it from /opt where it lived and put into a new /tmp location lol
    tmp_pagerduty_dir = "/tmp/pagerduty-mcp-server"
    opt_pagerduty_dir = "/opt/pagerduty-mcp-server"

    # Remove any existing copy and copy fresh from /opt
    shutil.copytree(opt_pagerduty_dir, tmp_pagerduty_dir)

    return MCPClient(
        lambda: stdio_client(
            StdioServerParameters(
                # Set working directory for this MCP to where the pagerduty MCP lives
                cwd=tmp_pagerduty_dir,
                # Launch python from the venv inside the copied pagerduty MCP directory
                # This is required so python finds the pre-staged venv and dependencies
                command=f"{tmp_pagerduty_dir}/.venv/bin/python",
                args=["-m", "pagerduty_mcp", "--enable-write-tools"],
                env={
                    "PAGERDUTY_HOST": pagerduty_api_url,
                    "PAGERDUTY_USER_API_KEY": pagerduty_api_key,
                },
            )
        )
    )


def build_pagerduty_mcp_client(
    pagerduty_api_key, pagerduty_api_url, build_pagerduty_mcp_client="read_only"
):

    # Build PagerDuty MCP client
    pagerduty_mcp_client = initial_pagerduty_mcp_client(
        pagerduty_api_key, pagerduty_api_url
    )

    # Enter to open and leave open
    pagerduty_client = pagerduty_mcp_client.__enter__()

    # Get tools from PagerDuty client
    all_pagerduty_tools = pagerduty_client.list_tools_sync()

    # If read-only tools requested, only include those tools
    if build_pagerduty_mcp_client == "read_only":

        filtered_tools = []
        for tool in all_pagerduty_tools:
            tool_name = tool.tool_spec["name"]
            if tool_name.startswith(read_only_tools_permitted_prefixes):
                filtered_tools.append(tool)

        return pagerduty_mcp_client, filtered_tools

    # If filtered list of MCP tools is not required, return client and all tools
    else:
        return pagerduty_mcp_client, all_pagerduty_tools
