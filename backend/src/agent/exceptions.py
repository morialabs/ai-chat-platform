"""Custom exceptions for agent session management."""


class SessionError(Exception):
    """Base exception for session-related errors."""


class SessionNotFoundError(SessionError):
    """Raised when a session ID is not found or has expired."""


class SessionStateError(SessionError):
    """Raised when a session is in an invalid state for the requested operation."""


class SessionLimitError(SessionError):
    """Raised when maximum session limit is exceeded."""
