"""Claude Agent SDK client wrapper."""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from claude_code_sdk import (
    AssistantMessage,
    ClaudeCodeOptions,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    query,
)

from src.agent.options import get_default_options


@dataclass
class StreamEvent:
    """Event emitted during agent response streaming."""

    type: str
    text: str | None = None
    tool_name: str | None = None
    tool_id: str | None = None
    tool_input: dict[str, Any] | None = None
    session_id: str | None = None
    cost: float | None = None
    is_error: bool = False


class AgentRunner:
    """Runs Claude agent queries with streaming output."""

    def __init__(self, options: ClaudeCodeOptions | None = None) -> None:
        """Initialize the agent runner.

        Args:
            options: Custom options, or None to use defaults.
        """
        self.options = options or get_default_options()

    async def run(self, prompt: str) -> AsyncIterator[StreamEvent]:
        """Run a query and yield streaming events.

        Args:
            prompt: The user's prompt.

        Yields:
            StreamEvent objects for text, tool calls, and completion.
        """
        async for message in query(prompt=prompt, options=self.options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        yield StreamEvent(type="text", text=block.text)
                    elif isinstance(block, ToolUseBlock):
                        yield StreamEvent(
                            type="tool_start",
                            tool_name=block.name,
                            tool_id=block.id,
                            tool_input=block.input,
                        )

            elif isinstance(message, ResultMessage):
                yield StreamEvent(
                    type="done",
                    session_id=message.session_id,
                    cost=message.total_cost_usd,
                    is_error=message.is_error,
                )
