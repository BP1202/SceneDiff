"""Tests for app/core/config.py.

Each test that constructs a Settings instance directly (not via get_settings)
passes all required fields explicitly so the tests are self-contained and
never depend on the process environment or a .env file.
"""

from pydantic import ValidationError
import pytest

from app.core.config import Settings, get_settings

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_REQUIRED = {"DATABASE_URL": "postgresql+asyncpg://u:p@localhost:5432/db"}


def _make(**overrides: object) -> Settings:
    """Return a Settings instance with required fields + any overrides."""
    return Settings.model_validate({**_REQUIRED, **overrides})


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------


def test_default_app_env() -> None:
    """APP_ENV must default to development."""
    s = _make()
    assert s.APP_ENV == "development"


def test_default_log_level() -> None:
    """LOG_LEVEL must default to INFO."""
    s = _make()
    assert s.LOG_LEVEL == "INFO"


def test_default_debug_is_false() -> None:
    """DEBUG must default to False."""
    s = _make()
    assert s.DEBUG is False


def test_default_docs_enabled() -> None:
    """DOCS_ENABLED must default to True."""
    s = _make()
    assert s.DOCS_ENABLED is True


def test_default_api_version() -> None:
    """API_VERSION must default to v1."""
    s = _make()
    assert s.API_VERSION == "v1"


def test_default_allowed_origins() -> None:
    """ALLOWED_ORIGINS must default to localhost:3000."""
    s = _make()
    assert s.ALLOWED_ORIGINS == "http://localhost:3000"


def test_default_db_pool_size() -> None:
    """DB_POOL_SIZE must default to 5."""
    s = _make()
    assert s.DB_POOL_SIZE == 5


def test_default_db_max_overflow() -> None:
    """DB_MAX_OVERFLOW must default to 10."""
    s = _make()
    assert s.DB_MAX_OVERFLOW == 10


def test_default_db_pool_timeout() -> None:
    """DB_POOL_TIMEOUT must default to 30."""
    s = _make()
    assert s.DB_POOL_TIMEOUT == 30


def test_default_db_echo_is_false() -> None:
    """DB_ECHO must default to False."""
    s = _make()
    assert s.DB_ECHO is False


def test_default_secret_shield_enabled() -> None:
    """SECRET_SHIELD_ENABLED must default to True."""
    s = _make()
    assert s.SECRET_SHIELD_ENABLED is True


def test_default_secret_shield_block_on_detect() -> None:
    """SECRET_SHIELD_BLOCK_ON_DETECT must default to True."""
    s = _make()
    assert s.SECRET_SHIELD_BLOCK_ON_DETECT is True


def test_default_secret_shield_log_detections() -> None:
    """SECRET_SHIELD_LOG_DETECTIONS must default to False."""
    s = _make()
    assert s.SECRET_SHIELD_LOG_DETECTIONS is False


# ---------------------------------------------------------------------------
# Required fields
# ---------------------------------------------------------------------------


def test_missing_database_url_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """Omitting DATABASE_URL must raise ValidationError.

    We explicitly unset the env var so the test is not affected by the
    DATABASE_URL injected by conftest.py for the broader test session.
    """
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValidationError, match="DATABASE_URL is required"):
        # _env_file=None prevents pydantic-settings from reading .env on disk.
        Settings(_env_file=None)  # type: ignore[call-arg]


def test_database_url_empty_string_raises() -> None:
    """An empty DATABASE_URL must raise ValidationError."""
    with pytest.raises(ValidationError, match="DATABASE_URL is required"):
        Settings.model_validate({"DATABASE_URL": ""})


# ---------------------------------------------------------------------------
# Boolean parsing
# ---------------------------------------------------------------------------


def test_debug_parses_true_string() -> None:
    """Pydantic must coerce the string 'true' to bool True."""
    s = Settings.model_validate({**_REQUIRED, "DEBUG": "true"})
    assert s.DEBUG is True


def test_debug_parses_false_string() -> None:
    """Pydantic must coerce the string 'false' to bool False."""
    s = Settings.model_validate({**_REQUIRED, "DEBUG": "false"})
    assert s.DEBUG is False


def test_db_echo_parses_1() -> None:
    """Pydantic must coerce the string '1' to bool True for DB_ECHO."""
    s = Settings.model_validate({**_REQUIRED, "DB_ECHO": "1"})
    assert s.DB_ECHO is True


def test_docs_enabled_parses_false_string() -> None:
    """Pydantic must coerce 'false' to bool False for DOCS_ENABLED."""
    s = Settings.model_validate({**_REQUIRED, "DOCS_ENABLED": "false"})
    assert s.DOCS_ENABLED is False


# ---------------------------------------------------------------------------
# Production guards
# ---------------------------------------------------------------------------


def test_production_debug_true_raises() -> None:
    """DEBUG=True in production must raise ValidationError."""
    with pytest.raises(ValidationError, match="DEBUG must be False in production"):
        Settings.model_validate({**_REQUIRED, "APP_ENV": "production", "DEBUG": True})


def test_production_secret_shield_disabled_raises() -> None:
    """SECRET_SHIELD_ENABLED=False in production must raise ValidationError."""
    with pytest.raises(
        ValidationError, match="SECRET_SHIELD_ENABLED must be True in production"
    ):
        Settings.model_validate(
            {**_REQUIRED, "APP_ENV": "production", "SECRET_SHIELD_ENABLED": False}
        )


# ---------------------------------------------------------------------------
# Derived properties
# ---------------------------------------------------------------------------


def test_allowed_origins_list_single() -> None:
    """allowed_origins_list must return a list with one item."""
    s = _make(ALLOWED_ORIGINS="http://localhost:3000")
    assert s.allowed_origins_list == ["http://localhost:3000"]


def test_allowed_origins_list_multiple() -> None:
    """allowed_origins_list must split on comma and strip whitespace."""
    s = _make(ALLOWED_ORIGINS="http://a.com, http://b.com , http://c.com")
    assert s.allowed_origins_list == ["http://a.com", "http://b.com", "http://c.com"]


def test_is_development_true_for_development() -> None:
    """is_development must be True when APP_ENV is development."""
    s = _make(APP_ENV="development")
    assert s.is_development is True


def test_is_development_false_for_staging() -> None:
    """is_development must be False when APP_ENV is staging."""
    s = _make(APP_ENV="staging")
    assert s.is_development is False


def test_is_production_true_for_production() -> None:
    """is_production must be True when APP_ENV is production."""
    s = _make(
        APP_ENV="production",
        DEBUG=False,
        SECRET_SHIELD_ENABLED=True,
    )
    assert s.is_production is True


# ---------------------------------------------------------------------------
# Cached singleton
# ---------------------------------------------------------------------------


def test_get_settings_returns_same_instance(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_settings() must return the identical object on repeated calls."""
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost:5432/test")
    get_settings.cache_clear()
    try:
        first = get_settings()
        second = get_settings()
        assert first is second
    finally:
        get_settings.cache_clear()


def test_get_settings_cache_clear_produces_new_instance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """After cache_clear, get_settings() must return a fresh instance."""
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost:5432/test")
    get_settings.cache_clear()
    try:
        first = get_settings()
        get_settings.cache_clear()
        second = get_settings()
        assert first is not second
    finally:
        get_settings.cache_clear()
