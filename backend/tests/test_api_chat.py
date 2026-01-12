"""Tests for chat API endpoints.

Tests the /api/chat endpoint, request models, and SSE headers.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.routes.chat import (
    ChatRequest,
    VercelMessage,
    get_sse_headers,
)
from src.main import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestChatRequestModel:
    """Tests for ChatRequest Pydantic model."""

    def test_vercel_format_accepted(self) -> None:
        """ChatRequest accepts {messages: [...], session_id}."""
        request = ChatRequest(
            messages=[
                VercelMessage(role="user", content="Hello"),
            ],
            session_id="session-123",
        )
        assert request.messages is not None
        assert len(request.messages) == 1
        assert request.session_id == "session-123"

    def test_legacy_format_accepted(self) -> None:
        """ChatRequest accepts {message: '...', session_id}."""
        request = ChatRequest(message="Hello", session_id="session-123")
        assert request.message == "Hello"
        assert request.session_id == "session-123"

    def test_get_user_message_from_messages(self) -> None:
        """get_user_message() extracts last user message from array."""
        request = ChatRequest(
            messages=[
                VercelMessage(role="user", content="First"),
                VercelMessage(role="assistant", content="Response"),
                VercelMessage(role="user", content="Second"),
            ]
        )
        assert request.get_user_message() == "Second"

    def test_get_user_message_from_message(self) -> None:
        """get_user_message() returns message field."""
        request = ChatRequest(message="Hello world")
        assert request.get_user_message() == "Hello world"

    def test_get_user_message_prefers_messages(self) -> None:
        """If both provided, messages takes precedence."""
        request = ChatRequest(
            messages=[VercelMessage(role="user", content="From messages")],
            message="From message field",
        )
        assert request.get_user_message() == "From messages"

    def test_get_user_message_no_user_role(self) -> None:
        """Raises ValueError if no user message in array."""
        request = ChatRequest(
            messages=[
                VercelMessage(role="assistant", content="Hello"),
                VercelMessage(role="system", content="You are helpful"),
            ]
        )
        with pytest.raises(ValueError, match="No user message found"):
            request.get_user_message()

    def test_get_user_message_empty(self) -> None:
        """Raises ValueError if neither format provided."""
        request = ChatRequest()
        with pytest.raises(ValueError, match="No message provided"):
            request.get_user_message()

    def test_multiple_user_messages_returns_last(self) -> None:
        """Returns last user message, not first."""
        request = ChatRequest(
            messages=[
                VercelMessage(role="user", content="First question"),
                VercelMessage(role="assistant", content="First answer"),
                VercelMessage(role="user", content="Second question"),
                VercelMessage(role="assistant", content="Second answer"),
                VercelMessage(role="user", content="Third question"),
            ]
        )
        assert request.get_user_message() == "Third question"

    def test_empty_messages_array(self) -> None:
        """Empty messages array raises ValueError."""
        request = ChatRequest(messages=[])
        with pytest.raises(ValueError, match="No message provided"):
            request.get_user_message()


class TestSSEHeaders:
    """Tests for SSE response headers."""

    def test_cache_control_no_cache(self) -> None:
        """Cache-Control: no-cache."""
        headers = get_sse_headers()
        assert headers["Cache-Control"] == "no-cache"

    def test_connection_keep_alive(self) -> None:
        """Connection: keep-alive."""
        headers = get_sse_headers()
        assert headers["Connection"] == "keep-alive"

    def test_x_accel_buffering_no(self) -> None:
        """X-Accel-Buffering: no."""
        headers = get_sse_headers()
        assert headers["X-Accel-Buffering"] == "no"

    def test_content_type_header(self) -> None:
        """Content-Type header is text/plain; charset=utf-8 for Data Stream."""
        headers = get_sse_headers()
        assert headers["Content-Type"] == "text/plain; charset=utf-8"

    def test_session_header_when_provided(self) -> None:
        """x-session-id header set when session_id provided."""
        headers = get_sse_headers(session_id="session-123")
        assert headers["x-session-id"] == "session-123"

    def test_no_session_header_when_none(self) -> None:
        """x-session-id header not set when session_id is None."""
        headers = get_sse_headers(session_id=None)
        assert "x-session-id" not in headers


class TestChatEndpoint:
    """Tests for POST /api/chat endpoint."""

    def test_empty_message_returns_400(self, client: TestClient) -> None:
        """Empty message returns 400 Bad Request."""
        response = client.post(
            "/api/chat",
            json={"messages": [{"role": "user", "content": ""}]},
        )
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    def test_whitespace_only_returns_400(self, client: TestClient) -> None:
        """Whitespace-only message returns 400."""
        response = client.post(
            "/api/chat",
            json={"messages": [{"role": "user", "content": "   \n\t  "}]},
        )
        assert response.status_code == 400

    def test_no_message_returns_400(self, client: TestClient) -> None:
        """Missing message returns 400."""
        response = client.post("/api/chat", json={})
        assert response.status_code == 400

    def test_content_type_is_text_plain(self, client: TestClient) -> None:
        """Content-Type is text/plain for Data Stream protocol."""
        with patch("src.api.routes.chat.get_agent_manager") as mock_manager:
            mock_instance = AsyncMock()
            mock_instance.stream_response = AsyncMock(return_value=async_empty_generator())
            mock_manager.return_value = mock_instance

            response = client.post(
                "/api/chat",
                json={"messages": [{"role": "user", "content": "Hello"}]},
            )
            assert "text/plain" in response.headers["content-type"]

    def test_session_header_when_provided(self, client: TestClient) -> None:
        """x-session-id header set when session_id in request."""
        with patch("src.api.routes.chat.get_agent_manager") as mock_manager:
            mock_instance = AsyncMock()
            mock_instance.stream_response = AsyncMock(return_value=async_empty_generator())
            mock_manager.return_value = mock_instance

            response = client.post(
                "/api/chat",
                json={
                    "messages": [{"role": "user", "content": "Hello"}],
                    "session_id": "session-123",
                },
            )
            assert response.headers.get("x-session-id") == "session-123"


class TestRespondEndpoint:
    """Tests for POST /api/chat/respond endpoint."""

    def test_missing_session_id_returns_422(self, client: TestClient) -> None:
        """Missing session_id returns 422 (Pydantic validation error)."""
        response = client.post(
            "/api/chat/respond",
            json={"response": "My answer"},
        )
        assert response.status_code == 422

    def test_empty_session_id_returns_400(self, client: TestClient) -> None:
        """Empty session_id returns 400."""
        response = client.post(
            "/api/chat/respond",
            json={"session_id": "", "response": "My answer"},
        )
        assert response.status_code == 400


class TestDeleteSessionEndpoint:
    """Tests for DELETE /api/chat/sessions/{session_id} endpoint."""

    def test_delete_nonexistent_session(self, client: TestClient) -> None:
        """Deleting nonexistent session returns deleted: false."""
        with patch("src.api.routes.chat.get_agent_manager") as mock_manager:
            mock_instance = AsyncMock()
            mock_instance.delete_session = AsyncMock(return_value=False)
            mock_manager.return_value = mock_instance

            response = client.delete("/api/chat/sessions/nonexistent-123")
            assert response.status_code == 200
            assert response.json()["deleted"] is False

    def test_delete_existing_session(self, client: TestClient) -> None:
        """Deleting existing session returns deleted: true."""
        with patch("src.api.routes.chat.get_agent_manager") as mock_manager:
            mock_instance = AsyncMock()
            mock_instance.delete_session = AsyncMock(return_value=True)
            mock_manager.return_value = mock_instance

            response = client.delete("/api/chat/sessions/session-123")
            assert response.status_code == 200
            assert response.json()["deleted"] is True


async def async_empty_generator():
    """Empty async generator for mocking stream responses."""
    return
    yield  # Makes this a generator  # noqa: B901
