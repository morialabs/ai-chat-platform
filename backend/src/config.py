"""Configuration management for AI Chat Platform."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = "AI Chat Platform"
    debug: bool = False

    # Claude Agent SDK
    anthropic_api_key: str = ""
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 8192

    # Workspace
    workspace_dir: Path = Path.cwd()

    @property
    def is_configured(self) -> bool:
        """Check if the API key is configured."""
        return bool(self.anthropic_api_key)


# Global settings instance
settings = Settings()
