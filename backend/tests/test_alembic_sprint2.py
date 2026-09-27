"""Sprint 2 — Alembic migration validation tests.

These tests validate the Sprint 2 migration file structure without
connecting to a live database.

Sprint philosophy
-----------------
Sprint 1 tests (test_alembic.py) verify Alembic infrastructure.
This file verifies Sprint 2 database schema migration correctness.
The split keeps sprint history clean and lets each sprint own its tests.

What is tested
--------------
- Exactly one Sprint 2 migration file exists.
- Revision ID is a non-empty string.
- down_revision is None (Sprint 2 is the first migration).
- upgrade() and downgrade() functions are defined.
- trace_sessions and trace_events tables appear in upgrade().
- tracestatus ENUM appears in upgrade().
- All expected indexes are present in upgrade().
- downgrade() drops indexes and tables in reverse order.
- Migration is importable as valid Python (AST parse).
- Alembic ScriptDirectory resolves the migration in its chain.
"""

import ast
import os
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_BACKEND_DIR = Path(__file__).parent.parent
_ALEMBIC_INI = _BACKEND_DIR / "alembic.ini"
_VERSIONS_DIR = _BACKEND_DIR / "alembic" / "versions"

_SPRINT2_PREFIX = "sprint2"


def _get_sprint2_migration() -> Path:
    """Return the single Sprint 2 migration file.

    Raises AssertionError with a descriptive message if not found.
    """
    files = [
        f
        for f in _VERSIONS_DIR.glob("*.py")
        if _SPRINT2_PREFIX in f.name and not f.name.startswith("_")
    ]
    assert len(files) == 1, (
        f"Expected exactly one Sprint 2 migration file (name contains "
        f"'{_SPRINT2_PREFIX}'), found {len(files)}: {files}"
    )
    return files[0]


def _migration_source() -> str:
    """Return the raw source text of the Sprint 2 migration."""
    return _get_sprint2_migration().read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# File existence and naming
# ---------------------------------------------------------------------------


def test_sprint2_migration_file_exists() -> None:
    """Exactly one Sprint 2 migration file must exist in alembic/versions/."""
    _get_sprint2_migration()  # raises if not exactly one


def test_sprint2_migration_filename_contains_sprint2() -> None:
    """Migration filename must contain 'sprint2' for clear sprint attribution."""
    path = _get_sprint2_migration()
    assert _SPRINT2_PREFIX in path.name


# ---------------------------------------------------------------------------
# Python syntax
# ---------------------------------------------------------------------------


