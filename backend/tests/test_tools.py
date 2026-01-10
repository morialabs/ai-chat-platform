"""Test custom tools module."""

import pytest

from src.tools.echo import echo_tool
from src.tools.server import create_tools_server


@pytest.mark.asyncio
async def test_echo_tool_returns_message() -> None:
    """Verify echo tool echoes the message."""
    # echo_tool is an SdkMcpTool, call its handler directly
    result = await echo_tool.handler({"message": "Hello, world!"})
    assert result["content"][0]["type"] == "text"
    assert "Hello, world!" in result["content"][0]["text"]


@pytest.mark.asyncio
async def test_echo_tool_handles_empty_message() -> None:
    """Verify echo tool handles empty message."""
    result = await echo_tool.handler({"message": ""})
    assert result["content"][0]["type"] == "text"
    assert "Echo:" in result["content"][0]["text"]


def test_echo_tool_metadata() -> None:
    """Verify echo tool has correct metadata."""
    assert echo_tool.name == "echo"
    assert echo_tool.description == "Echo back the input message"
    assert echo_tool.input_schema == {"message": str}


def test_create_tools_server_returns_config() -> None:
    """Verify create_tools_server returns valid config."""
    config = create_tools_server()
    assert config is not None
