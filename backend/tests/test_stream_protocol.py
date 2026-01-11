"""Tests for Vercel AI SDK stream protocol conversion.

Tests the SSE protocol conversion from internal StreamEvent to Vercel UI Message Stream Protocol.
"""

import json

import pytest

from src.agent.client import StreamEvent
from src.api.routes.chat import (
    VercelStreamState,
    convert_to_vercel_events,
    vercel_event_to_sse,
)


class TestVercelStreamState:
    """Tests for VercelStreamState tracking class."""

    def test_initial_state(self) -> None:
        """State starts with no text_id, text_started=False."""
        state = VercelStreamState()
        assert state.text_id is None
        assert state.text_started is False
        assert state.session_id is None

    def test_generate_text_id_creates_unique_id(self) -> None:
        """generate_text_id() returns text-{uuid} format."""
        state = VercelStreamState()
        text_id = state.generate_text_id()
        assert text_id.startswith("text-")
        assert len(text_id) > 5  # text- plus some uuid chars

    def test_generate_text_id_updates_state(self) -> None:
        """generate_text_id() sets self.text_id."""
        state = VercelStreamState()
        text_id = state.generate_text_id()
        assert state.text_id == text_id

    def test_generate_text_id_creates_different_ids(self) -> None:
        """Each call to generate_text_id() creates a different id."""
        state1 = VercelStreamState()
        state2 = VercelStreamState()
        id1 = state1.generate_text_id()
        id2 = state2.generate_text_id()
        assert id1 != id2

    def test_session_id_tracking(self) -> None:
        """session_id is captured from events."""
        state = VercelStreamState()
        event = StreamEvent(type="text", text="Hello", session_id="session-123")
        convert_to_vercel_events(event, state)
        assert state.session_id == "session-123"


class TestTextEventConversion:
    """Tests for text event conversion to Vercel protocol."""

    def test_first_text_emits_text_start(self) -> None:
        """First text event emits text-start before text-delta."""
        state = VercelStreamState()
        event = StreamEvent(type="text", text="Hello")
        events = convert_to_vercel_events(event, state)

        assert len(events) == 2
        assert events[0]["type"] == "text-start"
        assert "id" in events[0]
        assert events[1]["type"] == "text-delta"

    def test_text_delta_includes_content(self) -> None:
        """text-delta event includes id and delta fields."""
        state = VercelStreamState()
        event = StreamEvent(type="text", text="Hello world")
        events = convert_to_vercel_events(event, state)

        text_delta = events[1]
        assert text_delta["type"] == "text-delta"
        assert text_delta["delta"] == "Hello world"
        assert "id" in text_delta

    def test_multiple_text_events_no_duplicate_start(self) -> None:
        """Subsequent text events don't emit text-start again."""
        state = VercelStreamState()

        # First text
        event1 = StreamEvent(type="text", text="Hello")
        events1 = convert_to_vercel_events(event1, state)
        assert len(events1) == 2
        assert events1[0]["type"] == "text-start"

        # Second text - should only emit delta
        event2 = StreamEvent(type="text", text=" world")
        events2 = convert_to_vercel_events(event2, state)
        assert len(events2) == 1
        assert events2[0]["type"] == "text-delta"

    def test_empty_text_still_tracked(self) -> None:
        """Empty text string still starts text block."""
        state = VercelStreamState()
        event = StreamEvent(type="text", text="")
        events = convert_to_vercel_events(event, state)

        # Should emit text-start but no delta for empty text
        assert len(events) == 1
        assert events[0]["type"] == "text-start"
        assert state.text_started is True

    def test_text_id_consistent_across_deltas(self) -> None:
        """All text-delta events use same id."""
        state = VercelStreamState()

        event1 = StreamEvent(type="text", text="Hello")
        events1 = convert_to_vercel_events(event1, state)
        text_id = events1[0]["id"]

        event2 = StreamEvent(type="text", text=" world")
        events2 = convert_to_vercel_events(event2, state)

        assert events2[0]["id"] == text_id


