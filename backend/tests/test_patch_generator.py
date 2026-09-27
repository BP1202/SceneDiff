"""Unit tests for Patch Generator Engine (Sprint 6 - Task 49)."""

from __future__ import annotations

from app.repair.context import CodeContext
from app.repair.patch_generator import (
    GeneratedPatch,
    MockPatchProvider,
    OllamaPatchProvider,
    TemplatePatchProvider,
)
from app.repair.planner import RepairAction, RepairPlan


def _sample_plan(
    summary: str = "Fix validate_token null handling",
    target_file: str = "app/auth/login.py",
    target_function: str = "validate_token",
    actions: list[RepairAction] | None = None,
) -> RepairPlan:
    acts = actions or [
        RepairAction(
            step=1,
            description=f"Action for {summary}",
            rationale="Rationale",
        )
    ]
    return RepairPlan(
        summary=summary,
        target_file=target_file,
        target_function=target_function,
        actions=acts,
    )


def test_generated_patch_to_dict_and_masking() -> None:
    """GeneratedPatch masks secrets in diff content and description."""
    secret_token = "ghp_123456789012345678901234567890123456"
    patch = GeneratedPatch(
        target_file="app/auth/login.py",
        diff_content=(
            f"diff --git a/app/login.py b/app/login.py\n+ token = '{secret_token}'"
        ),
        lines_added=1,
        lines_removed=0,
        provider="TemplatePatchProvider",
        description=f"Fix {secret_token} leakage",
    )
    d = patch.to_dict()
    assert d["target_file"] == "app/auth/login.py"
    assert "ghp_" not in d["diff_content"]
    assert "[REDACTED]" in d["diff_content"]
    assert "[REDACTED]" in d["description"]


def test_template_provider_null_guard_with_return() -> None:
    """TemplatePatchProvider inserts null check before return statement."""
    provider = TemplatePatchProvider()
    plan = _sample_plan("Fix validate_token null handling")
    fn_code = (
        "def validate_token(token):\n    payload = decode(token)\n    return payload"
    )
    context = CodeContext(
        file_path="app/auth/login.py",
        function_name="validate_token",
        before="import os",
        target=fn_code,
        after="",
        start_line=10,
        end_line=13,
    )
    patch = provider.generate(plan, context)
    assert patch.target_file == "app/auth/login.py"
    assert "diff --git a/app/auth/login.py b/app/auth/login.py" in patch.diff_content
    assert "+    if payload is None:" in patch.diff_content
    assert "raise ValueError" in patch.diff_content
    assert patch.lines_added >= 2


def test_template_provider_null_guard_without_return() -> None:
    """TemplatePatchProvider inserts guard at head of function if no return."""
    provider = TemplatePatchProvider()
    plan = _sample_plan("Fix validate_token null handling")
    context = CodeContext(
        file_path="app/auth/login.py",
        function_name="validate_token",
        before="",
        target="def validate_token(*args, **kwargs):\n    pass",
        after="",
        start_line=1,
        end_line=2,
    )
    patch = provider.generate(plan, context)
    assert "Missing required arguments" in patch.diff_content
    assert patch.lines_added > 0


def test_template_provider_500_exception_handler() -> None:
    """TemplatePatchProvider wraps operation in try-except for 500 server error."""
    provider = TemplatePatchProvider()
    plan = _sample_plan(
        summary="Remediate 500 server error in payment",
        target_file="app/api/checkout.py",
        target_function="charge",
    )
    context = CodeContext(
        file_path="app/api/checkout.py",
        function_name="charge",
        before="",
        target="def charge():\n    execute_operation()\n    return True",
        after="",
        start_line=5,
        end_line=8,
    )
    patch = provider.generate(plan, context)
    assert "+    try:" in patch.diff_content
    assert "+    except Exception as exc:" in patch.diff_content


def test_template_provider_auth_guard() -> None:
    """TemplatePatchProvider generates auth verification diff."""
    provider = TemplatePatchProvider()
    plan = _sample_plan(
        summary="Fix auth verification token check",
        target_file="app/auth/jwt.py",
        target_function="verify_session",
    )
    context = CodeContext(
        file_path="app/auth/jwt.py",
        function_name="verify_session",
        before="",
        target="def verify_session(token):\n    payload = decode(token)",
        after="",
        start_line=1,
        end_line=2,
    )
    patch = provider.generate(plan, context)
    assert "AuthenticationError" in patch.diff_content


def test_template_provider_generic_fallback() -> None:
    """TemplatePatchProvider generates defensive invariant check."""
    provider = TemplatePatchProvider()
    plan = _sample_plan(
        summary="Repair logic in calculate",
        target_file="app/math/calc.py",
        target_function="compute",
    )
    context = CodeContext(
        file_path="app/math/calc.py",
        function_name="compute",
        before="",
        target="def compute():\n    return None",
        after="",
        start_line=1,
        end_line=2,
    )
    patch = provider.generate(plan, context)
    assert "Invariant satisfied" in patch.diff_content


def test_mock_patch_provider_custom_diff() -> None:
    """MockPatchProvider outputs predefined custom diff."""
    custom = "diff --git a/test.py b/test.py\n@@ -1 +1 @@\n-old\n+new"
    mock = MockPatchProvider(predefined_diff=custom)
    patch = mock.generate(
        _sample_plan(), CodeContext("test.py", None, "", "", "", 1, 1)
    )
    assert patch.diff_content == custom
    assert patch.provider == "MockPatchProvider"


def test_mock_patch_provider_default_diff() -> None:
    """MockPatchProvider generates default diff when none is provided."""
    mock = MockPatchProvider()
    patch = mock.generate(
        _sample_plan(), CodeContext("app/login.py", None, "", "", "", 1, 1)
    )
    assert "mock fix" in patch.diff_content
    assert patch.target_file == "app/auth/login.py"


def test_ollama_patch_provider_fallback() -> None:
    """OllamaPatchProvider uses template fallback."""
    provider = OllamaPatchProvider()
    plan = _sample_plan()
    context = CodeContext(
        "app/auth/login.py",
        "validate_token",
        "",
        "def validate_token(): return True",
        "",
        1,
        1,
    )
    patch = provider.generate(plan, context)
    assert patch.provider == "OllamaPatchProvider"
    assert "OllamaProvider" in patch.description
