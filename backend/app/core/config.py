"""Application configuration loaded from environment variables.

All settings are typed via pydantic-settings.
No secret values are hard-coded here.
No os.getenv() calls outside this module.

Settings groups:
    App          — runtime environment, logging
    API          — versioning, documentation visibility, CORS
    PostgreSQL   — async database connection
    Secret Shield — trace privacy and masking behaviour
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed runtime configuration for SceneDiff backend.

    Every field maps 1-to-1 to an environment variable (UPPER_CASE).
    Sensitive defaults are never hard-coded; required fields raise
    ValidationError at startup if missing.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        # Extra env vars in .env are silently ignored — safer than erroring.
        extra="ignore",
    )

    # -------------------------------------------------------------------------
    # App
    # -------------------------------------------------------------------------
    APP_ENV: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Runtime environment. Controls docs visibility and log verbosity.",
    )
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Stdlib logging level applied at startup.",
    )
    DEBUG: bool = Field(
        default=False,
        description="Enable debug mode. Must be False in production.",
    )

    # -------------------------------------------------------------------------
    # API
    # -------------------------------------------------------------------------
    API_VERSION: str = Field(
        default="v1",
        description="Current API version prefix, e.g. v1.",
    )
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:3000",
        description=(
            "Comma-separated list of allowed CORS origins. "
            "Example: http://localhost:3000,https://app.scenediff.io"
        ),
    )
    DOCS_ENABLED: bool = Field(
        default=True,
        description="Expose /docs and /redoc. Set False in production.",
    )

    # -------------------------------------------------------------------------
    # PostgreSQL
    # -------------------------------------------------------------------------
    DATABASE_URL: str | None = Field(
        default=None,
        description=(
            "Async PostgreSQL DSN. Required. "
            "Format: postgresql+asyncpg://user:password@host:port/dbname"
        ),
    )
    DB_POOL_SIZE: int = Field(
        default=5,
        ge=1,
        le=50,
        description="SQLAlchemy connection pool size.",
    )
    DB_MAX_OVERFLOW: int = Field(
        default=10,
        ge=0,
        le=100,
        description="SQLAlchemy max connections above DB_POOL_SIZE.",
    )
    DB_POOL_TIMEOUT: int = Field(
        default=30,
        ge=1,
        description="Seconds to wait for a connection from the pool.",
    )
    DB_ECHO: bool = Field(
        default=False,
        description="Log all SQL statements. Override to True in development.",
    )

    # -------------------------------------------------------------------------
    # Secret Shield
    # -------------------------------------------------------------------------
    SECRET_SHIELD_ENABLED: bool = Field(
        default=True,
        description=(
            "Master switch for Secret Shield. Must be True in staging and production."
        ),
    )
    SECRET_SHIELD_BLOCK_ON_DETECT: bool = Field(
        default=True,
        description=(
            "Reject a trace entirely when a secret is detected. "
            "When False, the trace is stored with MASKED privacy level."
        ),
    )
    SECRET_SHIELD_LOG_DETECTIONS: bool = Field(
        default=False,
        description=(
            "Emit a WARNING log when a secret pattern is matched. "
            "Never logs the secret itself — only the pattern category."
        ),
    )

    # -------------------------------------------------------------------------
    # Validators
    # -------------------------------------------------------------------------
    @model_validator(mode="after")
    def _validate_required_fields(self) -> "Settings":
        """Enforce fields that have no safe default."""
        if not self.DATABASE_URL:
            raise ValueError(
                "DATABASE_URL is required. "
                "Set it to a postgresql+asyncpg:// DSN in your .env file."
            )
        if self.APP_ENV == "production" and self.DEBUG:
            raise ValueError("DEBUG must be False in production.")
        if self.APP_ENV == "production" and not self.SECRET_SHIELD_ENABLED:
            raise ValueError("SECRET_SHIELD_ENABLED must be True in production.")
        return self

    # -------------------------------------------------------------------------
    # Derived helpers (not env vars — read-only properties)
    # -------------------------------------------------------------------------
    @property
    def allowed_origins_list(self) -> list[str]:
        """Return ALLOWED_ORIGINS as a parsed list."""
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    @property
    def is_development(self) -> bool:
        """True when running in the development environment."""
        return self.APP_ENV == "development"

    @property
    def is_production(self) -> bool:
        """True when running in the production environment."""
        return self.APP_ENV == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached Settings singleton.

    lru_cache defers env-var resolution until first call, which allows
    tests to set os.environ before settings are loaded.  Call
    get_settings.cache_clear() in tests that need a fresh instance.
    """
    return Settings()
