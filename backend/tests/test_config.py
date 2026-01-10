"""Test configuration loading."""

from src.config import Settings


def test_settings_loads() -> None:
    """Verify settings can be instantiated."""
    settings = Settings()
    assert settings.app_name == "AI Chat Platform"


def test_settings_default_model() -> None:
    """Verify default model is set."""
    settings = Settings()
    assert "claude" in settings.model.lower()


def test_settings_is_configured_without_key() -> None:
    """Verify is_configured returns False without API key."""
    settings = Settings(anthropic_api_key="")
    assert settings.is_configured is False


def test_settings_is_configured_with_key() -> None:
    """Verify is_configured returns True with API key."""
    settings = Settings(anthropic_api_key="test-key")
    assert settings.is_configured is True
