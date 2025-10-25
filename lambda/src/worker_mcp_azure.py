import os
import shutil
from mcp import stdio_client, StdioServerParameters
from strands.tools.mcp.mcp_client import MCPClient


# Build Azure MCP client
def initial_azure_mcp_client(tenant_id, client_id, client_secret):

    return MCPClient(
        lambda: stdio_client(
            StdioServerParameters(
                command="azmcp",
                args=["server", "start"],
                env={
                    "AZURE_TENANT_ID": tenant_id,
                    "AZURE_CLIENT_ID": client_id,
                    "AZURE_CLIENT_SECRET": client_secret,
                    # Tell .NET to extract to /tmp (only writable location in Lambda)
                    "DOTNET_BUNDLE_EXTRACT_BASE_DIR": "/tmp",
                    "HOME": "/tmp",
                },
            )
        )
    )


def build_azure_mcp_client(tenant_id, client_id, client_secret):

    # Build Azure MCP client
    azure_mcp_client = initial_azure_mcp_client(tenant_id, client_id, client_secret)

    # Enter to open and leave open
    azure_client = azure_mcp_client.__enter__()

    # Get tools from Azure client
    all_azure_tools = azure_client.list_tools_sync()

    # Note: Filtering by read-only tools is not practical for Azure MCP
    # because tool names don't follow a consistent verb-based naming convention
    # Return client and all tools
    print(
        f"Azure MCP: Returning {len(all_azure_tools)} tools: {[t.tool_spec['name'] for t in all_azure_tools]}"
    )
    return azure_mcp_client, all_azure_tools
