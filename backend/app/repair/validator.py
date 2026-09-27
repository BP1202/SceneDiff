"""Patch Validator Engine (Sprint 6 - Task 50).

Validates generated patches before storage or export:
1. Unified diff syntax & hunk header integrity.
2. Python AST parse validation for .py files.
3. Secret Shield scanning (zero secret persistence).
4. Patch safety & scope enforcement (no .env, no unprompted deps, no migrations).
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
import os
from pathlib import Path
import re
from typing import Any

from app.services.secret_shield import contains_secret, mask_string

_HUNK_PATTERN = re.compile(
    r"^@@\s+-(?P<old_start>\d+)(?:,(?P<old_count>\d+))?\s+\+(?P<new_start>\d+)(?:,(?P<new_count>\d+))?\s+@@"
)

_ALLOWED_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".html",
    ".css",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".md",
    ".txt",
}

_FORBIDDEN_FILES = {
    ".env",
    ".env.local",
    ".env.production",
    ".env.staging",
    ".env.test",
}


@dataclass(frozen=True)
class ValidationResult:
    """Outcome of multi-layer patch validation."""

    is_valid: bool
    syntax_valid: bool
    ast_valid: bool
    secret_scan: str  # "passed" | "failed"
    scope_valid: bool
    errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert validation result to dictionary."""
        return {
            "is_valid": self.is_valid,
            "syntax_valid": self.syntax_valid,
            "ast_valid": self.ast_valid,
            "secret_scan": self.secret_scan,
            "scope_valid": self.scope_valid,
            "errors": [mask_string(e) for e in self.errors],
            "notes": [mask_string(n) for n in self.notes],
        }