class TestToolStartConversion:
    """Tests for tool_start event conversion."""

    def test_tool_start_ends_text_block(self) -> None:
        """tool_start emits text-end if text was streaming."""
        state = VercelStreamState()

        # Start text streaming
        text_event = StreamEvent(type="text", text="Thinking...")
        convert_to_vercel_events(text_event, state)
        text_id = state.text_id

        # Tool start should end text block
        tool_event = StreamEvent(
            type="tool_start",
            tool_name="Read",
            tool_id="tool-123",
            tool_input={"file_path": "/test.txt"},
        )
        events = convert_to_vercel_events(tool_event, state)

        assert events[0]["type"] == "text-end"
        assert events[0]["id"] == text_id

    def test_tool_start_emits_input_start(self) -> None:
        """tool_start emits tool-input-start with toolCallId, toolName."""
        state = VercelStreamState()
        event = StreamEvent(
            type="tool_start",
            tool_name="Read",
            tool_id="tool-123",
            tool_input={"file_path": "/test.txt"},
        )
        events = convert_to_vercel_events(event, state)

        input_start = next(e for e in events if e["type"] == "tool-input-start")
        assert input_start["toolCallId"] == "tool-123"
        assert input_start["toolName"] == "Read"

    def test_tool_start_emits_input_available(self) -> None:
        """tool_start emits tool-input-available with input object."""
        state = VercelStreamState()
        event = StreamEvent(
            type="tool_start",
            tool_name="Read",
            tool_id="tool-123",
            tool_input={"file_path": "/test.txt"},
        )
        events = convert_to_vercel_events(event, state)

        input_available = next(e for e in events if e["type"] == "tool-input-available")
        assert input_available["toolCallId"] == "tool-123"
        assert input_available["toolName"] == "Read"
        assert input_available["input"] == {"file_path": "/test.txt"}

    def test_tool_start_without_prior_text(self) -> None:
        """tool_start without text doesn't emit text-end."""
        state = VercelStreamState()
        event = StreamEvent(
            type="tool_start",
            tool_name="Read",
            tool_id="tool-123",
            tool_input={},
        )
        events = convert_to_vercel_events(event, state)

        # Should only have tool events, no text-end
        assert all(e["type"].startswith("tool-") for e in events)

    def test_tool_input_handles_none(self) -> None:
        """tool_input=None becomes empty dict."""
        state = VercelStreamState()
        event = StreamEvent(
            type="tool_start",
            tool_name="Read",
            tool_id="tool-123",
            tool_input=None,
        )
        events = convert_to_vercel_events(event, state)

        input_available = next(e for e in events if e["type"] == "tool-input-available")
        assert input_available["input"] == {}


class TestToolResultConversion:
    """Tests for tool_result event conversion."""

    def test_tool_result_emits_output_available(self) -> None:
        """tool_result emits tool-output-available."""
        state = VercelStreamState()
        event = StreamEvent(
            type="tool_result",
            tool_id="tool-123",
            tool_result="File contents",
            is_error=False,
        )
        events = convert_to_vercel_events(event, state)

        assert len(events) == 1
        assert events[0]["type"] == "tool-output-available"

    def test_tool_result_includes_result(self) -> None:
        """output includes result field."""
        state = VercelStreamState()
        event = StreamEvent(
            type="tool_result",
            tool_id="tool-123",
            tool_result="File contents here",
            is_error=False,
        )
        events = convert_to_vercel_events(event, state)

        assert events[0]["output"]["result"] == "File contents here"

    def test_tool_result_includes_is_error(self) -> None:
        """output includes isError field."""
        state = VercelStreamState()
        event = StreamEvent(
            type="tool_result",
            tool_id="tool-123",
            tool_result="Success",
            is_error=False,
        )
        events = convert_to_vercel_events(event, state)

        assert events[0]["output"]["isError"] is False

    def test_tool_result_error_true(self) -> None:
        """is_error=True sets isError=True."""
        state = VercelStreamState()
        event = StreamEvent(
            type="tool_result",
            tool_id="tool-123",
            tool_result="Error: file not found",
            is_error=True,
        )
        events = convert_to_vercel_events(event, state)

        assert events[0]["output"]["isError"] is True
        assert events[0]["toolCallId"] == "tool-123"


class TestUserInputRequiredConversion:
    """Tests for user_input_required event conversion."""

    def test_user_input_ends_text_block(self) -> None:
        """user_input_required ends any ongoing text."""
        state = VercelStreamState()

        # Start text streaming
        text_event = StreamEvent(type="text", text="I have a question")
        convert_to_vercel_events(text_event, state)

        # User input required should end text
        questions = [{"question": "What color?", "options": [{"label": "Red"}]}]
        user_input_event = StreamEvent(
            type="user_input_required",
            tool_id="ask-123",
            questions=questions,
        )
        events = convert_to_vercel_events(user_input_event, state)

        assert events[0]["type"] == "text-end"

    def test_user_input_emits_ask_user_question(self) -> None:
        """Emits tool events with toolName='AskUserQuestion'."""
        state = VercelStreamState()
        questions = [{"question": "What color?", "options": [{"label": "Red"}]}]
        event = StreamEvent(
            type="user_input_required",
            tool_id="ask-123",
            questions=questions,
        )
        events = convert_to_vercel_events(event, state)

        input_start = next(e for e in events if e["type"] == "tool-input-start")
        assert input_start["toolName"] == "AskUserQuestion"

    def test_user_input_includes_questions(self) -> None:
        """input includes questions array."""
        state = VercelStreamState()
        questions = [
            {"question": "What color?", "options": [{"label": "Red"}, {"label": "Blue"}]}
        ]
        event = StreamEvent(
            type="user_input_required",
            tool_id="ask-123",
            questions=questions,
        )
        events = convert_to_vercel_events(event, state)

        input_available = next(e for e in events if e["type"] == "tool-input-available")
        assert input_available["input"]["questions"] == questions

    def test_user_input_merges_tool_input(self) -> None:
        """Merges tool_input with questions."""
        state = VercelStreamState()
        questions = [{"question": "Pick one", "options": []}]
        event = StreamEvent(
            type="user_input_required",
            tool_id="ask-123",
            questions=questions,
            tool_input={"metadata": "extra"},
        )
        events = convert_to_vercel_events(event, state)

        input_available = next(e for e in events if e["type"] == "tool-input-available")
        assert input_available["input"]["questions"] == questions
        assert input_available["input"]["metadata"] == "extra"


