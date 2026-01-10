"""Agent configuration options."""

from claude_code_sdk import ClaudeCodeOptions

from src.agent.hooks import create_hooks
from src.config import settings


def get_default_options(*, include_hooks: bool = True) -> ClaudeCodeOptions:
    """Create default agent options."""
    return ClaudeCodeOptions(
        # Core settings
        model=settings.model,
        cwd=str(settings.workspace_dir),
        # Permission mode - acceptEdits allows file operations without prompting
        permission_mode="acceptEdits",
        # Built-in tools to allow
        allowed_tools=[
            "Read",
            "Write",
            "Edit",
            "Bash",
            "Glob",
            "Grep",
            "WebSearch",
            "WebFetch",
            "Task",
        ],
        # System prompt customization
        append_system_prompt=f"""
You are an AI assistant for {settings.app_name}.
Be helpful, concise, and accurate in your responses.
""",
        # Hooks for validation and logging
        hooks=create_hooks() if include_hooks else None,
    )
