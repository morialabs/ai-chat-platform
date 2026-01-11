"""Chat API routes with SSE streaming and multi-turn session support."""

import json
from collections.abc import AsyncIterator
from dataclasses import asdict

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.agent.client import AgentManager, StreamEvent
from src.agent.exceptions import SessionNotFoundError

router = APIRouter()

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}

# Module-level singleton for agent manager
_agent_manager: AgentManager | None = None


def get_agent_manager() -> AgentManager:
    """Get the global AgentManager instance."""
    global _agent_manager
    if _agent_manager is None:
        _agent_manager = AgentManager()
    return _agent_manager


class ChatRequest(BaseModel):
    """Request body for chat endpoint."""

    message: str
    session_id: str | None = None


class UserResponse(BaseModel):
    """Request body for user response endpoint."""

    session_id: str
    response: str


def event_to_sse(event: StreamEvent) -> str:
    """Convert a StreamEvent to SSE format."""
    data = {k: v for k, v in asdict(event).items() if v is not None}
    return f"data: {json.dumps(data)}\n\n"


async def stream_agent_response(
    message: str, session_id: str | None = None
) -> AsyncIterator[str]:
    """Stream agent response as SSE events.

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
    """Main chat endpoint with SSE streaming.

    Accepts a message and streams back the agent's response as Server-Sent Events.
    If a session_id is provided, continues the existing conversation with full
    context preserved. Otherwise, starts a new session.

    Args:
        request: The chat request containing the message and optional session_id.

    Returns:
        StreamingResponse with SSE events.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    return StreamingResponse(
        stream_agent_response(request.message, request.session_id),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )


@router.post("/respond")
async def respond(request: UserResponse) -> StreamingResponse:
    """Continue conversation with user's response.

    Used when the agent asks for user input via AskUserQuestion tool.
    The session must exist and be in the WAITING_INPUT state.

    Args:
        request: The user response containing session_id and response.

    Returns:
        StreamingResponse with SSE events.
    """
    if not request.session_id:
        raise HTTPException(status_code=400, detail="Session ID is required")

    manager = get_agent_manager()

    async def generate() -> AsyncIterator[str]:
        try:
            async for event in manager.respond_to_prompt(request.session_id, request.response):
                yield event_to_sse(event)
        except SessionNotFoundError:
            error_event = StreamEvent(
                type="error",
                text="Session not found or expired",
                is_error=True,
            )
            yield event_to_sse(error_event)
        except Exception as e:
            error_event = StreamEvent(type="error", text=str(e), is_error=True)
            yield event_to_sse(error_event)

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
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
