"""Custom hooks for agent tool validation and logging."""

import logging
from typing import Any, Literal, cast

from claude_agent_sdk import (
    HookContext,
    HookInput,
    HookJSONOutput,
    HookMatcher,
)

logger = logging.getLogger(__name__)

# Type alias for hook event names
HookEventName = Literal[
    "PreToolUse", "PostToolUse", "UserPromptSubmit", "Stop", "SubagentStop", "PreCompact"
]


async def log_tool_usage(
    input_data: HookInput,
    tool_use_id: str | None,
    context: HookContext,
) -> HookJSONOutput:
    """Log all tool usage for analytics and debugging."""
    tool_name = input_data.get("tool_name", "unknown")
    logger.info(f"Tool used: {tool_name}, ID: {tool_use_id}")
    return {}


async def validate_bash_commands(
    input_data: HookInput,
    tool_use_id: str | None,
    context: HookContext,
) -> HookJSONOutput:
    """Validate bash commands for safety, blocking dangerous patterns."""
    if input_data.get("tool_name") != "Bash":
        return {}

    tool_input = cast(dict[str, Any], input_data.get("tool_input") or {})
    command = tool_input.get("command", "")

    # Block dangerous patterns
    dangerous_patterns = [
        "rm -rf /",
        "rm -rf ~",
        "sudo rm",
        "> /dev/sda",
        "mkfs.",
        "dd if=",
        ":(){:|:&};:",  # Fork bomb
    ]

    for pattern in dangerous_patterns:
        if pattern in command:
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (f"Dangerous command pattern blocked: {pattern}"),
                }
            }

    return {}


async def track_file_changes(
    input_data: HookInput,
    tool_use_id: str | None,
    context: HookContext,
) -> HookJSONOutput:
    """Track file modifications for audit trail."""
    tool_name = input_data.get("tool_name")

    if tool_name in ["Write", "Edit"]:
        tool_input = cast(dict[str, Any], input_data.get("tool_input") or {})
        file_path = tool_input.get("file_path", "")
        logger.info(f"File modified: {file_path}")

    return {}


def create_hooks() -> dict[HookEventName, list[HookMatcher]]:
    """Create hooks configuration for agent sessions.

    Returns:
        Dictionary mapping hook event names to matchers.
    """
    return {
        "PreToolUse": [
            HookMatcher(hooks=[log_tool_usage]),
            HookMatcher(matcher="Bash", hooks=[validate_bash_commands]),
        ],
        "PostToolUse": [
            HookMatcher(matcher="Write|Edit", hooks=[track_file_changes]),
        ],
    }
