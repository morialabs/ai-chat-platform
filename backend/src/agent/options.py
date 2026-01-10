"""Agent configuration options."""

from claude_code_sdk import ClaudeCodeOptions
from claude_code_sdk.types import McpServerConfig

from src.agent.hooks import create_hooks
from src.config import settings
from src.tools.server import create_tools_server


def get_default_options(
    *, include_hooks: bool = True, include_custom_tools: bool = True
) -> ClaudeCodeOptions:
    """Create default agent options.

    Args:
        include_hooks: Whether to include hooks for logging and validation.
        include_custom_tools: Whether to include custom MCP tools.

    Returns:
        Configured ClaudeCodeOptions.
    """
    # Base allowed tools
    allowed_tools = [
        "Read",
        "Write",
        "Edit",
        "Bash",
        "Glob",
        "Grep",
        "WebSearch",
        "WebFetch",
        "Task",
    ]

    # Add custom tool names (prefixed with mcp__<server>__)
    if include_custom_tools:
        allowed_tools.append("mcp__tools__echo")

    # Configure MCP servers
    mcp_servers: dict[str, McpServerConfig] = {}
    if include_custom_tools:
        mcp_servers["tools"] = create_tools_server()

    return ClaudeCodeOptions(
        # Core settings
        model=settings.model,
        cwd=str(settings.workspace_dir),
        # Permission mode - acceptEdits allows file operations without prompting
        permission_mode="acceptEdits",
        # Built-in tools to allow
        allowed_tools=allowed_tools,
        # MCP servers for custom tools
        mcp_servers=mcp_servers,
        # System prompt customization
        append_system_prompt=f"""
You are an AI assistant for {settings.app_name}.
Be helpful, concise, and accurate in your responses.
""",
        # Hooks for validation and logging
        hooks=create_hooks() if include_hooks else None,
    )
