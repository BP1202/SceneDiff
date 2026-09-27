"""Unit tests for Patch Exporter (Sprint 6 - Task 54)."""

from __future__ import annotations

import json

from app.repair.exporter import PatchExporter
from app.repair.patch_generator import GeneratedPatch


def _sample_patch() -> GeneratedPatch:
    return GeneratedPatch(
        target_file="app/auth/login.py",
        diff_content=(
            "diff --git a/app/auth/login.py b/app/auth/login.py\n"
            "@@ -1,2 +1,3 @@\n+new_line\n"
        ),
        lines_added=1,
        lines_removed=0,
        provider="TemplatePatchProvider",
        description="Fix login null pointer",
    )


def test_exporter_git_patch_headers() -> None:
    """PatchExporter creates git-am compatible email headers."""
    patch = _sample_patch()
    exported = PatchExporter.export_git_patch(patch, summary="Fix login null guard")
    assert "From: IBM Bob <bob@scenediff.local>" in exported
    assert "Subject: [PATCH] Fix login null guard" in exported
    assert "1 file changed, 1 insertions(+), 0 deletions(-)" in exported
    assert "diff --git a/app/auth/login.py b/app/auth/login.py" in exported
    assert "-- \n2.42.0" in exported


def test_exporter_git_patch_custom_author_and_commit_message() -> None:
    """PatchExporter respects custom author and body message."""
    patch = _sample_patch()
    exported = PatchExporter.export_git_patch(
        patch,
        summary="Custom Fix",
        author="Alice Engineer <alice@company.com>",
        commit_message="Detailed rationale for the patch",
    )
    assert "From: Alice Engineer <alice@company.com>" in exported
    assert "Detailed rationale for the patch" in exported


def test_exporter_git_patch_secret_masking() -> None:
    """PatchExporter masks secrets in subject and body."""
    patch = _sample_patch()
    exported = PatchExporter.export_git_patch(
        patch,
        summary="Fix ghp_123456789012345678901234567890123456 exposure",
        commit_message="Removed secret AKIA1234567890123456",
    )
    assert "ghp_" not in exported
    assert "AKIA" not in exported
    assert "[REDACTED]" in exported


def test_exporter_json() -> None:
    """PatchExporter exports valid JSON string."""
    data = {"report_id": "test-123", "target_file": "main.py"}
    res = PatchExporter.export_json(data)
    parsed = json.loads(res)
    assert parsed["report_id"] == "test-123"


def test_exporter_markdown() -> None:
    """PatchExporter creates markdown preview with diff fenced code block."""
    md = PatchExporter.export_markdown(
        summary="Fix auth issue",
        diff_content="diff --git a/a b/b\n+fix",
        risk_level="HIGH",
    )
    assert "### Proposed Fix: Fix auth issue" in md
    assert "**Risk Level:** `HIGH`" in md
    assert "```diff\ndiff --git a/a b/b\n+fix\n```" in md
