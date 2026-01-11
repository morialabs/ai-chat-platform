"""Integration tests for chat API with mocked Claude SDK.

Tests the full flow from API request through to response,
verifying the AI SDK Data Stream protocol events are produced correctly.
"""

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.agent.client import StreamEvent
from src.main import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI app."""
    return TestClient(app)


def parse_data_stream(response_text: str) -> list[tuple[str, Any]]:
    """Parse Data Stream response into list of (code, value) tuples."""
    parts = []
    for line in response_text.strip().split("\n"):
        if line and ":" in line:
            code = line[0]
            json_str = line[2:]  # Skip "X:"
            try:
                value = json.loads(json_str)
                parts.append((code, value))
            except json.JSONDecodeError:
                pass
    return parts


def mock_stream_events(*events: StreamEvent):
    """Create an async generator that yields StreamEvents."""

    async def generator(message: str, session_id: str | None = None):
        for event in events:
            yield event

    return generator


class TestBasicTextResponse:
    """Integration tests for basic text response flow."""

    def test_text_response_streams_correctly(self, client: TestClient) -> None:
        """Verify text response produces correct Data Stream protocol events."""
        events = [
            StreamEvent(type="text", text="Hello ", session_id="session-123"),
            StreamEvent(type="text", text="world!"),
            StreamEvent(type="done", session_id="session-123", cost=0.001),
        ]

        with patch("src.api.routes.chat.get_agent_manager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.stream_response = mock_stream_events(*events)
            mock_manager.return_value = mock_instance

            response = client.post(
                "/api/chat",
                json={"messages": [{"role": "user", "content": "Hello"}]},
            )

            assert response.status_code == 200

            parts = parse_data_stream(response.text)
            codes = [p[0] for p in parts]

            # Should have: text (0, 0), finish_step (e), finish_message (d), data (2)
            assert codes.count("0") == 2
            assert "e" in codes
            assert "d" in codes

    def test_text_content_preserved(self, client: TestClient) -> None:
        """Verify text content is preserved in text parts."""
        events = [
            StreamEvent(type="text", text="Test message", session_id="session-123"),
            StreamEvent(type="done", session_id="session-123"),
        ]

        with patch("src.api.routes.chat.get_agent_manager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.stream_response = mock_stream_events(*events)
            mock_manager.return_value = mock_instance

            response = client.post(
                "/api/chat",
                json={"messages": [{"role": "user", "content": "Hello"}]},
            )

            parts = parse_data_stream(response.text)
            text_parts = [p for p in parts if p[0] == "0"]
            assert len(text_parts) == 1
            assert text_parts[0][1] == "Test message"


class TestToolCallDisplay:
    """Integration tests for tool call flow."""

    def test_tool_call_shows_start_and_result(self, client: TestClient) -> None:
        """Verify tool calls emit b (streaming start), 9 (call), a (result)."""
        events = [
            StreamEvent(type="text", text="Let me read that file.", session_id="session-123"),
            StreamEvent(
                type="tool_start",
                tool_name="Read",
                tool_id="tool-001",
                tool_input={"file_path": "/test.txt"},
                session_id="session-123",
            ),
            StreamEvent(
                type="tool_result",
                tool_id="tool-001",
                tool_result="File contents here",
                is_error=False,
                session_id="session-123",
            ),
            StreamEvent(type="text", text="The file contains the data.", session_id="session-123"),
            StreamEvent(type="done", session_id="session-123", cost=0.002),
        ]

        with patch("src.api.routes.chat.get_agent_manager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.stream_response = mock_stream_events(*events)
            mock_manager.return_value = mock_instance

            response = client.post(
                "/api/chat",
                json={"messages": [{"role": "user", "content": "Read /test.txt"}]},
            )

            assert response.status_code == 200

            parts = parse_data_stream(response.text)
            codes = [p[0] for p in parts]

            # Verify tool events present
            assert "b" in codes  # tool call streaming start
            assert "9" in codes  # tool call
            assert "a" in codes  # tool result

            # Verify tool call content
            tool_call = next(p[1] for p in parts if p[0] == "9")
            assert tool_call["toolName"] == "Read"
            assert tool_call["toolCallId"] == "tool-001"
            assert tool_call["args"]["file_path"] == "/test.txt"

            # Verify tool result content
            tool_result = next(p[1] for p in parts if p[0] == "a")
            assert tool_result["result"] == "File contents here"


class TestMultiTurnConversation:
    """Integration tests for multi-turn conversation flow."""

    def test_session_id_in_data_event(self, client: TestClient) -> None:
        """Verify session_id is included in data event (code 2)."""
        events = [
            StreamEvent(type="text", text="Hello!", session_id="session-abc"),
            StreamEvent(type="done", session_id="session-abc", cost=0.001),
        ]

        with patch("src.api.routes.chat.get_agent_manager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.stream_response = mock_stream_events(*events)
            mock_manager.return_value = mock_instance

            response = client.post(
                "/api/chat",
                json={"messages": [{"role": "user", "content": "Hello"}]},
            )

            parts = parse_data_stream(response.text)
            data_event = next((p[1] for p in parts if p[0] == "2"), None)

            assert data_event is not None
            assert isinstance(data_event, list)
            assert data_event[0]["session_id"] == "session-abc"
            assert "cost" in data_event[0]

    def test_multi_turn_sends_session_id(self, client: TestClient) -> None:
        """Verify second request with session_id continues conversation."""
        events = [
            StreamEvent(type="text", text="I remember!", session_id="session-123"),
            StreamEvent(type="done", session_id="session-123", cost=0.001),
        ]

        with patch("src.api.routes.chat.get_agent_manager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.stream_response = mock_stream_events(*events)
            mock_manager.return_value = mock_instance

            # Second turn with session_id
            response = client.post(
                "/api/chat",
                json={
                    "messages": [{"role": "user", "content": "What did I say?"}],
                    "session_id": "session-123",
                },
            )

            assert response.status_code == 200

            # Verify session_id header is set
            assert response.headers.get("x-session-id") == "session-123"


class TestAskUserQuestionFlow:
    """Integration tests for AskUserQuestion tool flow."""

    def test_ask_user_question_emits_tool_call(self, client: TestClient) -> None:
        """Verify AskUserQuestion emits tool call events with questions."""
        questions = [
            {
                "question": "Which color do you prefer?",
                "header": "Color",
                "options": [
                    {"label": "Red", "description": "A warm color"},
                    {"label": "Blue", "description": "A cool color"},
                ],
                "multiSelect": False,
            }
        ]

        events = [
            StreamEvent(type="text", text="I need to ask you something.", session_id="session-123"),
            StreamEvent(
                type="user_input_required",
                tool_name="AskUserQuestion",
                tool_id="ask-001",
                questions=questions,
                session_id="session-123",
            ),
            # Note: No "done" event - stream pauses waiting for user input
        ]

        with patch("src.api.routes.chat.get_agent_manager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.stream_response = mock_stream_events(*events)
            mock_manager.return_value = mock_instance

            response = client.post(
                "/api/chat",
                json={"messages": [{"role": "user", "content": "Help me choose"}]},
            )

            assert response.status_code == 200

            parts = parse_data_stream(response.text)
            codes = [p[0] for p in parts]

            # Verify AskUserQuestion tool events
            assert "b" in codes  # streaming start
            assert "9" in codes  # tool call

            # Verify questions are included
            tool_call = next(p[1] for p in parts if p[0] == "9")
            assert tool_call["toolName"] == "AskUserQuestion"
            assert "questions" in tool_call["args"]
            assert len(tool_call["args"]["questions"]) == 1
            assert tool_call["args"]["questions"][0]["header"] == "Color"

    def test_respond_endpoint_resumes_after_question(self, client: TestClient) -> None:
        """Verify /api/chat/respond continues paused session."""
        events = [
            StreamEvent(type="text", text="Great choice!", session_id="session-123"),
            StreamEvent(type="done", session_id="session-123", cost=0.001),
        ]

        with patch("src.api.routes.chat.get_agent_manager") as mock_manager:
            mock_instance = MagicMock()

            async def mock_respond(session_id: str, response: str):
                for event in events:
                    yield event

            mock_instance.respond_to_prompt = mock_respond
            mock_manager.return_value = mock_instance

            response = client.post(
                "/api/chat/respond",
                json={
                    "session_id": "session-123",
                    "response": '{"Which color do you prefer?": "Blue"}',
                },
            )

            assert response.status_code == 200

            parts = parse_data_stream(response.text)
            codes = [p[0] for p in parts]

            # Verify response continues with text and finish
            assert "0" in codes  # text
            assert "e" in codes  # finish step
            assert "d" in codes  # finish message


class TestErrorHandling:
    """Integration tests for error handling."""

    def test_error_response_format(self, client: TestClient) -> None:
        """Verify errors produce correct error event format (code 3)."""
        events = [
            StreamEvent(type="text", text="Processing...", session_id="session-123"),
            StreamEvent(
                type="error",
                text="Connection timeout",
                is_error=True,
                session_id="session-123",
            ),
        ]

        with patch("src.api.routes.chat.get_agent_manager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.stream_response = mock_stream_events(*events)
            mock_manager.return_value = mock_instance

            response = client.post(
                "/api/chat",
                json={"messages": [{"role": "user", "content": "Do something"}]},
            )

            assert response.status_code == 200

            parts = parse_data_stream(response.text)
            error_part = next((p for p in parts if p[0] == "3"), None)

            assert error_part is not None
            assert error_part[1] == "Connection timeout"

    def test_stream_exception_produces_error_event(self, client: TestClient) -> None:
        """Verify exceptions during streaming produce error events."""

        async def failing_stream(message: str, session_id: str | None = None):
            yield StreamEvent(type="text", text="Starting...", session_id="session-123")
            raise Exception("Network error")

        with patch("src.api.routes.chat.get_agent_manager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.stream_response = failing_stream
            mock_manager.return_value = mock_instance

            response = client.post(
                "/api/chat",
                json={"messages": [{"role": "user", "content": "Hello"}]},
            )

            parts = parse_data_stream(response.text)
            error_part = next((p for p in parts if p[0] == "3"), None)

            assert error_part is not None
            assert "Network error" in error_part[1]


class TestStreamEndsCorrectly:
    """Integration tests for stream termination."""

    def test_stream_ends_with_finish_messages(self, client: TestClient) -> None:
        """Verify stream ends with finish_step (e) and finish_message (d)."""
        events = [
            StreamEvent(type="text", text="Done", session_id="session-123"),
            StreamEvent(type="done", session_id="session-123"),
        ]

        with patch("src.api.routes.chat.get_agent_manager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.stream_response = mock_stream_events(*events)
            mock_manager.return_value = mock_instance

            response = client.post(
                "/api/chat",
                json={"messages": [{"role": "user", "content": "Hello"}]},
            )

            parts = parse_data_stream(response.text)
            codes = [p[0] for p in parts]

            # Verify finish events present
            assert "e" in codes
            assert "d" in codes

    def test_finish_step_before_finish_message(self, client: TestClient) -> None:
        """Verify finish_step (e) comes before finish_message (d)."""
        events = [
            StreamEvent(type="text", text="Response text", session_id="session-123"),
            StreamEvent(type="done", session_id="session-123"),
        ]

        with patch("src.api.routes.chat.get_agent_manager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.stream_response = mock_stream_events(*events)
            mock_manager.return_value = mock_instance

            response = client.post(
                "/api/chat",
                json={"messages": [{"role": "user", "content": "Hello"}]},
            )

            parts = parse_data_stream(response.text)
            codes = [p[0] for p in parts]

            # finish_step (e) should come before finish_message (d)
            e_idx = codes.index("e")
            d_idx = codes.index("d")
            assert e_idx < d_idx

    def test_finish_includes_usage(self, client: TestClient) -> None:
        """Verify finish events include usage information."""
        events = [
            StreamEvent(type="text", text="Done", session_id="session-123"),
            StreamEvent(type="done", session_id="session-123", cost=0.01),
        ]

        with patch("src.api.routes.chat.get_agent_manager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.stream_response = mock_stream_events(*events)
            mock_manager.return_value = mock_instance

            response = client.post(
                "/api/chat",
                json={"messages": [{"role": "user", "content": "Hello"}]},
            )

            parts = parse_data_stream(response.text)

            # Verify finish_step has usage
            finish_step = next(p[1] for p in parts if p[0] == "e")
            assert "usage" in finish_step
            assert "finishReason" in finish_step

            # Verify finish_message has usage
            finish_message = next(p[1] for p in parts if p[0] == "d")
            assert "usage" in finish_message
            assert "finishReason" in finish_message