class PatchValidator:
    """Multi-layer safety and syntax validator for Git patches."""

    @classmethod
    def validate_patch_syntax(cls, diff_content: str) -> tuple[bool, list[str]]:
        """Validate standard unified diff headers and hunk formatting.

        Args:
            diff_content: Raw patch string.

        Returns:
            Tuple of (is_syntax_valid, error_messages).
        """
        errors: list[str] = []
        if not diff_content or not diff_content.strip():
            return False, ["Patch content is empty"]

        lines = diff_content.splitlines()
        has_header = False
        has_hunk = False

        for line in lines:
            if (
                line.startswith("diff --git")
                or line.startswith("--- ")
                or line.startswith("+++ ")
            ):
                has_header = True
            elif line.startswith("@@"):
                has_hunk = True
                if not _HUNK_PATTERN.match(line):
                    errors.append(f"Malformed hunk header: {line}")
            elif has_hunk and line and line[0] not in ("+", "-", " ", "\\"):
                errors.append(f"Invalid diff line prefix: {line[:10]}")

        if not has_header:
            errors.append(
                "Missing standard unified diff header (diff --git or ---/+++)"
            )
        if not has_hunk:
            errors.append("Patch contains no valid hunks (@@ ... @@)")

        return len(errors) == 0, errors

    @classmethod
    def validate_python_ast(
        cls,
        target_file: str,
        diff_content: str,
    ) -> tuple[bool, list[str]]:
        """Validate Python syntax of modified hunks.

        Args:
            target_file: File name/path.
            diff_content: Unified diff.

        Returns:
            Tuple of (is_ast_valid, error_messages).
        """
        errors: list[str] = []
        if not target_file.endswith(".py"):
            return True, []  # Non-python files skip Python AST

        # Extract added and context lines from hunks to reconstruct candidate code
        lines = diff_content.splitlines()
        reconstructed_lines: list[str] = []
        in_hunk = False

        for line in lines:
            if line.startswith("@@"):
                in_hunk = True
                continue
            if not in_hunk:
                continue
            if (line.startswith("+") and not line.startswith("+++")) or line.startswith(
                " "
            ):
                reconstructed_lines.append(line[1:])
            # Omit deleted lines starting with "-"

        if not reconstructed_lines:
            return True, []

        candidate_code = "\n".join(reconstructed_lines)
        try:
            ast.parse(candidate_code)
        except SyntaxError as err:
            # Wrap in def stub if hunk was an indented function body
            try:
                wrapped_code = "def _stub():\n" + "\n".join(
                    f"    {ln}" for ln in reconstructed_lines
                )
                ast.parse(wrapped_code)
            except SyntaxError:
                errors.append(f"Python AST syntax error: {err.msg} (line {err.lineno})")

        return len(errors) == 0, errors

    @classmethod
    def validate_patch_scope(
        cls,
        target_file: str,
        allowed_files: list[str] | set[str] | None = None,
        reason: str = "",
    ) -> tuple[bool, list[str]]:
        """Enforce strict patch safety rules (Improvement 1).

        Rules:
        - No .env file modifications under any circumstances.
        - No requirements.txt changes unless reason mentions dependency.
        - No migration file generation (alembic/versions, migrations/).
        - Patch strictly restricted to expected culprit file(s).
        - File extension must be in allowed list (no executables/binaries).
        """
        errors: list[str] = []
        norm = target_file.replace("\\", "/").strip().lstrip("/")
        base_name = os.path.basename(norm).lower()

        # 1. No .env modifications
        if base_name in _FORBIDDEN_FILES or base_name.startswith(".env"):
            errors.append(
                f"Security violation: modifications to {base_name} are blocked"
            )

        # 2. Dependency file rule
        is_dep_file = base_name in (
            "requirements.txt",
            "pyproject.toml",
            "package.json",
        )
        has_dep_reason = "dep" in reason.lower() or "package" in reason.lower()
        if is_dep_file and not has_dep_reason:
            errors.append(
                f"Scope violation: {base_name} modified without dependency root cause"
            )

        # 3. No migrations inside patch
        in_migrations = (
            "alembic/versions" in norm
            or "/migrations/" in norm
            or norm.startswith("migrations/")
        )
        if in_migrations:
            errors.append(
                "Scope violation: database migrations inside patch are prohibited"
            )

        # 4. Scope confinement to culprit file(s)
        if allowed_files:
            norm_allowed = {
                f.replace("\\", "/").strip().lstrip("/") for f in allowed_files
            }
            if norm not in norm_allowed and base_name not in norm_allowed:
                allowed_list = list(norm_allowed)
                errors.append(
                    f"Scope violation: {norm} is not in culprit files {allowed_list}"
                )

        # 5. Extension check
        ext = Path(norm).suffix.lower()
        if ext and ext not in _ALLOWED_EXTENSIONS:
            errors.append(f"Security violation: file extension {ext} is not permitted")

        return len(errors) == 0, errors

    @classmethod
    def validate(
        cls,
        target_file: str,
        diff_content: str,
        allowed_files: list[str] | set[str] | None = None,
        root_cause_reason: str = "",
    ) -> ValidationResult:
        """Run all validation layers on a generated patch."""
        all_errors: list[str] = []
        notes: list[str] = []

        # 1. Syntax check
        syntax_ok, syntax_errors = cls.validate_patch_syntax(diff_content)
        all_errors.extend(syntax_errors)
        if syntax_ok:
            notes.append("Unified diff syntax passed")

        # 2. AST check
        ast_ok, ast_errors = cls.validate_python_ast(target_file, diff_content)
        all_errors.extend(ast_errors)
        if ast_ok and target_file.endswith(".py"):
            notes.append("Python AST parsing passed")

        # 3. Secret Shield check
        secret_detected = contains_secret(diff_content)
        if secret_detected:
            all_errors.append(
                "Secret Shield violation: credentials or tokens detected in patch"
            )
            secret_scan = "failed"  # noqa: S105
        else:
            secret_scan = "passed"  # noqa: S105
            notes.append("Secret Shield scan passed (zero secrets)")

        # 4. Scope check
        scope_ok, scope_errors = cls.validate_patch_scope(
            target_file=target_file,
            allowed_files=allowed_files,
            reason=root_cause_reason,
        )
        all_errors.extend(scope_errors)
        if scope_ok:
            notes.append("Patch safety and scope confinement passed")

        is_valid = (
            syntax_ok
            and ast_ok
            and (secret_scan == "passed")  # noqa: S105
            and scope_ok
        )

        return ValidationResult(
            is_valid=is_valid,
            syntax_valid=syntax_ok,
            ast_valid=ast_ok,
            secret_scan=secret_scan,
            scope_valid=scope_ok,
            errors=all_errors,
            notes=notes,
        )
