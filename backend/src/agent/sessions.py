"""Session management for multi-turn conversations.

Since ClaudeSDKClient cannot be reused across async contexts (FastAPI requests),
we store conversation history and pass it as context with each new query.
"""

import asyncio
import time
import uuid
from dataclasses import dataclass, field

from claude_code_sdk import ClaudeCodeOptions

from src.agent.options import get_default_options


@dataclass
class ConversationMessage:
    """A message in the conversation history."""

    role: str  # "user" or "assistant"
    content: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class SessionData:
    """Data for a conversation session."""

    session_id: str
    history: list[ConversationMessage] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_access: float = field(default_factory=time.time)
    waiting_for_user_input: bool = False


class SessionManager:
    """Manages conversation sessions with history storage."""

    def __init__(
        self,
        options: ClaudeCodeOptions | None = None,
        session_timeout_minutes: int = 30,
    ) -> None:
        """Initialize the session manager.

        Args:
            options: Claude SDK options to use for new sessions.
            session_timeout_minutes: Minutes before sessions expire.
        """
        self.options = options or get_default_options()
        self.session_timeout_seconds = session_timeout_minutes * 60
        self._sessions: dict[str, SessionData] = {}
        self._lock = asyncio.Lock()

    def generate_session_id(self) -> str:
        """Generate a new unique session ID."""
        return str(uuid.uuid4())

    async def get_or_create_session(self, session_id: str | None = None) -> SessionData:
        """Get an existing session or create a new one.

        Args:
            session_id: Session ID to look up, or None to create new.

        Returns:
            The session data.
        """
        async with self._lock:
            # Clean up expired sessions
            await self._cleanup_expired_sessions_locked()

            if session_id and session_id in self._sessions:
                session = self._sessions[session_id]
                session.last_access = time.time()
                return session

            # Create new session
            new_id = session_id or self.generate_session_id()
            session = SessionData(session_id=new_id)
            self._sessions[new_id] = session
            return session

    async def get_session(self, session_id: str) -> SessionData | None:
        """Get an existing session.

        Args:
            session_id: Session ID to look up.

        Returns:
            The session data, or None if not found.
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.last_access = time.time()
            return session

    async def add_message(
        self, session_id: str, role: str, content: str
    ) -> None:
        """Add a message to the session history.

        Args:
            session_id: Session ID.
            role: Message role ("user" or "assistant").
            content: Message content.
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.history.append(ConversationMessage(role=role, content=content))

    async def remove_session(self, session_id: str) -> bool:
        """Remove a session.

        Args:
            session_id: Session ID to remove.

        Returns:
            True if session was found and removed.
        """
        async with self._lock:
            return self._sessions.pop(session_id, None) is not None

    async def mark_waiting_for_input(self, session_id: str) -> None:
        """Mark a session as waiting for user input.

        Args:
            session_id: Session ID to mark.
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.waiting_for_user_input = True

    async def clear_waiting_for_input(self, session_id: str) -> None:
        """Clear the waiting-for-input flag on a session.

        Args:
            session_id: Session ID to update.
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.waiting_for_user_input = False

    async def _cleanup_expired_sessions_locked(self) -> None:
        """Remove expired sessions (must be called with lock held)."""
        now = time.time()
        expired = [
            sid
            for sid, session in self._sessions.items()
            if now - session.last_access > self.session_timeout_seconds
        ]
        for sid in expired:
            self._sessions.pop(sid, None)

    def list_sessions(self) -> list[str]:
        """List all active session IDs.

        Returns:
            List of session IDs.
        """
        return list(self._sessions.keys())

    def build_context_prompt(self, session: SessionData, new_message: str) -> str:
        """Build a prompt that includes conversation history.

        Args:
            session: The session data with history.
            new_message: The new user message.

        Returns:
            Prompt string with history context.
        """
        if not session.history:
            return new_message

        # Build conversation history as context
        history_parts = []
        for msg in session.history[-10:]:  # Last 10 messages for context
            role_label = "User" if msg.role == "user" else "Assistant"
            history_parts.append(f"{role_label}: {msg.content}")

        history_text = "\n".join(history_parts)
        return f"""Previous conversation:
{history_text}

User: {new_message}

Continue the conversation naturally, remembering the context above."""


# Global session manager instance
_session_manager: SessionManager | None = None


def get_session_manager() -> SessionManager:
    """Get the global session manager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
