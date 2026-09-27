"""Sprint 4 — Alembic migration validation tests.

Validates the Sprint 4 migration (revision 0002) without connecting to a live DB.
"""

from __future__ import annotations

import ast
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

_BACKEND_DIR = Path(__file__).parent.parent
_ALEMBIC_INI = _BACKEND_DIR / "alembic.ini"
_VERSIONS_DIR = _BACKEND_DIR / "alembic" / "versions"
_SPRINT4_PREFIX = "sprint4"


def _get_sprint4_migration() -> Path:
    files = [
        f
        for f in _VERSIONS_DIR.glob("*.py")
        if _SPRINT4_PREFIX in f.name and not f.name.startswith("_")
    ]
    assert len(files) == 1, (
        f"Expected exactly 1 Sprint 4 migration ({_SPRINT4_PREFIX}), "
        f"found {len(files)}: {files}"
    )
    return files[0]


class TestSprint4MigrationStructure:
    def test_sprint4_migration_file_exists(self) -> None:
        path = _get_sprint4_migration()
        assert path.is_file()

    def test_migration_is_valid_python(self) -> None:
        source = _get_sprint4_migration().read_text(encoding="utf-8")
        tree = ast.parse(source)
        assert tree is not None

    def test_migration_defines_revision_and_down_revision(self) -> None:
        source = _get_sprint4_migration().read_text(encoding="utf-8")
        assert 'revision: str = "' in source or "revision: str = '" in source
        assert "down_revision: str | None =" in source

    def test_down_revision_is_0001(self) -> None:
        source = _get_sprint4_migration().read_text(encoding="utf-8")
        assert 'down_revision: str | None = "0001"' in source

    def test_upgrade_and_downgrade_functions_exist(self) -> None:
        source = _get_sprint4_migration().read_text(encoding="utf-8")
        tree = ast.parse(source)
        funcs = {
            node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
        }
        assert "upgrade" in funcs
        assert "downgrade" in funcs

    def test_upgrade_creates_behavior_comparisons_and_events(self) -> None:
        source = _get_sprint4_migration().read_text(encoding="utf-8")
        assert "behavior_comparisons" in source
        assert "comparison_events" in source
        assert "comparisonstatus" in source

    def test_alembic_script_directory_resolves_0002_head(self) -> None:
        config = Config(str(_ALEMBIC_INI))
        scripts = ScriptDirectory.from_config(config)
        heads = scripts.get_heads()
        assert "0002" in heads
