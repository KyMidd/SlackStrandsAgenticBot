import os
import shutil
from mcp import stdio_client, StdioServerParameters
from strands.tools.mcp.mcp_client import MCPClient

TOOLS_PREFIX = "azure"


def build_azure_mcp_client(tenant_id, client_id, client_secret):
    """Build Azure MCP client."""

    # Create Azure MCP client
    azure_mcp_client = MCPClient(
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
        ),
        prefix=TOOLS_PREFIX,
    )

    return azure_mcp_client
