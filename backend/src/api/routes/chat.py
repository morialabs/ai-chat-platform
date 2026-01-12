"""Chat API routes with SSE streaming and multi-turn session support.

Implements AI SDK Data Stream Protocol for frontend compatibility.
See: https://ai-sdk.dev/docs/ai-sdk-ui/stream-protocol#data-stream-protocol

Stream codes:
- 0: text (string value)
- 2: data (array value)
- 3: error (string value)
- 9: tool_call (object with toolCallId, toolName, args)
- a: tool_result (object with toolCallId, result)
- b: tool_call_streaming_start (object with toolCallId, toolName)
- c: tool_call_delta (object with toolCallId, argsTextDelta)
- d: finish_message (object with finishReason, usage)
- e: finish_step (object with finishReason, usage, isContinued)
"""

import json
import uuid
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.agent.client import AgentManager, StreamEvent
from src.agent.exceptions import SessionNotFoundError

router = APIRouter()


def get_sse_headers(session_id: str | None = None) -> dict[str, str]:
    """Get SSE headers for Data Stream protocol."""
    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
        "Content-Type": "text/plain; charset=utf-8",
    }
    if session_id:
        headers["x-session-id"] = session_id
    return headers


# Module-level singleton for agent manager
_agent_manager: AgentManager | None = None


class DataStreamState:
    """Tracks state for Data Stream protocol conversion."""

    def __init__(self) -> None:
        self.session_id: str | None = None

    def generate_tool_id(self) -> str:
        """Generate a new tool call ID."""
        return f"call-{uuid.uuid4().hex[:12]}"


def format_data_stream_part(code: str, value: Any) -> str:
    """Format a single Data Stream part.

    Args:
        code: Single character code (0, 2, 3, 9, a, b, c, d, e).
        value: JSON-serializable value.

    Returns:
        Formatted string like "0:\"Hello\"\n".
    """
    return f"{code}:{json.dumps(value)}\n"


def convert_to_data_stream(event: StreamEvent, state: DataStreamState) -> list[str]:
    """Convert internal StreamEvent to AI SDK Data Stream Protocol parts.

    Args:
        event: The internal StreamEvent from the agent.
        state: Mutable state tracking session info.

    Returns:
        List of Data Stream formatted strings.
    """
    parts: list[str] = []

    # Track session_id
    if event.session_id:
        state.session_id = event.session_id

    if event.type == "text":
        # Text content: code 0
        if event.text:
            parts.append(format_data_stream_part("0", event.text))

    elif event.type == "tool_start":
        # Tool call streaming start: code b
        parts.append(
            format_data_stream_part(
                "b",
                {
                    "toolCallId": event.tool_id,
                    "toolName": event.tool_name,
                },
            )
        )
        # Full tool call with args: code 9
        parts.append(
            format_data_stream_part(
                "9",
                {
                    "toolCallId": event.tool_id,
                    "toolName": event.tool_name,
                    "args": event.tool_input or {},
                },
            )
        )

    elif event.type == "user_input_required":
        # AskUserQuestion as a tool call
        parts.append(
            format_data_stream_part(
                "b",
                {
                    "toolCallId": event.tool_id,
                    "toolName": "AskUserQuestion",
                },
            )
        )
        parts.append(
            format_data_stream_part(
                "9",
                {
                    "toolCallId": event.tool_id,
                    "toolName": "AskUserQuestion",
                    "args": {
                        "questions": event.questions or [],
                        **(event.tool_input or {}),
                    },
                },
            )
        )

    elif event.type == "tool_result":
        # Tool result: code a
        parts.append(
            format_data_stream_part(
                "a",
                {
                    "toolCallId": event.tool_id,
                    "result": event.tool_result
                    if not event.is_error
                    else {"error": event.tool_result},
                },
            )
        )

    elif event.type == "done":
        # Finish step: code e
        parts.append(
            format_data_stream_part(
                "e",
                {
                    "finishReason": "stop",
                    "usage": {"promptTokens": 0, "completionTokens": 0},
                    "isContinued": False,
                },
            )
        )
        # Finish message: code d (includes session metadata)
        parts.append(
            format_data_stream_part(
                "d",
                {
                    "finishReason": "stop",
                    "usage": {"promptTokens": 0, "completionTokens": 0},
                },
            )
        )
        # Send session info as data: code 2
        if state.session_id:
            parts.append(
                format_data_stream_part(
                    "2",
                    [
                        {
                            "session_id": state.session_id,
                            "cost": event.cost,
                        }
                    ],
                )
            )

    elif event.type == "error":
        # Error: code 3
        parts.append(format_data_stream_part("3", event.text or "Unknown error"))

    return parts