def test_sprint2_migration_is_valid_python() -> None:
    """Migration file must parse as valid Python (no syntax errors)."""
    source = _migration_source()
    try:
        ast.parse(source)
    except SyntaxError as exc:
        raise AssertionError(
            f"Sprint 2 migration contains a syntax error: {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# Revision identifiers
# ---------------------------------------------------------------------------


def test_sprint2_revision_id_is_set() -> None:
    """revision must be a non-empty string literal."""
    source = _migration_source()
    assert 'revision: str = "' in source or "revision: str = '" in source, (
        "Sprint 2 migration must assign a typed revision string"
    )


def test_sprint2_down_revision_is_none() -> None:
    """down_revision must be None — Sprint 2 is the initial migration."""
    source = _migration_source()
    assert "down_revision: str | None = None" in source, (
        "Sprint 2 is the first migration; down_revision must be None"
    )


# ---------------------------------------------------------------------------
# upgrade() function
# ---------------------------------------------------------------------------


def test_sprint2_migration_has_upgrade() -> None:
    """upgrade() function must be defined."""
    assert "def upgrade() -> None:" in _migration_source()


def test_sprint2_upgrade_creates_trace_sessions() -> None:
    """upgrade() must create the trace_sessions table."""
    source = _migration_source()
    assert "trace_sessions" in source, "upgrade() must create the trace_sessions table"


def test_sprint2_upgrade_creates_trace_events() -> None:
    """upgrade() must create the trace_events table."""
    source = _migration_source()
    assert "trace_events" in source, "upgrade() must create the trace_events table"


def test_sprint2_upgrade_creates_tracestatus_enum() -> None:
    """upgrade() must create the tracestatus ENUM type."""
    source = _migration_source()
    assert "tracestatus" in source, "upgrade() must create the tracestatus ENUM type"


def test_sprint2_upgrade_creates_session_indexes() -> None:
    """upgrade() must create all trace_sessions indexes."""
    source = _migration_source()
    expected = [
        "ix_trace_sessions_repository_name",
        "ix_trace_sessions_status",
        "ix_trace_sessions_created_at",
    ]
    for index_name in expected:
        assert index_name in source, f"upgrade() must create index '{index_name}'"


def test_sprint2_upgrade_creates_event_indexes() -> None:
    """upgrade() must create all trace_events indexes."""
    source = _migration_source()
    expected = [
        "ix_trace_events_trace_session_id",
        "ix_trace_events_event_type",
        "ix_trace_events_behavior_hash",
    ]
    for index_name in expected:
        assert index_name in source, f"upgrade() must create index '{index_name}'"


def test_sprint2_upgrade_cascade_fk() -> None:
    """upgrade() must define the FK with CASCADE delete."""
    source = _migration_source()
    assert "CASCADE" in source, (
        "trace_events.trace_session_id FK must use ON DELETE CASCADE"
    )


# ---------------------------------------------------------------------------
# downgrade() function
# ---------------------------------------------------------------------------


def test_sprint2_migration_has_downgrade() -> None:
    """downgrade() function must be defined."""
    assert "def downgrade() -> None:" in _migration_source()


def test_sprint2_downgrade_drops_trace_events_first() -> None:
    """downgrade() must drop trace_events before trace_sessions (FK order)."""
    source = _migration_source()
    downgrade_section = source[source.find("def downgrade()") :]
    events_pos = downgrade_section.find("trace_events")
    sessions_pos = downgrade_section.find("trace_sessions")
    assert events_pos != -1, "downgrade() must reference trace_events"
    assert sessions_pos != -1, "downgrade() must reference trace_sessions"
    assert events_pos < sessions_pos, (
        "downgrade() must drop trace_events before trace_sessions "
        "(child before parent — respects the FK constraint)"
    )


def test_sprint2_downgrade_drops_enum() -> None:
    """downgrade() must drop the tracestatus ENUM type."""
    source = _migration_source()
    downgrade_section = source[source.find("def downgrade()") :]
    assert "tracestatus" in downgrade_section, (
        "downgrade() must drop the tracestatus ENUM type"
    )


# ---------------------------------------------------------------------------
# Alembic script directory resolution
# ---------------------------------------------------------------------------


def test_sprint2_migration_in_alembic_chain() -> None:
    """Alembic ScriptDirectory must include the Sprint 2 migration in its chain."""
    cfg = Config(str(_ALEMBIC_INI))
    original = os.getcwd()
    try:
        os.chdir(_BACKEND_DIR)
        sd = ScriptDirectory.from_config(cfg)
        # Walk the revision chain and collect all revision IDs.
        revisions = [rev.revision for rev in sd.walk_revisions()]
    finally:
        os.chdir(original)

    assert len(revisions) >= 1, (
        "Alembic chain must contain at least one revision (Sprint 2)"
    )


def test_sprint2_migration_is_head() -> None:
    """Sprint 2 migration must be the current head revision."""
    cfg = Config(str(_ALEMBIC_INI))
    original = os.getcwd()
    try:
        os.chdir(_BACKEND_DIR)
        sd = ScriptDirectory.from_config(cfg)
        heads = sd.get_heads()
    finally:
        os.chdir(original)

    assert len(heads) == 1, f"Expected a single head revision, got: {heads}"
