"""Test agent module."""

from src.agent.client import AgentRunner, StreamEvent
from src.agent.options import get_default_options


def test_agent_runner_instantiates() -> None:
    """Verify AgentRunner can be created."""
    runner = AgentRunner()
    assert runner is not None
    assert runner.options is not None


def test_agent_runner_with_custom_options() -> None:
    """Verify AgentRunner accepts custom options."""
    options = get_default_options()
    runner = AgentRunner(options=options)
    assert runner.options == options


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
