"""Chat API routes with SSE streaming and multi-turn session support.

Implements Vercel AI SDK UI Message Stream Protocol for frontend compatibility.
See: https://ai-sdk.dev/docs/ai-sdk-ui/stream-protocol
"""

import json
import uuid
from collections.abc import AsyncIterator
from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.agent.client import AgentManager, StreamEvent
from src.agent.exceptions import SessionNotFoundError

router = APIRouter()


def get_sse_headers(session_id: str | None = None) -> dict[str, str]:
    """Get SSE headers including Vercel AI SDK protocol header."""
    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
        "x-vercel-ai-ui-message-stream": "v1",
    }
    if session_id:
        headers["x-session-id"] = session_id
    return headers


# Legacy headers for backward compatibility
SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}

# Module-level singleton for agent manager
_agent_manager: AgentManager | None = None


class VercelStreamState:
    """Tracks state for Vercel protocol conversion."""

    def __init__(self) -> None:
        self.text_id: str | None = None
        self.text_started = False
        self.session_id: str | None = None

    def generate_text_id(self) -> str:
        """Generate a new text ID."""
        self.text_id = f"text-{uuid.uuid4().hex[:8]}"
        return self.text_id


def convert_to_vercel_events(event: StreamEvent, state: VercelStreamState) -> list[dict[str, Any]]:
    """Convert internal StreamEvent to Vercel UI Message Stream Protocol events.

    Args:
        event: The internal StreamEvent from the agent.
        state: Mutable state tracking text IDs and session.

    Returns:
        List of Vercel protocol event dictionaries.
    """
    events: list[dict[str, Any]] = []

    # Track session_id
    if event.session_id:
        state.session_id = event.session_id

    if event.type == "text":
        # Start text block if not started
        if not state.text_started:
            text_id = state.generate_text_id()
            events.append({"type": "text-start", "id": text_id})
            state.text_started = True

        # Emit text delta
        if event.text and state.text_id:
            events.append(
                {
                    "type": "text-delta",
                    "id": state.text_id,
                    "delta": event.text,
                }
            )

    elif event.type == "tool_start":
        # End any ongoing text block before tool
        if state.text_started and state.text_id:
            events.append({"type": "text-end", "id": state.text_id})
            state.text_started = False

        # Emit tool input events
        events.append(
            {
                "type": "tool-input-start",
                "toolCallId": event.tool_id,
                "toolName": event.tool_name,
            }
        )
        events.append(
            {
                "type": "tool-input-available",
                "toolCallId": event.tool_id,
                "toolName": event.tool_name,
                "input": event.tool_input or {},
            }
        )

    elif event.type == "user_input_required":
        # End any ongoing text block before tool
        if state.text_started and state.text_id:
            events.append({"type": "text-end", "id": state.text_id})
            state.text_started = False

        # Emit as AskUserQuestion tool (no result yet - waiting for user)
        events.append(
            {
                "type": "tool-input-start",
                "toolCallId": event.tool_id,
                "toolName": "AskUserQuestion",
            }
        )
        events.append(
            {
                "type": "tool-input-available",
                "toolCallId": event.tool_id,
                "toolName": "AskUserQuestion",
                "input": {
                    "questions": event.questions or [],
                    **(event.tool_input or {}),
                },
            }
        )

    elif event.type == "tool_result":
        # Emit tool output
        events.append(
            {
                "type": "tool-output-available",
                "toolCallId": event.tool_id,
                "output": {
                    "result": event.tool_result,
                    "isError": event.is_error,
                },
            }
        )

    elif event.type == "done":
        # End any ongoing text block
        if state.text_started and state.text_id:
            events.append({"type": "text-end", "id": state.text_id})
            state.text_started = False

        # Emit finish with metadata
        events.append(
            {
                "type": "finish",
                "metadata": {
                    "session_id": event.session_id,
                    "cost": event.cost,
                },
            }
        )

    elif event.type == "error":
        # End any ongoing text block
        if state.text_started and state.text_id:
            events.append({"type": "text-end", "id": state.text_id})
            state.text_started = False

        # Emit error
        events.append(
            {
                "type": "error",
                "errorText": event.text or "Unknown error",
            }
        )

    return events


def vercel_event_to_sse(event: dict[str, Any]) -> str:
    """Convert a Vercel protocol event dict to SSE format."""
    return f"data: {json.dumps(event)}\n\n"


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


