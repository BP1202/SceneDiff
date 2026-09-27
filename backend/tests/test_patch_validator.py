"""Unit tests for Patch Validator Engine (Sprint 6 - Task 50)."""

from __future__ import annotations

from app.repair.validator import PatchValidator, ValidationResult

VALID_DIFF = """diff --git a/app/auth/login.py b/app/auth/login.py
--- a/app/auth/login.py
+++ b/app/auth/login.py
@@ -10,3 +10,6 @@
 def validate_token(token):
+    if token is None:
+        raise ValueError("Token is None")
     return token
"""

MALFORMED_HUNK_DIFF = """diff --git a/app/auth/login.py b/app/auth/login.py
--- a/app/auth/login.py
+++ b/app/auth/login.py
@@ not a valid hunk @@
 def validate_token(token):
+    return token
"""

BAD_SYNTAX_PYTHON_DIFF = """diff --git a/app/auth/login.py b/app/auth/login.py
--- a/app/auth/login.py
+++ b/app/auth/login.py
@@ -10,3 +10,4 @@
 def validate_token(token):
+    if token is (definitely not valid python syntax:::
     return token
"""


def test_validation_result_to_dict() -> None:
    """ValidationResult serializes to dictionary."""
    res = ValidationResult(
        is_valid=True,
        syntax_valid=True,
        ast_valid=True,
        secret_scan="passed",
        scope_valid=True,
        errors=[],
        notes=["All checks passed"],
    )
    d = res.to_dict()
    assert d["is_valid"] is True
    assert d["secret_scan"] == "passed"
    assert d["notes"] == ["All checks passed"]


def test_validator_valid_patch_syntax() -> None:
    """Validator passes valid unified git diff."""
    ok, errors = PatchValidator.validate_patch_syntax(VALID_DIFF)
    assert ok is True
    assert len(errors) == 0


def test_validator_empty_patch_syntax() -> None:
    """Validator rejects empty patch content."""
    ok, errors = PatchValidator.validate_patch_syntax("")
    assert ok is False
    assert any("empty" in e.lower() for e in errors)


def test_validator_malformed_hunk() -> None:
    """Validator rejects malformed @@ hunk header."""
    ok, errors = PatchValidator.validate_patch_syntax(MALFORMED_HUNK_DIFF)
    assert ok is False
    assert any("malformed hunk" in e.lower() for e in errors)


def test_validator_python_ast_success() -> None:
    """Validator confirms parseable Python code in diff hunks."""
    ok, errors = PatchValidator.validate_python_ast("app/auth/login.py", VALID_DIFF)
    assert ok is True
    assert len(errors) == 0


def test_validator_python_ast_syntax_error() -> None:
    """Validator catches Python syntax errors in diff hunks."""
    ok, errors = PatchValidator.validate_python_ast(
        "app/auth/login.py", BAD_SYNTAX_PYTHON_DIFF
    )
    assert ok is False
    assert any("syntax error" in e.lower() for e in errors)


def test_validator_non_python_skips_ast() -> None:
    """Validator skips AST parsing for non-python files."""
    ok, errors = PatchValidator.validate_python_ast(
        "frontend/app.tsx", BAD_SYNTAX_PYTHON_DIFF
    )
    assert ok is True
    assert len(errors) == 0


def test_validator_secret_shield_detection() -> None:
    """Validator detects hardcoded credentials and fails secret scan."""
    diff_with_secret = (
        "diff --git a/app/config.py b/app/config.py\n"
        "--- a/app/config.py\n"
        "+++ b/app/config.py\n"
        "@@ -1,2 +1,3 @@\n"
        "+AWS_KEY = 'AKIA1234567890123456'\n"
    )
    res = PatchValidator.validate(
        target_file="app/config.py",
        diff_content=diff_with_secret,
    )
    assert res.is_valid is False
    assert res.secret_scan == "failed"
    assert any("Secret Shield" in e for e in res.errors)


def test_validator_scope_blocks_env_file() -> None:
    """Validator blocks modifications to .env files (Improvement 1)."""
    ok, errors = PatchValidator.validate_patch_scope(
        target_file=".env",
        allowed_files=[".env"],
    )
    assert ok is False
    assert any("modifications to .env are blocked" in e for e in errors)


def test_validator_scope_blocks_unprompted_requirements() -> None:
    """Validator blocks requirements.txt modification without dependency reason."""
    ok, errors = PatchValidator.validate_patch_scope(
        target_file="requirements.txt",
        allowed_files=["requirements.txt"],
        reason="Null pointer in login",
    )
    assert ok is False
    assert any("without dependency root cause" in e for e in errors)


def test_validator_scope_allows_prompted_requirements() -> None:
    """Validator allows requirements.txt modification when reason states dependency."""
    ok, errors = PatchValidator.validate_patch_scope(
        target_file="requirements.txt",
        allowed_files=["requirements.txt"],
        reason="Missing package dependency cryptography",
    )
    assert ok is True


def test_validator_scope_blocks_migrations_inside_patch() -> None:
    """Validator blocks database migration scripts inside repair patches."""
    ok, errors = PatchValidator.validate_patch_scope(
        target_file="backend/alembic/versions/0005_test.py",
        allowed_files=["backend/alembic/versions/0005_test.py"],
    )
    assert ok is False
    assert any("database migrations inside patch are prohibited" in e for e in errors)


def test_validator_scope_enforces_allowed_files() -> None:
    """Validator restricts patch strictly to culprit file(s)."""
    ok, errors = PatchValidator.validate_patch_scope(
        target_file="app/core/unrelated.py",
        allowed_files=["app/auth/login.py"],
    )
    assert ok is False
    assert any("not in culprit files" in e for e in errors)


def test_validator_scope_blocks_disallowed_extensions() -> None:
    """Validator blocks executable or binary file extensions."""
    ok, errors = PatchValidator.validate_patch_scope(
        target_file="scripts/exploit.exe",
        allowed_files=["scripts/exploit.exe"],
    )
    assert ok is False
    assert any("extension .exe is not permitted" in e for e in errors)
