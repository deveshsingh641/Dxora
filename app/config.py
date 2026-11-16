"""Configuration module using pydantic-settings.

Loads environment variables from `.env` or system environment.
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings and API credentials."""

    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 4000
    ENVIRONMENT: str = "development"

    # Simulation fallback mode for demo/testing without credentials
    ENABLE_MOCK_FALLBACK: bool = False

    # 1. Telegram
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None

    # 2. Discord
    DISCORD_WEBHOOK_URL: Optional[str] = None
    DISCORD_GUILD_ID: Optional[str] = None

    # 3. Mastodon
    MASTODON_INSTANCE_URL: str = "https://mastodon.social"
    MASTODON_ACCESS_TOKEN: Optional[str] = None

    # 4. Bluesky (AT Protocol)
    BLUESKY_HANDLE: Optional[str] = None
    BLUESKY_APP_PASSWORD: Optional[str] = None
    BLUESKY_PDS_URL: str = "https://bsky.social"

    # 5. Hugging Face (LLM & Community Platform)
    HUGGINGFACE_TOKEN: Optional[str] = None
    HUGGINGFACE_REPO_ID: Optional[str] = None

    # 6. Dev.to
    DEVTO_API_KEY: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
