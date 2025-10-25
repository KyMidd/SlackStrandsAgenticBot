import os
import shutil
from mcp import stdio_client, StdioServerParameters
from strands.tools.mcp.mcp_client import MCPClient


# Build AWS CLI MCP client
def initial_aws_cli_mcp_client(
    aws_region="us-east-1",
):

    # Run AWS CLI MCP
    opt_aws_cli_mcp_dir = "/opt/aws-cli-mcp-server"

    # Create working directory in /tmp for runtime files
    os.makedirs("/tmp/aws-mcp-working", exist_ok=True)
    os.makedirs("/tmp/.aws", exist_ok=True)

    # Copy AWS config file with pre-configured profiles to /tmp
    shutil.copy("/opt/aws_config", "/tmp/.aws/config")

    # Build environment variables for AWS CLI MCP
    env = {
        # Lambda not writeable except /tmp
        "HOME": "/tmp",  # Set HOME to /tmp so log files go to writable location
        "AWS_API_MCP_WORKING_DIR": "/tmp/aws-mcp-working",
        # AWS config
        "AWS_REGION": aws_region,
        # Ensure AWS CLI MCP server uses config file
        "AWS_CONFIG_FILE": "/tmp/.aws/config",
        "AWS_SDK_LOAD_CONFIG": "1",
        # Pass through Lambda execution role credentials to permit assuming other roles
        "AWS_ACCESS_KEY_ID": os.environ.get("AWS_ACCESS_KEY_ID", ""),
        "AWS_SECRET_ACCESS_KEY": os.environ.get("AWS_SECRET_ACCESS_KEY", ""),
        "AWS_SESSION_TOKEN": os.environ.get("AWS_SESSION_TOKEN", ""),
    }

    return MCPClient(
        lambda: stdio_client(
            StdioServerParameters(
                cwd="/tmp/aws-mcp-working",
                command=f"{opt_aws_cli_mcp_dir}/.venv/bin/awslabs.aws-api-mcp-server",
                env=env,
            )
        )
    )


def build_aws_cli_mcp_client(
    aws_region="us-east-1",
):

    # Build AWS CLI MCP client
    aws_cli_mcp_client = initial_aws_cli_mcp_client(
        aws_region=aws_region,
    )

    # Enter to open and leave open
    aws_cli_client = aws_cli_mcp_client.__enter__()

    # Get tools from AWS CLI MCP client
    all_aws_cli_tools = aws_cli_client.list_tools_sync()

    print(
        f"AWS CLI MCP: Returning {len(all_aws_cli_tools)} tools: {[t.tool_spec['name'] for t in all_aws_cli_tools]}"
    )
    return aws_cli_mcp_client, all_aws_cli_tools
