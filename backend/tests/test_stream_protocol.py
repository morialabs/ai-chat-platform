"""Tests for AI SDK Data Stream protocol conversion.

Tests the protocol conversion from internal StreamEvent to AI SDK Data Stream Protocol.
See: https://ai-sdk.dev/docs/ai-sdk-ui/stream-protocol#data-stream-protocol
"""

import json

from src.agent.client import StreamEvent
from src.api.routes.chat import (
    DataStreamState,
    convert_to_data_stream,
    format_data_stream_part,
)


class TestDataStreamState:
    """Tests for DataStreamState tracking class."""

    def test_initial_state(self) -> None:
        """State starts with no session_id."""
        state = DataStreamState()
        assert state.session_id is None

    def test_generate_tool_id_creates_unique_id(self) -> None:
        """generate_tool_id() returns call-{uuid} format."""
        state = DataStreamState()
        tool_id = state.generate_tool_id()
        assert tool_id.startswith("call-")
        assert len(tool_id) > 5

    def test_generate_tool_id_creates_different_ids(self) -> None:
        """Each call to generate_tool_id() creates a different id."""
        state = DataStreamState()
        id1 = state.generate_tool_id()
        id2 = state.generate_tool_id()
        assert id1 != id2

    def test_session_id_tracking(self) -> None:
        """session_id is captured from events."""
        state = DataStreamState()
        event = StreamEvent(type="text", text="Hello", session_id="session-123")
        convert_to_data_stream(event, state)
        assert state.session_id == "session-123"


class TestFormatDataStreamPart:
    """Tests for format_data_stream_part function."""

    def test_text_format(self) -> None:
        """Text code 0 with string value."""
        result = format_data_stream_part("0", "Hello")
        assert result == '0:"Hello"\n'

    def test_error_format(self) -> None:
        """Error code 3 with string value."""
        result = format_data_stream_part("3", "Something went wrong")
        assert result == '3:"Something went wrong"\n'

    def test_object_format(self) -> None:
        """Object values are JSON serialized."""
        result = format_data_stream_part("9", {"toolCallId": "call-123", "toolName": "Read"})
        parsed = json.loads(result[2:-1])  # Remove "9:" and "\n"
        assert parsed["toolCallId"] == "call-123"
        assert parsed["toolName"] == "Read"

    def test_array_format(self) -> None:
        """Array values are JSON serialized."""
        result = format_data_stream_part("2", [{"key": "value"}])
        parsed = json.loads(result[2:-1])  # Remove "2:" and "\n"
        assert parsed == [{"key": "value"}]

    def test_special_characters_escaped(self) -> None:
        """Special chars in strings are JSON escaped."""
        result = format_data_stream_part("0", 'Line1\nLine2\t"quoted"')
        # Should be valid, parseable JSON
        json_str = result[2:-1]  # Remove "0:" and "\n"
        parsed = json.loads(json_str)
        assert parsed == 'Line1\nLine2\t"quoted"'

    def test_unicode_characters(self) -> None:
        """Unicode characters are handled correctly."""
        result = format_data_stream_part("0", "Hello 世界 🌍")
        json_str = result[2:-1]
        parsed = json.loads(json_str)
        assert parsed == "Hello 世界 🌍"


class TestTextEventConversion:
    """Tests for text event conversion to Data Stream protocol."""

    def test_text_emits_code_0(self) -> None:
        """Text event emits code 0."""
        state = DataStreamState()
        event = StreamEvent(type="text", text="Hello")
        parts = convert_to_data_stream(event, state)

        assert len(parts) == 1
        assert parts[0].startswith("0:")

    def test_text_content_included(self) -> None:
        """Text content is JSON encoded string."""
        state = DataStreamState()
        event = StreamEvent(type="text", text="Hello world")
        parts = convert_to_data_stream(event, state)

        json_str = parts[0][2:-1]  # Remove "0:" and "\n"
        parsed = json.loads(json_str)
        assert parsed == "Hello world"

    def test_multiple_text_events(self) -> None:
        """Multiple text events each emit their own part."""
        state = DataStreamState()

        event1 = StreamEvent(type="text", text="Hello")
        parts1 = convert_to_data_stream(event1, state)
        assert len(parts1) == 1

        event2 = StreamEvent(type="text", text=" world")
        parts2 = convert_to_data_stream(event2, state)
        assert len(parts2) == 1

    def test_empty_text_no_emit(self) -> None:
        """Empty text string doesn't emit anything."""
        state = DataStreamState()
        event = StreamEvent(type="text", text="")
        parts = convert_to_data_stream(event, state)

        assert len(parts) == 0


