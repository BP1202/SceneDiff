"""Unit tests for Code Context Retriever (Sprint 6 - Task 48)."""

from __future__ import annotations

import pytest

from app.repair.context import CodeContext, CodeContextRetriever

SAMPLE_CODE = """import os
import sys

def helper():
    return True

def validate_token(token: str) -> dict:
    # validate payload
    payload = decode_jwt(token)
    if not payload:
        return None
    return payload

def finish():
    print("Done")
"""


def test_code_context_to_dict_and_property() -> None:
    """CodeContext serializes to dict and concatenates full code."""
    ctx = CodeContext(
        file_path="app/auth/login.py",
        function_name="validate_token",
        before="import os",
        target="def validate_token():\n    return None",
        after="def finish(): pass",
        start_line=8,
        end_line=9,
    )
    d = ctx.to_dict()
    assert d["file_path"] == "app/auth/login.py"
    assert d["function_name"] == "validate_token"
    assert d["start_line"] == 8
    assert d["end_line"] == 9
    assert "def validate_token" in ctx.full_extracted_code


def test_context_retriever_locates_function() -> None:
    """CodeContextRetriever extracts function and surrounding context."""
    retriever = CodeContextRetriever(virtual_files={"app/auth/login.py": SAMPLE_CODE})
    ctx = retriever.retrieve("app/auth/login.py", "validate_token", context_lines=4)
    assert ctx.function_name == "validate_token"
    assert "def validate_token(token: str)" in ctx.target
    assert "return payload" in ctx.target
    assert "def helper" in ctx.before or "import" in ctx.before
    assert "def finish" in ctx.after
    assert ctx.start_line == 7
    assert ctx.end_line in (12, 13)


def test_context_retriever_no_function_specified() -> None:
    """CodeContextRetriever retrieves top of file when function_name is None."""
    retriever = CodeContextRetriever(virtual_files={"app/main.py": SAMPLE_CODE})
    ctx = retriever.retrieve("app/main.py", None, context_lines=3)
    assert ctx.function_name is None
    assert ctx.start_line == 1
    assert "import os" in ctx.target


def test_context_retriever_missing_function() -> None:
    """CodeContextRetriever gracefully handles function not found."""
    retriever = CodeContextRetriever(virtual_files={"app/auth/login.py": SAMPLE_CODE})
    ctx = retriever.retrieve("app/auth/login.py", "nonexistent_fn")
    assert ctx.function_name == "nonexistent_fn"
    assert "import os" in ctx.target


def test_context_retriever_empty_file() -> None:
    """CodeContextRetriever handles empty file safely."""
    retriever = CodeContextRetriever(virtual_files={"app/empty.py": ""})
    ctx = retriever.retrieve("app/empty.py", "foo")
    assert ctx.target == ""
    assert ctx.before == ""
    assert ctx.after == ""


def test_context_retriever_missing_file_on_disk() -> None:
    """CodeContextRetriever returns empty context if file doesn't exist."""
    retriever = CodeContextRetriever(base_dir=None)
    ctx = retriever.retrieve("does_not_exist_xyz.py", "foo")
    assert ctx.target == ""


def test_context_retriever_path_traversal_blocked() -> None:
    """CodeContextRetriever raises ValueError when path traversal is attempted."""
    retriever = CodeContextRetriever()
    with pytest.raises(ValueError, match="Path traversal detected"):
        retriever.retrieve("../../../etc/passwd", "read")


def test_context_retriever_masking_in_to_dict() -> None:
    """CodeContext masks secrets in before/target/after strings."""
    secret_code = "SECRET_KEY = 'AKIA1234567890123456'"
    ctx = CodeContext(
        file_path="config.py",
        function_name="load_key",
        before=secret_code,
        target="def load_key(): pass",
        after="",
        start_line=1,
        end_line=2,
    )
    d = ctx.to_dict()
    assert "AKIA" not in d["before"]
    assert "[REDACTED]" in d["before"]
