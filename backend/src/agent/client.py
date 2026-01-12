"""Claude Agent SDK client wrapper with multi-turn session support."""

import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)

from src.agent.exceptions import SessionNotFoundError
from src.agent.options import get_default_options
from src.config import settings
from src.services.sessions import ManagedSession, SessionManager, SessionState

logger = logging.getLogger(__name__)


@dataclass
class StreamEvent:
    """Event emitted during agent response streaming."""

    type: str
    text: str | None = None
    tool_name: str | None = None
    tool_id: str | None = None
    tool_input: dict[str, Any] | None = None
    tool_result: str | None = None
    session_id: str | None = None
    cost: float | None = None
    is_error: bool = False
    questions: list[dict[str, Any]] | None = None  # For AskUserQuestion


class AgentManager:
    """Manages Claude Agent SDK sessions with multi-turn support.

    Uses ClaudeSDKClient to maintain conversation context across
    multiple exchanges in the same session.
    """

    def __init__(self) -> None:
        """Initialize the agent manager with a session manager."""
        self.session_manager = SessionManager(ttl_seconds=settings.session_ttl_seconds)

    async def stream_response(
        self,
        prompt: str,
        session_id: str | None = None,
        options: ClaudeAgentOptions | None = None,
    ) -> AsyncIterator[StreamEvent]:
        """Stream response from existing or new session.

        Args:
            prompt: The user's message/prompt.
            session_id: Optional existing session ID to continue.
            options: Optional custom options (used only for new sessions).

        Yields:
            StreamEvent objects for text, tool calls, and completion.
        """
        session: ManagedSession | None = None

        logger.info(f"[stream_response] Received request with session_id={session_id}")

        # Try to get existing session
        if session_id:
            session = await self.session_manager.get_session(session_id)
            if session is None:
                logger.info(f"[stream_response] Session {session_id} not found, creating new")
            else:
                logger.info(
                    f"[stream_response] Found existing session {session_id}, state={session.state}"
                )

        # Create new session if needed
        if session is None:
            opts = options or get_default_options()
            session = await self.session_manager.create_session(opts)
            logger.info(f"[stream_response] Created new session {session.session_id}")
        elif session.sdk_session_id != "default":
            # For multi-turn: reconnect the client with resume option to continue
            # conversation. Works around SDK limitation where receive_response()
            # can only be iterated once.
            logger.info(f"[stream_response] Reconnecting with resume={session.sdk_session_id}")
            await session.client.disconnect()
            from dataclasses import replace

            resumed_opts = replace(session.options, resume=session.sdk_session_id)
            from claude_agent_sdk import ClaudeSDKClient

            session.client = ClaudeSDKClient(options=resumed_opts)
            await session.client.connect()
            logger.info("[stream_response] Client reconnected with resume option")

        # Update session state
        await self.session_manager.set_session_state(session.session_id, SessionState.STREAMING)

        try:
            # Send query to the client
            logger.info(f"[stream_response] Sending query to session {session.session_id}")
            await session.client.query(prompt)
            logger.info("[stream_response] Query sent, starting to receive response")

            # Stream the response
            async for event in self._process_response(session):
                yield event

            logger.info(f"[stream_response] Response complete for session {session.session_id}")

        except Exception as e:
            logger.error(f"Error in session {session.session_id}: {e}")
            await self.session_manager.set_session_state(session.session_id, SessionState.ERROR)
            yield StreamEvent(
                type="error",
                text=str(e),
                is_error=True,
                session_id=session.session_id,
            )

    async def respond_to_prompt(
        self,
        session_id: str,
        response: str,
    ) -> AsyncIterator[StreamEvent]:
        """Continue session with user response to AskUserQuestion.

        Args:
            session_id: The session ID to continue.
            response: The user's response.

        Yields:
            StreamEvent objects for the continued conversation.

        Raises:
            SessionNotFoundError: If session is not found.
        """
        session = await self.session_manager.get_session(session_id)
        if session is None:
            raise SessionNotFoundError(f"Session {session_id} not found")

        # Update session state
        await self.session_manager.set_session_state(session.session_id, SessionState.STREAMING)

        try:
            # Send the user's response with SDK session ID for multi-turn
            logger.info(
                f"[respond_to_prompt] Sending to session {session.session_id} "
                f"(sdk_session_id={session.sdk_session_id})"
            )
            await session.client.query(response, session_id=session.sdk_session_id)
            logger.info("[respond_to_prompt] Response sent, receiving response")

            # Stream the response
            async for event in self._process_response(session):
                yield event

            logger.info(f"[respond_to_prompt] Complete for session {session.session_id}")

        except Exception as e:
            logger.error(f"Error in session {session.session_id}: {e}")
            await self.session_manager.set_session_state(session.session_id, SessionState.ERROR)
            yield StreamEvent(
                type="error",
                text=str(e),
                is_error=True,
                session_id=session.session_id,
            )

    def _create_tool_result_event(self, block: ToolResultBlock, session_id: str) -> StreamEvent:
        """Create a StreamEvent from a ToolResultBlock."""
        return StreamEvent(
            type="tool_result",
            tool_id=block.tool_use_id,
            tool_result=block.content if isinstance(block.content, str) else str(block.content),
            is_error=block.is_error or False,
            session_id=session_id,
        )

    async def _process_response(self, session: ManagedSession) -> AsyncIterator[StreamEvent]:
        """Process messages from the client and yield StreamEvents.

        Args:
            session: The active session.

        Yields:
            StreamEvent objects for each message component.
        """
        # Track AskUserQuestion tool IDs to skip their results
        ask_user_question_ids: set[str] = set()

        logger.info(f"[_process_response] Starting receive_response() for {session.session_id}")
        async for message in session.client.receive_response():
            logger.info(f"[_process_response] Received message type: {type(message).__name__}")
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        yield StreamEvent(
                            type="text",
                            text=block.text,
                            session_id=session.session_id,
                        )
                    elif isinstance(block, ToolUseBlock):
                        # Check for AskUserQuestion tool
                        if block.name == "AskUserQuestion":
                            # Track this tool ID to skip its result
                            ask_user_question_ids.add(block.id)
                            await self.session_manager.set_session_state(
                                session.session_id, SessionState.WAITING_INPUT
                            )
                            yield StreamEvent(
                                type="user_input_required",
                                tool_name=block.name,
                                tool_id=block.id,
                                tool_input=block.input,
                                questions=block.input.get("questions"),
                                session_id=session.session_id,
                            )
                        else:
                            yield StreamEvent(
                                type="tool_start",
                                tool_name=block.name,
                                tool_id=block.id,
                                tool_input=block.input,
                                session_id=session.session_id,
                            )
                    elif isinstance(block, ToolResultBlock):
                        yield self._create_tool_result_event(block, session.session_id)

            elif isinstance(message, UserMessage):
                # UserMessage contains tool results from Claude Code SDK
                for user_block in message.content:
                    if isinstance(user_block, ToolResultBlock):
                        # Skip tool results for AskUserQuestion (handled by frontend)
                        if user_block.tool_use_id in ask_user_question_ids:
                            continue
                        yield self._create_tool_result_event(user_block, session.session_id)

            elif isinstance(message, ResultMessage):
                # Save SDK session ID for multi-turn conversations
                if message.session_id:
                    logger.info(f"[_process_response] Saving SDK session_id: {message.session_id}")
                    session.sdk_session_id = message.session_id

                # Determine final state based on result
                final_state = SessionState.ERROR if message.is_error else SessionState.ACTIVE

                await self.session_manager.set_session_state(session.session_id, final_state)

                yield StreamEvent(
                    type="done",
                    session_id=session.session_id,
                    cost=message.total_cost_usd,
                    is_error=message.is_error,
                )

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session explicitly.

        Args:
            session_id: The session ID to delete.

        Returns:
            True if session was found and deleted.
        """
        return await self.session_manager.delete_session(session_id)

    async def cleanup(self) -> None:
        """Clean up all sessions (for shutdown)."""
        await self.session_manager.cleanup_all()


# Keep AgentRunner as an alias for backward compatibility with tests
class AgentRunner(AgentManager):
    """Deprecated: Use AgentManager instead.

    This alias is kept for backward compatibility.
    """

    async def run(self, prompt: str) -> AsyncIterator[StreamEvent]:
        """Run a query (backward compatible method).

        Args:
            prompt: The user's prompt.

        Yields:
            StreamEvent objects.
        """
        async for event in self.stream_response(prompt):
            yield event
