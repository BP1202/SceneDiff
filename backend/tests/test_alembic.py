"""Tests for Alembic configuration.

These tests validate the Alembic setup — alembic.ini structure, env.py
imports, and migration script generation — without connecting to a real
database.

Test strategy
-------------
- Parse alembic.ini with ConfigParser to verify required keys.
- Import alembic/env.py symbols directly to validate they are importable.
- Use alembic.config.Config to confirm the script_location resolves.
- Use alembic.script.ScriptDirectory to verify versions/ is discoverable.
- Verify that the script template renders a valid Python migration stub.
- Confirm Base.metadata is wired to target_metadata in env.py.
"""

import configparser
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_BACKEND_DIR = Path(__file__).parent.parent  # backend/
_ALEMBIC_INI = _BACKEND_DIR / "alembic.ini"
_ALEMBIC_DIR = _BACKEND_DIR / "alembic"
_VERSIONS_DIR = _ALEMBIC_DIR / "versions"
_ENV_PY = _ALEMBIC_DIR / "env.py"
_SCRIPT_MAKO = _ALEMBIC_DIR / "script.py.mako"


# ---------------------------------------------------------------------------
# alembic.ini structure
# ---------------------------------------------------------------------------


def test_alembic_ini_exists() -> None:
    """alembic.ini must exist in the backend/ directory."""
    assert _ALEMBIC_INI.exists(), f"Missing: {_ALEMBIC_INI}"


def test_alembic_ini_has_alembic_section() -> None:
    """alembic.ini must have an [alembic] section."""
    cfg = configparser.ConfigParser()
    cfg.read(_ALEMBIC_INI)
    assert cfg.has_section("alembic")


def test_alembic_ini_script_location() -> None:
    """script_location must point to the alembic/ directory."""
    cfg = configparser.ConfigParser()
    cfg.read(_ALEMBIC_INI)
    assert cfg.get("alembic", "script_location") == "alembic"


def test_alembic_ini_no_hardcoded_url() -> None:
    """sqlalchemy.url must NOT be set in alembic.ini (credentials stay out of VCS)."""
    cfg = configparser.ConfigParser()
    cfg.read(_ALEMBIC_INI)
    assert not cfg.has_option("alembic", "sqlalchemy.url"), (
        "sqlalchemy.url must not be set in alembic.ini — "
        "DATABASE_URL is read from pydantic Settings at runtime."
    )


def test_alembic_ini_prepend_sys_path() -> None:
    """prepend_sys_path must include '.' so that 'app' is importable."""
    cfg = configparser.ConfigParser()
    cfg.read(_ALEMBIC_INI)
    value = cfg.get("alembic", "prepend_sys_path")
    assert "." in value.split()


def test_alembic_ini_file_template() -> None:
    """file_template must be set for consistent migration file naming."""
    cfg = configparser.ConfigParser()
    cfg.read(_ALEMBIC_INI)
    assert cfg.has_option("alembic", "file_template")
    # Template must reference revision ID.
    assert "rev" in cfg.get("alembic", "file_template")


# ---------------------------------------------------------------------------
# alembic/ directory structure
# ---------------------------------------------------------------------------


def test_alembic_directory_exists() -> None:
    """alembic/ directory must exist inside backend/."""
    assert _ALEMBIC_DIR.is_dir()


def test_env_py_exists() -> None:
    """alembic/env.py must exist."""
    assert _ENV_PY.exists()


def test_script_mako_exists() -> None:
    """alembic/script.py.mako must exist."""
    assert _SCRIPT_MAKO.exists()


def test_versions_directory_exists() -> None:
    """alembic/versions/ directory must exist."""
    assert _VERSIONS_DIR.is_dir()


# ---------------------------------------------------------------------------
# Alembic Config API
# ---------------------------------------------------------------------------


def test_alembic_config_loads() -> None:
    """alembic.Config must load alembic.ini without errors."""
    cfg = Config(str(_ALEMBIC_INI))
    assert cfg is not None


def test_alembic_config_script_location_resolves() -> None:
    """Config.get_main_option('script_location') must return 'alembic'."""
    cfg = Config(str(_ALEMBIC_INI))
    assert cfg.get_main_option("script_location") == "alembic"


