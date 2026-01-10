"""Test hooks module."""

import pytest

from src.agent.hooks import create_hooks, validate_bash_commands


@pytest.mark.asyncio
async def test_blocks_dangerous_rm_rf() -> None:
    """Verify rm -rf / is blocked."""
    input_data = {"tool_name": "Bash", "tool_input": {"command": "rm -rf /"}}
    result = await validate_bash_commands(input_data, None, None)  # type: ignore[arg-type]
    assert result.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"


@pytest.mark.asyncio
async def test_blocks_fork_bomb() -> None:
    """Verify fork bomb pattern is blocked."""
    input_data = {"tool_name": "Bash", "tool_input": {"command": ":(){:|:&};:"}}
    result = await validate_bash_commands(input_data, None, None)  # type: ignore[arg-type]
    assert result.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"


@pytest.mark.asyncio
async def test_allows_safe_commands() -> None:
    """Verify safe commands are allowed."""
    input_data = {"tool_name": "Bash", "tool_input": {"command": "ls -la"}}
    result = await validate_bash_commands(input_data, None, None)  # type: ignore[arg-type]
    assert result == {}


@pytest.mark.asyncio
async def test_ignores_non_bash_tools() -> None:
    """Verify non-Bash tools are ignored."""
    input_data = {"tool_name": "Read", "tool_input": {"file_path": "/etc/passwd"}}
    result = await validate_bash_commands(input_data, None, None)  # type: ignore[arg-type]
    assert result == {}


def test_create_hooks_returns_dict() -> None:
    """Verify create_hooks returns proper structure."""
    hooks = create_hooks()
    assert "PreToolUse" in hooks
    assert "PostToolUse" in hooks
    assert len(hooks["PreToolUse"]) == 2
    assert len(hooks["PostToolUse"]) == 1
