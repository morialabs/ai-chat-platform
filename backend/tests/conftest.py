"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture
def sample_prompt() -> str:
    """Provide a sample prompt for testing."""
    return "What is 2 + 2?"