def event_to_sse(event: StreamEvent) -> str:
    """Convert a StreamEvent to SSE format."""
    data = {k: v for k, v in asdict(event).items() if v is not None}
    return f"data: {json.dumps(data)}\n\n"


async def stream_agent_response_vercel(
    message: str, session_id: str | None = None
) -> AsyncIterator[tuple[str, str | None]]:
    """Stream agent response as Vercel protocol SSE events.

    Args:
        message: The user's message.
        session_id: Optional session ID to continue an existing conversation.

    Yields:
        Tuples of (SSE formatted string, session_id or None).
    """
    manager = get_agent_manager()
    state = VercelStreamState()

    try:
        async for event in manager.stream_response(message, session_id):
            vercel_events = convert_to_vercel_events(event, state)
            for ve in vercel_events:
                yield vercel_event_to_sse(ve), state.session_id
    except Exception as e:
        error_event = StreamEvent(type="error", text=str(e), is_error=True)
        vercel_events = convert_to_vercel_events(error_event, state)
        for ve in vercel_events:
            yield vercel_event_to_sse(ve), state.session_id

    yield "data: [DONE]\n\n", state.session_id


async def stream_agent_response(message: str, session_id: str | None = None) -> AsyncIterator[str]:
    """Stream agent response as SSE events (legacy format).

    Args:
        message: The user's message.
        session_id: Optional session ID to continue an existing conversation.

    Yields:
        SSE formatted strings.
    """
    manager = get_agent_manager()

    try:
        async for event in manager.stream_response(message, session_id):
            yield event_to_sse(event)
    except Exception as e:
        error_event = StreamEvent(type="error", text=str(e), is_error=True)
        yield event_to_sse(error_event)

    yield "data: [DONE]\n\n"


@router.post("")
async def chat(request: ChatRequest) -> StreamingResponse:
    """Main chat endpoint with SSE streaming using Vercel AI SDK protocol.

    Accepts a message and streams back the agent's response as Server-Sent Events
    following the Vercel UI Message Stream Protocol for frontend compatibility.
    If a session_id is provided, continues the existing conversation with full
    context preserved. Otherwise, starts a new session.

    Args:
        request: The chat request containing the message and optional session_id.

    Returns:
        StreamingResponse with Vercel protocol SSE events.
    """
    # Extract user message from either Vercel format or legacy format
    try:
        user_message = request.get_user_message()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not user_message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Track session_id for header (will be set from first event if new session)
    captured_session_id: str | None = request.session_id

    async def generate() -> AsyncIterator[str]:
        nonlocal captured_session_id
        async for sse_chunk, session_id in stream_agent_response_vercel(
            user_message, request.session_id
        ):
            if session_id and not captured_session_id:
                captured_session_id = session_id
            yield sse_chunk

    # Use request session_id for header if available
    # New sessions will have session_id in finish event metadata
    headers = get_sse_headers(request.session_id)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers=headers,
    )


@router.post("/respond")
async def respond(request: UserResponse) -> StreamingResponse:
    """Continue conversation with user's response using Vercel protocol.

    Used when the agent asks for user input via AskUserQuestion tool.
    The session must exist and be in the WAITING_INPUT state.

    Args:
        request: The user response containing session_id and response.

    Returns:
        StreamingResponse with Vercel protocol SSE events.
    """
    if not request.session_id:
        raise HTTPException(status_code=400, detail="Session ID is required")

    manager = get_agent_manager()
    state = VercelStreamState()

    async def generate() -> AsyncIterator[str]:
        try:
            async for event in manager.respond_to_prompt(request.session_id, request.response):
                vercel_events = convert_to_vercel_events(event, state)
                for ve in vercel_events:
                    yield vercel_event_to_sse(ve)
        except SessionNotFoundError:
            error_event = StreamEvent(
                type="error",
                text="Session not found or expired",
                is_error=True,
            )
            vercel_events = convert_to_vercel_events(error_event, state)
            for ve in vercel_events:
                yield vercel_event_to_sse(ve)
        except Exception as e:
            error_event = StreamEvent(type="error", text=str(e), is_error=True)
            vercel_events = convert_to_vercel_events(error_event, state)
            for ve in vercel_events:
                yield vercel_event_to_sse(ve)

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
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
