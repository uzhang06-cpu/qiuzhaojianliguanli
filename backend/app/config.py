"""Application configuration, loaded from environment / .env file."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration."""

    database_url: str = "sqlite:///./smart_tracker.db"
    # For Render production:
    # database_url: str = "postgresql://user:pass@host:5432/smart_tracker"

    debug: bool = True

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