class TestDoneEventConversion:
    """Tests for done event conversion."""

    def test_done_ends_text_block(self) -> None:
        """done event emits text-end if text was streaming."""
        state = VercelStreamState()

        # Start text streaming
        text_event = StreamEvent(type="text", text="Final response")
        convert_to_vercel_events(text_event, state)
        text_id = state.text_id

        # Done should end text block
        done_event = StreamEvent(type="done", session_id="session-123", cost=0.001)
        events = convert_to_vercel_events(done_event, state)

        assert events[0]["type"] == "text-end"
        assert events[0]["id"] == text_id

    def test_done_emits_finish(self) -> None:
        """done emits finish event."""
        state = VercelStreamState()
        event = StreamEvent(type="done", session_id="session-123", cost=0.001)
        events = convert_to_vercel_events(event, state)

        finish = next(e for e in events if e["type"] == "finish")
        assert finish["type"] == "finish"

    def test_done_includes_metadata(self) -> None:
        """finish includes metadata with session_id and cost."""
        state = VercelStreamState()
        event = StreamEvent(type="done", session_id="session-123", cost=0.0025)
        events = convert_to_vercel_events(event, state)

        finish = next(e for e in events if e["type"] == "finish")
        assert finish["metadata"]["session_id"] == "session-123"
        assert finish["metadata"]["cost"] == 0.0025

    def test_done_without_text(self) -> None:
        """done without prior text doesn't emit text-end."""
        state = VercelStreamState()
        event = StreamEvent(type="done", session_id="session-123")
        events = convert_to_vercel_events(event, state)

        # Should only have finish event
        assert len(events) == 1
        assert events[0]["type"] == "finish"


class TestErrorEventConversion:
    """Tests for error event conversion."""

    def test_error_ends_text_block(self) -> None:
        """error ends any ongoing text block."""
        state = VercelStreamState()

        # Start text streaming
        text_event = StreamEvent(type="text", text="Working...")
        convert_to_vercel_events(text_event, state)

        # Error should end text
        error_event = StreamEvent(type="error", text="Something went wrong", is_error=True)
        events = convert_to_vercel_events(error_event, state)

        assert events[0]["type"] == "text-end"

    def test_error_emits_error_event(self) -> None:
        """error emits error event with errorText."""
        state = VercelStreamState()
        event = StreamEvent(type="error", text="Connection failed", is_error=True)
        events = convert_to_vercel_events(event, state)

        error = next(e for e in events if e["type"] == "error")
        assert error["errorText"] == "Connection failed"

    def test_error_handles_none_text(self) -> None:
        """error with text=None uses 'Unknown error'."""
        state = VercelStreamState()
        event = StreamEvent(type="error", text=None, is_error=True)
        events = convert_to_vercel_events(event, state)

        error = next(e for e in events if e["type"] == "error")
        assert error["errorText"] == "Unknown error"


class TestVercelEventToSSE:
    """Tests for vercel_event_to_sse SSE formatting."""

    def test_sse_format(self) -> None:
        """Output is 'data: {json}\\n\\n'."""
        event = {"type": "text-delta", "id": "text-1", "delta": "Hello"}
        sse = vercel_event_to_sse(event)

        assert sse.startswith("data: ")
        assert sse.endswith("\n\n")

    def test_json_encoding(self) -> None:
        """Event dict is properly JSON encoded."""
        event = {"type": "text-delta", "id": "text-1", "delta": "Hello"}
        sse = vercel_event_to_sse(event)

        # Extract JSON from SSE
        json_str = sse[6:-2]  # Remove "data: " prefix and "\n\n" suffix
        parsed = json.loads(json_str)

        assert parsed == event

    def test_special_characters_escaped(self) -> None:
        """Special chars in text are JSON escaped."""
        event = {"type": "text-delta", "delta": 'Line1\nLine2\t"quoted"'}
        sse = vercel_event_to_sse(event)

        # Should be valid JSON
        json_str = sse[6:-2]
        parsed = json.loads(json_str)
        assert parsed["delta"] == 'Line1\nLine2\t"quoted"'

    def test_unicode_characters(self) -> None:
        """Unicode characters are handled correctly."""
        event = {"type": "text-delta", "delta": "Hello 世界 🌍"}
        sse = vercel_event_to_sse(event)

        json_str = sse[6:-2]
        parsed = json.loads(json_str)
        assert parsed["delta"] == "Hello 世界 🌍"

    def test_nested_objects(self) -> None:
        """Nested objects are serialized correctly."""
        event = {
            "type": "tool-input-available",
            "toolCallId": "tool-1",
            "input": {"nested": {"deep": "value"}, "array": [1, 2, 3]},
        }
        sse = vercel_event_to_sse(event)

        json_str = sse[6:-2]
        parsed = json.loads(json_str)
        assert parsed["input"]["nested"]["deep"] == "value"
        assert parsed["input"]["array"] == [1, 2, 3]
