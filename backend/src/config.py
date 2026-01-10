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
    model: str = "claude-opus-4-5-20251101"
    max_tokens: int = 8192

    # Workspace
    workspace_dir: Path = Path.cwd()

    # Server ports
    port: int = 8000
    frontend_port: int = 3000

    @property
    def allowed_origins(self) -> list[str]:
        """Dynamic CORS origins based on frontend_port."""
        return [
            f"http://localhost:{self.frontend_port}",
            f"http://127.0.0.1:{self.frontend_port}",
        ]

    @property
    def is_configured(self) -> bool:
        """Check if the API key is configured."""
        return bool(self.anthropic_api_key)


# Global settings instance
settings = Settings()
