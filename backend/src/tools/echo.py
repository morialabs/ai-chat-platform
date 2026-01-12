"""Echo tool for testing custom tool integration."""

from typing import Any

from claude_agent_sdk import tool


@tool("echo", "Echo back the input message", {"message": str})
async def echo_tool(args: dict[str, Any]) -> dict[str, Any]:
    """Simple tool that echoes back the input message.

    This tool is primarily for testing the custom tool integration.

    Args:
        args: Dictionary with 'message' key containing text to echo.

    Returns:
        Dictionary with 'content' key containing the echoed text.
    """
    message = args.get("message", "")
    return {"content": [{"type": "text", "text": f"Echo: {message}"}]}