def get_agent_manager() -> AgentManager:
    """Get the global AgentManager instance."""
    global _agent_manager
    if _agent_manager is None:
        _agent_manager = AgentManager()
    return _agent_manager


class VercelMessage(BaseModel):
    """Message format from Vercel AI SDK."""

    role: str
    content: str


class ChatRequest(BaseModel):
    """Request body for chat endpoint - supports Vercel AI SDK format."""

    # Vercel AI SDK format
    id: str | None = None
    messages: list[VercelMessage] | None = None

    # Legacy format (single message)
    message: str | None = None

    # Session management
    session_id: str | None = None

    def get_user_message(self) -> str:
        """Extract the user message from either format."""
        # If using Vercel format (messages array), get the last user message
        if self.messages:
            for msg in reversed(self.messages):
                if msg.role == "user":
                    return msg.content
            raise ValueError("No user message found in messages array")

        # Legacy format
        if self.message:
            return self.message

        raise ValueError("No message provided")


class UserResponse(BaseModel):
    """Request body for user response endpoint."""

    session_id: str
    response: str


async def stream_agent_response_data_stream(
    message: str, session_id: str | None = None
) -> AsyncIterator[tuple[str, str | None]]:
    """Stream agent response as AI SDK Data Stream protocol.

    Args:
        message: The user's message.
        session_id: Optional session ID to continue an existing conversation.

    Yields:
        Tuples of (Data Stream formatted string, session_id or None).
    """
    manager = get_agent_manager()
    state = DataStreamState()

    try:
        async for event in manager.stream_response(message, session_id):
            parts = convert_to_data_stream(event, state)
            for part in parts:
                yield part, state.session_id
    except Exception as e:
        error_event = StreamEvent(type="error", text=str(e), is_error=True)
        parts = convert_to_data_stream(error_event, state)
        for part in parts:
            yield part, state.session_id


@router.post("")
async def chat(request: ChatRequest) -> StreamingResponse:
    """Main chat endpoint with streaming using AI SDK Data Stream protocol.

    Accepts a message and streams back the agent's response following
    the AI SDK Data Stream Protocol for frontend compatibility.
    If a session_id is provided, continues the existing conversation with full
    context preserved. Otherwise, starts a new session.

    Args:
        request: The chat request containing the message and optional session_id.

    Returns:
        StreamingResponse with Data Stream protocol events.
    """
    # Extract user message from either Vercel format or legacy format
    try:
        user_message = request.get_user_message()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None

    if not user_message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Track session_id for header (will be set from first event if new session)
    captured_session_id: str | None = request.session_id

    async def generate() -> AsyncIterator[str]:
        nonlocal captured_session_id
        async for chunk, session_id in stream_agent_response_data_stream(
            user_message, request.session_id
        ):
            if session_id and not captured_session_id:
                captured_session_id = session_id
            yield chunk

    # Use request session_id for header if available
    # New sessions will have session_id in data event
    headers = get_sse_headers(request.session_id)

    return StreamingResponse(
        generate(),
        media_type="text/plain; charset=utf-8",
        headers=headers,
    )


@router.post("/respond")
async def respond(request: UserResponse) -> StreamingResponse:
    """Continue conversation with user's response using Data Stream protocol.

    Used when the agent asks for user input via AskUserQuestion tool.
    The session must exist and be in the WAITING_INPUT state.

    Args:
        request: The user response containing session_id and response.

    Returns:
        StreamingResponse with Data Stream protocol events.
    """
    if not request.session_id:
        raise HTTPException(status_code=400, detail="Session ID is required")

    manager = get_agent_manager()
    state = DataStreamState()

    async def generate() -> AsyncIterator[str]:
        try:
            async for event in manager.respond_to_prompt(request.session_id, request.response):
                parts = convert_to_data_stream(event, state)
                for part in parts:
                    yield part
        except SessionNotFoundError:
            error_event = StreamEvent(
                type="error",
                text="Session not found or expired",
                is_error=True,
            )
            parts = convert_to_data_stream(error_event, state)
            for part in parts:
                yield part
        except Exception as e:
            error_event = StreamEvent(type="error", text=str(e), is_error=True)
            parts = convert_to_data_stream(error_event, state)
            for part in parts:
                yield part

    return StreamingResponse(
        generate(),
        media_type="text/plain; charset=utf-8",
        headers=get_sse_headers(request.session_id),
    )


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str) -> dict[str, bool]:
    """Delete a session explicitly.

    Args:
        session_id: The session ID to delete.

    Returns:
        A dict indicating whether the session was deleted.
    """
    manager = get_agent_manager()
    deleted = await manager.delete_session(session_id)
    return {"deleted": deleted}