class TestToolStartConversion:
    """Tests for tool_start event conversion."""

    def test_tool_start_emits_code_b_and_9(self) -> None:
        """tool_start emits streaming start (b) and tool call (9)."""
        state = DataStreamState()
        event = StreamEvent(
            type="tool_start",
            tool_name="Read",
            tool_id="tool-123",
            tool_input={"file_path": "/test.txt"},
        )
        parts = convert_to_data_stream(event, state)

        assert len(parts) == 2
        assert parts[0].startswith("b:")
        assert parts[1].startswith("9:")

    def test_tool_start_streaming_start_content(self) -> None:
        """Code b includes toolCallId and toolName."""
        state = DataStreamState()
        event = StreamEvent(
            type="tool_start",
            tool_name="Read",
            tool_id="tool-123",
            tool_input={"file_path": "/test.txt"},
        )
        parts = convert_to_data_stream(event, state)

        parsed = json.loads(parts[0][2:-1])
        assert parsed["toolCallId"] == "tool-123"
        assert parsed["toolName"] == "Read"

    def test_tool_start_call_content(self) -> None:
        """Code 9 includes toolCallId, toolName, and args."""
        state = DataStreamState()
        event = StreamEvent(
            type="tool_start",
            tool_name="Read",
            tool_id="tool-123",
            tool_input={"file_path": "/test.txt"},
        )
        parts = convert_to_data_stream(event, state)

        parsed = json.loads(parts[1][2:-1])
        assert parsed["toolCallId"] == "tool-123"
        assert parsed["toolName"] == "Read"
        assert parsed["args"] == {"file_path": "/test.txt"}

    def test_tool_input_handles_none(self) -> None:
        """tool_input=None becomes empty dict."""
        state = DataStreamState()
        event = StreamEvent(
            type="tool_start",
            tool_name="Read",
            tool_id="tool-123",
            tool_input=None,
        )
        parts = convert_to_data_stream(event, state)

        parsed = json.loads(parts[1][2:-1])
        assert parsed["args"] == {}


class TestToolResultConversion:
    """Tests for tool_result event conversion."""

    def test_tool_result_emits_code_a(self) -> None:
        """tool_result emits code a."""
        state = DataStreamState()
        event = StreamEvent(
            type="tool_result",
            tool_id="tool-123",
            tool_result="File contents",
            is_error=False,
        )
        parts = convert_to_data_stream(event, state)

        assert len(parts) == 1
        assert parts[0].startswith("a:")

    def test_tool_result_includes_result(self) -> None:
        """Result includes toolCallId and result."""
        state = DataStreamState()
        event = StreamEvent(
            type="tool_result",
            tool_id="tool-123",
            tool_result="File contents here",
            is_error=False,
        )
        parts = convert_to_data_stream(event, state)

        parsed = json.loads(parts[0][2:-1])
        assert parsed["toolCallId"] == "tool-123"
        assert parsed["result"] == "File contents here"

    def test_tool_result_error_wraps_in_error_object(self) -> None:
        """is_error=True wraps result in error object."""
        state = DataStreamState()
        event = StreamEvent(
            type="tool_result",
            tool_id="tool-123",
            tool_result="Error: file not found",
            is_error=True,
        )
        parts = convert_to_data_stream(event, state)

        parsed = json.loads(parts[0][2:-1])
        assert parsed["toolCallId"] == "tool-123"
        assert parsed["result"] == {"error": "Error: file not found"}


class TestUserInputRequiredConversion:
    """Tests for user_input_required event conversion."""

    def test_user_input_emits_code_b_and_9(self) -> None:
        """user_input_required emits as AskUserQuestion tool call."""
        state = DataStreamState()
        questions = [{"question": "What color?", "options": [{"label": "Red"}]}]
        event = StreamEvent(
            type="user_input_required",
            tool_id="ask-123",
            questions=questions,
        )
        parts = convert_to_data_stream(event, state)

        assert len(parts) == 2
        assert parts[0].startswith("b:")
        assert parts[1].startswith("9:")

    def test_user_input_uses_ask_user_question_name(self) -> None:
        """Tool name is AskUserQuestion."""
        state = DataStreamState()
        questions = [{"question": "What color?", "options": [{"label": "Red"}]}]
        event = StreamEvent(
            type="user_input_required",
            tool_id="ask-123",
            questions=questions,
        )
        parts = convert_to_data_stream(event, state)

        parsed = json.loads(parts[0][2:-1])
        assert parsed["toolName"] == "AskUserQuestion"

    def test_user_input_includes_questions_in_args(self) -> None:
        """Questions are included in args."""
        state = DataStreamState()
        questions = [{"question": "What color?", "options": [{"label": "Red"}, {"label": "Blue"}]}]
        event = StreamEvent(
            type="user_input_required",
            tool_id="ask-123",
            questions=questions,
        )
        parts = convert_to_data_stream(event, state)

        parsed = json.loads(parts[1][2:-1])
        assert parsed["args"]["questions"] == questions

    def test_user_input_merges_tool_input(self) -> None:
        """Merges tool_input with questions."""
        state = DataStreamState()
        questions = [{"question": "Pick one", "options": []}]
        event = StreamEvent(
            type="user_input_required",
            tool_id="ask-123",
            questions=questions,
            tool_input={"metadata": "extra"},
        )
        parts = convert_to_data_stream(event, state)

        parsed = json.loads(parts[1][2:-1])
        assert parsed["args"]["questions"] == questions
        assert parsed["args"]["metadata"] == "extra"


