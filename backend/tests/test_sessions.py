"""Tests for session management."""

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agent.exceptions import SessionNotFoundError
from src.services.sessions import ManagedSession, SessionManager, SessionState


@pytest.fixture
def session_manager() -> SessionManager:
    """Create a session manager with short TTL for testing."""
    return SessionManager(ttl_seconds=60)


class TestManagedSession:
    """Tests for ManagedSession dataclass."""

    def test_touch_updates_last_accessed(self) -> None:
        """Verify touch() updates the last_accessed timestamp."""
        mock_client = MagicMock()
        session = ManagedSession(
            client=mock_client,
            session_id="test-123",
            options=MagicMock(),
        )
        original_time = session.last_accessed
        session.touch()
        assert session.last_accessed >= original_time

    def test_is_expired_false_when_fresh(self) -> None:
        """Verify is_expired returns False for fresh session."""
        mock_client = MagicMock()
        session = ManagedSession(
            client=mock_client,
            session_id="test-123",
            options=MagicMock(),
        )
        assert session.is_expired(ttl_seconds=3600) is False

    def test_is_expired_true_when_old(self) -> None:
        """Verify is_expired returns True for old session."""
        mock_client = MagicMock()
        session = ManagedSession(
            client=mock_client,
            session_id="test-123",
            options=MagicMock(),
        )
        # Set last_accessed to 2 hours ago
        session.last_accessed = datetime.now(timezone.utc) - timedelta(hours=2)
        assert session.is_expired(ttl_seconds=3600) is True


class TestSessionManager:
    """Tests for SessionManager class."""

    @pytest.mark.asyncio
    async def test_create_session_returns_managed_session(
        self, session_manager: SessionManager
    ) -> None:
        """Verify create_session returns a ManagedSession."""
        mock_options = MagicMock()

        with patch("src.services.sessions.ClaudeSDKClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            session = await session_manager.create_session(mock_options)

            assert isinstance(session, ManagedSession)
            assert session.options == mock_options
            assert session.state == SessionState.ACTIVE
            mock_client.connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_session_generates_unique_ids(
        self, session_manager: SessionManager
    ) -> None:
        """Verify each session gets a unique ID."""
        mock_options = MagicMock()

        with patch("src.services.sessions.ClaudeSDKClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            session1 = await session_manager.create_session(mock_options)
            session2 = await session_manager.create_session(mock_options)

            assert session1.session_id != session2.session_id

    @pytest.mark.asyncio
    async def test_get_session_returns_existing_session(
        self, session_manager: SessionManager
    ) -> None:
        """Verify get_session returns existing session."""
        mock_options = MagicMock()

        with patch("src.services.sessions.ClaudeSDKClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            created = await session_manager.create_session(mock_options)
            retrieved = await session_manager.get_session(created.session_id)

            assert retrieved is not None
            assert retrieved.session_id == created.session_id

    @pytest.mark.asyncio
    async def test_get_session_returns_none_for_unknown_id(
        self, session_manager: SessionManager
    ) -> None:
        """Verify get_session returns None for unknown session."""
        result = await session_manager.get_session("nonexistent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_session_updates_last_accessed(self, session_manager: SessionManager) -> None:
        """Verify get_session updates last_accessed timestamp."""
        mock_options = MagicMock()

        with patch("src.services.sessions.ClaudeSDKClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            created = await session_manager.create_session(mock_options)
            original_time = created.last_accessed

            # Small delay to ensure timestamp differs
            await asyncio.sleep(0.01)

            retrieved = await session_manager.get_session(created.session_id)
            assert retrieved is not None
            assert retrieved.last_accessed >= original_time

    @pytest.mark.asyncio
    async def test_delete_session_removes_session(self, session_manager: SessionManager) -> None:
        """Verify delete_session removes the session."""
        mock_options = MagicMock()

        with patch("src.services.sessions.ClaudeSDKClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            session = await session_manager.create_session(mock_options)
            deleted = await session_manager.delete_session(session.session_id)

            assert deleted is True
            assert await session_manager.get_session(session.session_id) is None
            mock_client.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_session_returns_false_for_unknown(
        self, session_manager: SessionManager
    ) -> None:
        """Verify delete_session returns False for unknown session."""
        result = await session_manager.delete_session("nonexistent-id")
        assert result is False

    @pytest.mark.asyncio
    async def test_cleanup_expired_removes_old_sessions(self) -> None:
        """Verify cleanup_expired removes old sessions."""
        # Use very short TTL for testing
        manager = SessionManager(ttl_seconds=0)
        mock_options = MagicMock()

        with patch("src.services.sessions.ClaudeSDKClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            session = await manager.create_session(mock_options)
            session_id = session.session_id

            # Wait a tiny bit to ensure session is expired
            await asyncio.sleep(0.01)

            count = await manager.cleanup_expired()

            assert count == 1
            assert await manager.get_session(session_id) is None

    @pytest.mark.asyncio
    async def test_cleanup_all_removes_all_sessions(self, session_manager: SessionManager) -> None:
        """Verify cleanup_all removes all sessions."""
        mock_options = MagicMock()

        with patch("src.services.sessions.ClaudeSDKClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            await session_manager.create_session(mock_options)
            await session_manager.create_session(mock_options)

            count = await session_manager.cleanup_all()

            assert count == 2
            assert session_manager.get_session_count() == 0

    @pytest.mark.asyncio
    async def test_set_session_state_updates_state(self, session_manager: SessionManager) -> None:
        """Verify set_session_state updates the session state."""
        mock_options = MagicMock()

        with patch("src.services.sessions.ClaudeSDKClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            session = await session_manager.create_session(mock_options)
            assert session.state == SessionState.ACTIVE

            await session_manager.set_session_state(session.session_id, SessionState.STREAMING)

            updated = await session_manager.get_session(session.session_id)
            assert updated is not None
            assert updated.state == SessionState.STREAMING

    @pytest.mark.asyncio
    async def test_set_session_state_raises_for_unknown(
        self, session_manager: SessionManager
    ) -> None:
        """Verify set_session_state raises for unknown session."""
        with pytest.raises(SessionNotFoundError):
            await session_manager.set_session_state("nonexistent-id", SessionState.ACTIVE)

    def test_get_session_count(self, session_manager: SessionManager) -> None:
        """Verify get_session_count returns correct count."""
        assert session_manager.get_session_count() == 0
