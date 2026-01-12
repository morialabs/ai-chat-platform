"""MCP server configuration for custom tools."""

from claude_agent_sdk import create_sdk_mcp_server
from claude_agent_sdk.types import McpSdkServerConfig

from src.tools.echo import echo_tool


def create_tools_server() -> McpSdkServerConfig:
    """Create the in-process MCP server with custom tools.

    Returns:
        McpSdkServerConfig configured with all custom tools.
    """
    return create_sdk_mcp_server(
        name="tools",
        version="1.0.0",
        tools=[echo_tool],
    )
