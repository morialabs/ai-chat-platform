"""Claude Agent SDK client wrapper with session support.

Uses the stateless query() function with conversation history stored server-side,
since ClaudeSDKClient cannot be reused across different FastAPI request contexts.
"""

import json
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from claude_code_sdk import (
    AssistantMessage,
    ClaudeCodeOptions,
    ResultMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
    query,
)

from src.agent.options import get_default_options
from src.agent.sessions import SessionManager, get_session_manager

logger = logging.getLogger(__name__)


@dataclass
class StreamEvent:
    """Event emitted during agent response streaming."""

    type: str
    text: str | None = None
    tool_name: str | None = None
    tool_id: str | None = None
    tool_input: dict[str, Any] | None = None
    content: str | None = None
    session_id: str | None = None
    cost: float | None = None
    is_error: bool = False
    questions: list[dict[str, Any]] | None = None


def _serialize_content(content: str | list[dict[str, Any]] | None) -> str:
    """Serialize tool result content to string."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    return json.dumps(content)


class AgentRunner:
    """Runs Claude agent queries with streaming output and session support."""

    def __init__(
        self,
        options: ClaudeCodeOptions | None = None,
        session_manager: SessionManager | None = None,
    ) -> None:
        """Initialize the agent runner.

        Args:
            options: Custom options, or None to use defaults.
            session_manager: Session manager, or None to use global.
        """
        self.options = options or get_default_options()
        self.session_manager = session_manager or get_session_manager()

    async def run(
        self, prompt: str, session_id: str | None = None
    ) -> AsyncIterator[StreamEvent]:
        """Run a query and yield streaming events.

        Args:
            prompt: The user's prompt.
            session_id: Optional session ID for multi-turn conversations.

        Yields:
            StreamEvent objects for text, tool calls, and completion.
        """
        session = await self.session_manager.get_or_create_session(session_id)
        actual_session_id = session.session_id

        # Build prompt with conversation history
        context_prompt = self.session_manager.build_context_prompt(session, prompt)

        # Store user message in history
        await self.session_manager.add_message(actual_session_id, "user", prompt)

        # Collect assistant response for history
        assistant_response_parts: list[str] = []

        try:
            async for message in query(prompt=context_prompt, options=self.options):
                async for event in self._process_message(message, actual_session_id):
                    # Collect text for history
                    if event.type == "text" and event.text:
                        assistant_response_parts.append(event.text)

                    yield event

                    # Check if we should pause for user input
                    if event.type == "user_input_required":
                        await self.session_manager.mark_waiting_for_input(
                            actual_session_id
                        )
                        # Save partial response before pausing
                        if assistant_response_parts:
                            await self.session_manager.add_message(
                                actual_session_id,
                                "assistant",
                                "".join(assistant_response_parts),
                            )
                        return

            # Save complete assistant response to history
            if assistant_response_parts:
                await self.session_manager.add_message(
                    actual_session_id, "assistant", "".join(assistant_response_parts)
                )

        except Exception as e:
            logger.exception(f"Error in run for session {actual_session_id}")
            yield StreamEvent(type="error", text=str(e), is_error=True)

    async def respond_to_user_prompt(
        self, session_id: str, response: str
    ) -> AsyncIterator[StreamEvent]:
        """Continue a conversation after user provides input.

        Args:
            session_id: The session ID to resume.
            response: The user's response to the prompt.

        Yields:
            StreamEvent objects for the continued conversation.
        """
        session = await self.session_manager.get_session(session_id)
        if not session:
            yield StreamEvent(type="error", text="Session not found", is_error=True)
            return

        if not session.waiting_for_user_input:
            yield StreamEvent(
                type="error", text="Session not waiting for input", is_error=True
            )
            return

        await self.session_manager.clear_waiting_for_input(session_id)

        # Use run() to continue the conversation with the user's response
        async for event in self.run(response, session_id):
            yield event

    async def _process_message(
        self, message: Any, session_id: str
    ) -> AsyncIterator[StreamEvent]:
        """Process a message from the SDK and yield events.

        Args:
            message: Message from query().
            session_id: Current session ID.

        Yields:
            StreamEvent objects.
        """
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    yield StreamEvent(type="text", text=block.text)
                elif isinstance(block, ToolUseBlock):
                    # Check for AskUserQuestion tool
                    if block.name == "AskUserQuestion":
                        questions = block.input.get("questions", [])
                        yield StreamEvent(
                            type="user_input_required",
                            tool_id=block.id,
                            tool_name=block.name,
                            tool_input=block.input,
                            questions=questions,
                        )
                    else:
                        yield StreamEvent(
                            type="tool_start",
                            tool_name=block.name,
                            tool_id=block.id,
                            tool_input=block.input,
                        )

        elif isinstance(message, UserMessage):
            # UserMessage can contain tool results
            if isinstance(message.content, list):
                for block in message.content:
                    if isinstance(block, ToolResultBlock):
                        yield StreamEvent(
                            type="tool_result",
                            tool_id=block.tool_use_id,
                            content=_serialize_content(block.content),
                            is_error=block.is_error or False,
                        )

        elif isinstance(message, ResultMessage):
            yield StreamEvent(
                type="done",
                session_id=session_id,
                cost=message.total_cost_usd,
                is_error=message.is_error,
            )