class TestDoneEventConversion:
    """Tests for done event conversion."""

    def test_done_emits_codes_e_d_and_2(self) -> None:
        """done emits finish_step (e), finish_message (d), and data (2)."""
        state = DataStreamState()
        event = StreamEvent(type="done", session_id="session-123", cost=0.001)
        parts = convert_to_data_stream(event, state)

        assert len(parts) == 3
        assert parts[0].startswith("e:")
        assert parts[1].startswith("d:")
        assert parts[2].startswith("2:")

    def test_done_finish_step_content(self) -> None:
        """Finish step (e) includes finishReason, usage, isContinued."""
        state = DataStreamState()
        event = StreamEvent(type="done", session_id="session-123", cost=0.001)
        parts = convert_to_data_stream(event, state)

        parsed = json.loads(parts[0][2:-1])
        assert parsed["finishReason"] == "stop"
        assert "usage" in parsed
        assert parsed["isContinued"] is False

    def test_done_finish_message_content(self) -> None:
        """Finish message (d) includes finishReason and usage."""
        state = DataStreamState()
        event = StreamEvent(type="done", session_id="session-123", cost=0.001)
        parts = convert_to_data_stream(event, state)

        parsed = json.loads(parts[1][2:-1])
        assert parsed["finishReason"] == "stop"
        assert "usage" in parsed

    def test_done_includes_session_data(self) -> None:
        """Data (2) includes session_id and cost."""
        state = DataStreamState()
        event = StreamEvent(type="done", session_id="session-123", cost=0.0025)
        parts = convert_to_data_stream(event, state)

        parsed = json.loads(parts[2][2:-1])
        assert isinstance(parsed, list)
        assert parsed[0]["session_id"] == "session-123"
        assert parsed[0]["cost"] == 0.0025

    def test_done_without_session_no_data(self) -> None:
        """done without session_id doesn't emit data (2)."""
        state = DataStreamState()
        event = StreamEvent(type="done", session_id=None)
        parts = convert_to_data_stream(event, state)

        # Should only have finish_step and finish_message
        assert len(parts) == 2
        assert parts[0].startswith("e:")
        assert parts[1].startswith("d:")


class TestErrorEventConversion:
    """Tests for error event conversion."""

    def test_error_emits_code_3(self) -> None:
        """error emits code 3."""
        state = DataStreamState()
        event = StreamEvent(type="error", text="Connection failed", is_error=True)
        parts = convert_to_data_stream(event, state)

        assert len(parts) == 1
        assert parts[0].startswith("3:")

    def test_error_includes_message(self) -> None:
        """Error message is the value."""
        state = DataStreamState()
        event = StreamEvent(type="error", text="Connection failed", is_error=True)
        parts = convert_to_data_stream(event, state)

        parsed = json.loads(parts[0][2:-1])
        assert parsed == "Connection failed"

    def test_error_handles_none_text(self) -> None:
        """error with text=None uses 'Unknown error'."""
        state = DataStreamState()
        event = StreamEvent(type="error", text=None, is_error=True)
        parts = convert_to_data_stream(event, state)

        parsed = json.loads(parts[0][2:-1])
        assert parsed == "Unknown error"


class TestStreamSequence:
    """Tests for complete stream sequences."""

    def test_text_only_sequence(self) -> None:
        """Simple text response sequence."""
        state = DataStreamState()

        # Text chunks
        parts1 = convert_to_data_stream(StreamEvent(type="text", text="Hello"), state)
        parts2 = convert_to_data_stream(StreamEvent(type="text", text=" world"), state)
        parts3 = convert_to_data_stream(
            StreamEvent(type="done", session_id="sess-1", cost=0.01), state
        )

        # Verify sequence
        assert parts1[0].startswith("0:")
        assert parts2[0].startswith("0:")
        assert parts3[0].startswith("e:")
        assert parts3[1].startswith("d:")

    def test_tool_call_sequence(self) -> None:
        """Tool call followed by result sequence."""
        state = DataStreamState()

        # Tool start
        parts1 = convert_to_data_stream(
            StreamEvent(
                type="tool_start",
                tool_name="Read",
                tool_id="tool-1",
                tool_input={"path": "/test"},
            ),
            state,
        )

        # Tool result
        parts2 = convert_to_data_stream(
            StreamEvent(
                type="tool_result",
                tool_id="tool-1",
                tool_result="contents",
                is_error=False,
            ),
            state,
        )

        # Done
        parts3 = convert_to_data_stream(StreamEvent(type="done", session_id="sess-1"), state)

        # Verify codes
        assert parts1[0].startswith("b:")  # streaming start
        assert parts1[1].startswith("9:")  # tool call
        assert parts2[0].startswith("a:")  # tool result
        assert parts3[0].startswith("e:")  # finish step
