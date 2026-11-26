from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # General
    PROJECT_NAME: str = "mothership-core"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Database: PostgreSQL
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5433  # default mapped host port for local dev
    POSTGRES_DB: str = "mothership_core"
    POSTGRES_USER: str = "core_user"
    POSTGRES_PASSWORD: str = "devpassword123"

    # Optional complete database URL (overrides individual postgres settings if provided)
    CUSTOM_DATABASE_URL: str | None = Field(default=None, alias="DATABASE_URL")

    # Security & Auth
    JWT_SECRET_KEY: str = "insecure-dev-secret-key-change-in-production-only-12345"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ADMIN_INITIAL_USERNAME: str = "admin"
    ADMIN_INITIAL_PASSWORD: str = "adminpassword123"

    # Azure Application Insights (Optional in local dev, active in Azure)
    APPLICATIONINSIGHTS_CONNECTION_STRING: str | None = None

    # External services
    PULSE_API_URL: str = "http://localhost:8080"
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://dash.pydev.se",
    ]

    @property
    def database_url(self) -> str:
        """Return the async SQLAlchemy connection string."""
        if self.CUSTOM_DATABASE_URL:
            # Handle standard postgresql:// -> postgresql+asyncpg://
            url = self.CUSTOM_DATABASE_URL
            if url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            elif url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+asyncpg://", 1)
            return url
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


@lru_cache()
def get_settings() -> Settings:
    """Cached singleton for application settings."""
    return Settings()
