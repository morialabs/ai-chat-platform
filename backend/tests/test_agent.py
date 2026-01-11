"""Test agent module."""

from src.agent.client import AgentManager, AgentRunner, StreamEvent
from src.agent.options import get_default_options


def test_agent_manager_instantiates() -> None:
    """Verify AgentManager can be created."""
    manager = AgentManager()
    assert manager is not None
    assert manager.session_manager is not None


def test_agent_runner_backward_compatible() -> None:
    """Verify AgentRunner alias still works."""
    runner = AgentRunner()
    assert runner is not None
    assert isinstance(runner, AgentManager)


def test_default_options_valid() -> None:
    """Verify default options have expected values."""
    options = get_default_options()
    assert options.permission_mode == "bypassPermissions"
    assert "Read" in options.allowed_tools
    assert "Write" in options.allowed_tools
    assert "Bash" in options.allowed_tools


def test_stream_event_text() -> None:
    """Verify StreamEvent can represent text."""
    event = StreamEvent(type="text", text="Hello, world!")
    assert event.type == "text"
    assert event.text == "Hello, world!"


def test_stream_event_tool_start() -> None:
    """Verify StreamEvent can represent tool start."""
    event = StreamEvent(
        type="tool_start",
        tool_name="Read",
        tool_id="123",
        tool_input={"file_path": "/test.txt"},
    )
    assert event.type == "tool_start"
    assert event.tool_name == "Read"
    assert event.tool_id == "123"


def test_stream_event_done() -> None:
    """Verify StreamEvent can represent completion."""
    event = StreamEvent(
        type="done",
        session_id="session-123",
        cost=0.0025,
    )
    assert event.type == "done"
    assert event.session_id == "session-123"
    assert event.cost == 0.0025


def test_stream_event_user_input_required() -> None:
    """Verify StreamEvent can represent user input request."""
    questions = [{"question": "What color?", "options": ["Red", "Blue"]}]
    event = StreamEvent(
        type="user_input_required",
        tool_name="AskUserQuestion",
        tool_id="ask-123",
        questions=questions,
    )
    assert event.type == "user_input_required"
    assert event.questions == questions


def test_stream_event_tool_result() -> None:
    """Verify StreamEvent can represent tool result."""
    event = StreamEvent(
        type="tool_result",
        tool_id="123",
        tool_result="File contents here",
        is_error=False,
    )
    assert event.type == "tool_result"
    assert event.tool_result == "File contents here"
    assert event.is_error is False