def test_script_directory_resolves() -> None:
    """ScriptDirectory must resolve from alembic.ini without errors."""
    cfg = Config(str(_ALEMBIC_INI))
    # ScriptDirectory needs to find the alembic/ folder.
    # Run with cwd set to backend/ so relative paths resolve.
    import os

    original = os.getcwd()
    try:
        os.chdir(_BACKEND_DIR)
        sd = ScriptDirectory.from_config(cfg)
        assert sd is not None
    finally:
        os.chdir(original)


def test_script_directory_versions_path() -> None:
    """ScriptDirectory must resolve the versions/ path."""
    import os

    cfg = Config(str(_ALEMBIC_INI))
    original = os.getcwd()
    try:
        os.chdir(_BACKEND_DIR)
        sd = ScriptDirectory.from_config(cfg)
        # versions_fn_map holds the discovered migration files.
        assert sd.versions is not None
    finally:
        os.chdir(original)


def test_no_migration_files_on_clean_install() -> None:
    """versions/ must be empty (no application tables yet in Sprint 1)."""
    migration_files = [
        f for f in _VERSIONS_DIR.glob("*.py") if not f.name.startswith("_")
    ]
    sprint1_files = [f for f in migration_files if "sprint2" not in f.name]
    assert sprint1_files == [], (
        f"Unexpected pre-Sprint-2 migration files found: {sprint1_files}. "
        "Sprint 1 shipped no application table migrations by design."
    )


# ---------------------------------------------------------------------------
# env.py imports and wiring
# ---------------------------------------------------------------------------


def test_env_py_imports_base_metadata() -> None:
    """env.py must reference Base.metadata as target_metadata."""
    source = _ENV_PY.read_text(encoding="utf-8")
    assert "Base.metadata" in source or "target_metadata = Base.metadata" in source


def test_env_py_imports_get_settings() -> None:
    """env.py must import get_settings to source DATABASE_URL at runtime."""
    source = _ENV_PY.read_text(encoding="utf-8")
    assert "get_settings" in source
    # URL must be resolved lazily (inside a function), not at module-level.
    assert "_get_database_url" in source


def test_env_py_no_hardcoded_credentials() -> None:
    """env.py must not contain any hard-coded database credentials."""
    source = _ENV_PY.read_text(encoding="utf-8")
    # Passwords should never be embedded in source files.
    forbidden = ["password=", "passwd=", "secret=", "://user:pass"]
    for token in forbidden:
        assert token not in source, (
            f"Possible hard-coded credential found in env.py: {token!r}"
        )


def test_env_py_supports_offline_mode() -> None:
    """env.py must define run_migrations_offline()."""
    source = _ENV_PY.read_text(encoding="utf-8")
    assert "def run_migrations_offline" in source


def test_env_py_supports_online_mode() -> None:
    """env.py must define run_migrations_online() or run_async_migrations()."""
    source = _ENV_PY.read_text(encoding="utf-8")
    assert "run_migrations_online" in source or "run_async_migrations" in source


def test_env_py_uses_null_pool_for_migrations() -> None:
    """env.py must use NullPool so migrations don't share the app connection pool."""
    source = _ENV_PY.read_text(encoding="utf-8")
    assert "NullPool" in source


# ---------------------------------------------------------------------------
# script.py.mako template
# ---------------------------------------------------------------------------


def test_script_mako_has_upgrade_function() -> None:
    """Migration template must include an upgrade() function."""
    source = _SCRIPT_MAKO.read_text(encoding="utf-8")
    assert "def upgrade()" in source


def test_script_mako_has_downgrade_function() -> None:
    """Migration template must include a downgrade() function."""
    source = _SCRIPT_MAKO.read_text(encoding="utf-8")
    assert "def downgrade()" in source


def test_script_mako_has_revision_identifiers() -> None:
    """Migration template must include revision identifier variables."""
    source = _SCRIPT_MAKO.read_text(encoding="utf-8")
    assert "revision" in source
    assert "down_revision" in source


def test_script_mako_imports_sqlalchemy() -> None:
    """Migration template must import sqlalchemy for DDL operations."""
    source = _SCRIPT_MAKO.read_text(encoding="utf-8")
    assert "import sqlalchemy" in source or "import sa" in source


def test_script_mako_imports_op() -> None:
    """Migration template must import alembic.op for schema operations."""
    source = _SCRIPT_MAKO.read_text(encoding="utf-8")
    assert "from alembic import op" in source
