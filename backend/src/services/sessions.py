"""Session management for ClaudeSDKClient instances."""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

from src.agent.exceptions import SessionNotFoundError

logger = logging.getLogger(__name__)


class SessionState(Enum):
    """States for a managed session."""

    ACTIVE = "active"  # Ready for queries
    STREAMING = "streaming"  # Currently streaming response
    WAITING_INPUT = "waiting_input"  # AskUserQuestion pending
    COMPLETED = "completed"  # Session ended normally
    ERROR = "error"  # Session in error state


@dataclass
class ManagedSession:
    """A managed ClaudeSDKClient session with metadata."""

    client: ClaudeSDKClient
    session_id: str
    options: ClaudeAgentOptions
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_accessed: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    state: SessionState = SessionState.ACTIVE
    user_id: str | None = None
    # Claude Code SDK session ID (returned in ResultMessage)
    sdk_session_id: str = "default"

    def touch(self) -> None:
        """Update last_accessed timestamp."""
        self.last_accessed = datetime.now(timezone.utc)

    def is_expired(self, ttl_seconds: int) -> bool:
        """Check if session has expired based on TTL."""
        now = datetime.now(timezone.utc)
        age_seconds = (now - self.last_accessed).total_seconds()
        return age_seconds > ttl_seconds


class SessionManager:
    """Manages ClaudeSDKClient sessions with lifecycle handling.

    Thread-safe session management with TTL-based expiration.
    """

    def __init__(self, ttl_seconds: int = 3600) -> None:
        """Initialize the session manager.

        Args:
            ttl_seconds: Time-to-live for sessions in seconds (default: 1 hour).
        """
        self._sessions: dict[str, ManagedSession] = {}
        self._lock = asyncio.Lock()
        self._ttl_seconds = ttl_seconds

    async def create_session(
        self,
        options: ClaudeAgentOptions,
        user_id: str | None = None,
    ) -> ManagedSession:
        """Create a new session with ClaudeSDKClient.

        Args:
            options: Configuration options for the Claude agent.
            user_id: Optional user identifier for the session.

        Returns:
            The created ManagedSession.
        """
        session_id = str(uuid.uuid4())

        # Create and connect the client
        client = ClaudeSDKClient(options=options)
        await client.connect()

        session = ManagedSession(
            client=client,
            session_id=session_id,
            options=options,
            user_id=user_id,
        )

        async with self._lock:
            self._sessions[session_id] = session

        logger.info(f"Created session {session_id}")
        return session

    async def get_session(self, session_id: str) -> ManagedSession | None:
        """Retrieve an existing session.

        Args:
            session_id: The session ID to look up.

        Returns:
            The ManagedSession if found and not expired, None otherwise.
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None

            if session.is_expired(self._ttl_seconds):
                # Clean up expired session
                await self._cleanup_session(session)
                del self._sessions[session_id]
                logger.info(f"Session {session_id} expired and cleaned up")
                return None

            session.touch()
            return session

    async def delete_session(self, session_id: str) -> bool:
        """Explicitly delete a session.

        Args:
            session_id: The session ID to delete.

        Returns:
            True if session was found and deleted, False otherwise.
        """
        async with self._lock:
            session = self._sessions.pop(session_id, None)
            if session is None:
                return False

            await self._cleanup_session(session)
            logger.info(f"Deleted session {session_id}")
            return True

    async def cleanup_expired(self) -> int:
        """Remove sessions older than TTL.

        Returns:
            Number of sessions removed.
        """
        expired_ids: list[str] = []

        async with self._lock:
            for session_id, session in self._sessions.items():
                if session.is_expired(self._ttl_seconds):
                    expired_ids.append(session_id)

            for session_id in expired_ids:
                session = self._sessions.pop(session_id)
                await self._cleanup_session(session)

        if expired_ids:
            logger.info(f"Cleaned up {len(expired_ids)} expired sessions")
        return len(expired_ids)

    async def cleanup_all(self) -> int:
        """Clean up all sessions (for shutdown).

        Returns:
            Number of sessions cleaned up.
        """
        async with self._lock:
            count = len(self._sessions)
            for session in self._sessions.values():
                await self._cleanup_session(session)
            self._sessions.clear()

        logger.info(f"Cleaned up all {count} sessions")
        return count

    async def _cleanup_session(self, session: ManagedSession) -> None:
        """Clean up a single session's resources.

        Args:
            session: The session to clean up.
        """
        try:
            await session.client.disconnect()
        except Exception as e:
            logger.warning(f"Error disconnecting session {session.session_id}: {e}")

    def get_session_count(self) -> int:
        """Get the current number of active sessions."""
        return len(self._sessions)

    async def set_session_state(self, session_id: str, state: SessionState) -> None:
        """Update the state of a session.

        Args:
            session_id: The session ID to update.
            state: The new state.

        Raises:
            SessionNotFoundError: If session is not found.
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise SessionNotFoundError(f"Session {session_id} not found")
            session.state = state
            session.touch()
