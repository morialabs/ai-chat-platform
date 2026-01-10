"""Chat API routes with SSE streaming."""

import json
from collections.abc import AsyncIterator
from dataclasses import asdict

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.agent.client import AgentRunner, StreamEvent

router = APIRouter()

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


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


async def stream_agent_response(message: str) -> AsyncIterator[str]:
    """Stream agent response as SSE events.

    Args:
        message: The user's message.

    Yields:
        SSE formatted strings.
    """
    runner = AgentRunner()

    try:
        async for event in runner.run(message):
            yield event_to_sse(event)
    except Exception as e:
        error_event = StreamEvent(type="error", text=str(e), is_error=True)
        yield event_to_sse(error_event)

    yield "data: [DONE]\n\n"


@router.post("")
async def chat(request: ChatRequest) -> StreamingResponse:
    """Main chat endpoint with SSE streaming.

    Accepts a message and streams back the agent's response as Server-Sent Events.

    Args:
        request: The chat request containing the message and optional session_id.

    Returns:
        StreamingResponse with SSE events.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    return StreamingResponse(
        stream_agent_response(request.message),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )


@router.post("/respond")
async def respond(request: UserResponse) -> StreamingResponse:
    """Continue conversation with user's response.

    Used when the agent asks for user input via AskUserQuestion tool.

    Args:
        request: The user response containing session_id and response.

    Returns:
        StreamingResponse with SSE events.
    """
    if not request.session_id:
        raise HTTPException(status_code=400, detail="Session ID is required")

    # TODO: Implement proper session management with ClaudeSDKClient
    return StreamingResponse(
        stream_agent_response(request.response),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )
