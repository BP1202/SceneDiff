"""Patch Exporter (Sprint 6 - Task 54).

Formats and exports unified Git patches with standard commit headers,
RFC email headers, and machine-readable metadata.
"""

from __future__ import annotations

from datetime import UTC, datetime
import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.repair.patch_generator import GeneratedPatch

from app.services.secret_shield import mask_string


class PatchExporter:
    """Exports generated patches into multiple industry-standard formats."""

    DEFAULT_AUTHOR = "IBM Bob <bob@scenediff.local>"

    @classmethod
    def export_git_patch(
        cls,
        patch: GeneratedPatch,
        summary: str,
        author: str | None = None,
        commit_message: str | None = None,
    ) -> str:
        """Format patch with Git commit headers (git-am / format-patch compatible).

        Args:
            patch: GeneratedPatch instance.
            summary: Short description of the fix.
            author: Git commit author string.
            commit_message: Optional extended commit body.

        Returns:
            String containing complete formatted .patch file.
        """
        now_str = datetime.now(UTC).strftime("%a, %d %b %Y %H:%M:%S +0000")
        author_header = author or cls.DEFAULT_AUTHOR
        body = commit_message or patch.description or "Automated fix by IBM Bob."

        clean_path = patch.target_file.replace("\\", "/").lstrip("/")
        churn_str = f" {clean_path} | {patch.lines_added + patch.lines_removed} "
        plus_part = "+" * min(patch.lines_added, 10)
        minus_part = "-" * min(patch.lines_removed, 10)
        churn_str += plus_part + minus_part
        stats_line = (
            f" 1 file changed, {patch.lines_added} insertions(+), "
            f"{patch.lines_removed} deletions(-)"
        )

        header_lines = [
            f"From {author_header} {now_str}",
            f"From: {author_header}",
            f"Date: {now_str}",
            f"Subject: [PATCH] {mask_string(summary)}",
            "",
            mask_string(body),
            "",
            "---",
            churn_str,
            stats_line,
            "",
        ]

        # Ensure diff_content starts immediately after header
        raw_diff = patch.diff_content.strip()
        return "\n".join(header_lines) + raw_diff + "\n-- \n2.42.0\n"

    @classmethod
    def export_json(cls, data: dict[str, Any]) -> str:
        """Export patch metadata as JSON."""
        return json.dumps(data, indent=2, default=str)

    @classmethod
    def export_markdown(
        cls,
        summary: str,
        diff_content: str,
        risk_level: str,
    ) -> str:
        """Export quick markdown preview snippet."""
        return (
            f"### Proposed Fix: {mask_string(summary)}\n\n"
            f"**Risk Level:** `{risk_level}`\n\n"
            f"```diff\n{diff_content.strip()}\n```\n"
        )
