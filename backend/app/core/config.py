"""Application configuration loaded from environment variables.

All settings are typed via pydantic-settings.
No secret values are hard-coded here.
"""
from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for SceneDiff backend."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    APP_ENV: str = "development"
    # None as default so mypy can construct Settings(); the validator below
    # ensures a real value is always present at runtime.
    DATABASE_URL: str | None = None
    LOG_LEVEL: str = "INFO"
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    @model_validator(mode="after")
    def _require_database_url(self) -> "Settings":
        """Raise if DATABASE_URL was not supplied via the environment."""
        if not self.DATABASE_URL:
            raise ValueError(
                "DATABASE_URL environment variable is required but was not set."
            )
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached Settings singleton.

    Using lru_cache defers env-var resolution until first call, which
    allows tests to set os.environ before the settings are loaded.
    """
    return Settings()
