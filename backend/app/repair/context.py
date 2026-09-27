"""Code Context Retriever (Sprint 6 - Task 48).

Extracts source code context and boundaries for target files and functions
to guide accurate patch generation. Strictly read-only and safe.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
from typing import Any

from app.services.secret_shield import mask_string


@dataclass(frozen=True)
class CodeContext:
    """Surrounding source code context for a target file/function."""

    file_path: str
    function_name: str | None
    before: str
    target: str
    after: str
    start_line: int
    end_line: int

    def to_dict(self) -> dict[str, Any]:
        """Convert code context to dictionary with masked content."""
        return {
            "file_path": self.file_path,
            "function_name": self.function_name,
            "before": mask_string(self.before),
            "target": mask_string(self.target),
            "after": mask_string(self.after),
            "start_line": self.start_line,
            "end_line": self.end_line,
        }

    @property
    def full_extracted_code(self) -> str:
        """Combine before, target, and after into contiguous block."""
        parts = [p for p in (self.before, self.target, self.after) if p]
        return "\n".join(parts)


class CodeContextRetriever:
    """Secure, read-only retriever for extracting surrounding code context."""

    def __init__(
        self,
        base_dir: str | Path | None = None,
        virtual_files: dict[str, str] | None = None,
    ) -> None:
        """Initialize retriever with base directory and optional virtual files.

        Args:
            base_dir: Allowed root directory for file reads.
            virtual_files: Optional mapping of file paths to content
                (for testing/mocking).
        """
        self.base_dir = Path(base_dir).resolve() if base_dir else None
        self.virtual_files: dict[str, str] = virtual_files or {}

    def _sanitize_path(self, relative_path: str) -> Path | None:
        """Validate and resolve relative path to prevent traversal attacks.

        Args:
            relative_path: File path string.

        Returns:
            Resolved Path within base_dir, or None if invalid.
        """
        norm = os.path.normpath(relative_path).replace("\\", "/")
        if ".." in norm.split("/"):
            raise ValueError(f"Path traversal detected: {relative_path}")
        if os.path.isabs(norm) and not self.base_dir:
            return Path(norm)
        if self.base_dir:
            target = (self.base_dir / norm).resolve()
            if not str(target).startswith(str(self.base_dir)):
                raise ValueError(
                    f"Access outside base directory denied: {relative_path}"
                )
            return target
        return Path(norm)

    def retrieve(
        self,
        file_path: str,
        function_name: str | None = None,
        context_lines: int = 10,
    ) -> CodeContext:
        """Retrieve code context for a target file and optional function.

        Args:
            file_path: Target relative or repo file path.
            function_name: Optional target function name to locate.
            context_lines: Number of surrounding lines before and after.

        Returns:
            CodeContext containing before, target, and after code slices.
        """
        norm_path = file_path.replace("\\", "/").lstrip("/")

        # Check virtual files first
        content: str | None = None
        if norm_path in self.virtual_files:
            content = self.virtual_files[norm_path]
        elif file_path in self.virtual_files:
            content = self.virtual_files[file_path]
        else:
            resolved = self._sanitize_path(file_path)
            if resolved and resolved.is_file():
                content = resolved.read_text(encoding="utf-8")
            else:
                # If file does not exist on disk, return empty context
                return CodeContext(
                    file_path=file_path,
                    function_name=function_name,
                    before="",
                    target="",
                    after="",
                    start_line=1,
                    end_line=1,
                )

        lines = content.splitlines()
        total_lines = len(lines)
        if total_lines == 0:
            return CodeContext(
                file_path=file_path,
                function_name=function_name,
                before="",
                target="",
                after="",
                start_line=1,
                end_line=1,
            )

        if not function_name:
            # Return initial window
            window_end = min(total_lines, context_lines * 2)
            return CodeContext(
                file_path=file_path,
                function_name=None,
                before="",
                target="\n".join(lines[:window_end]),
                after="\n".join(lines[window_end : window_end + context_lines]),
                start_line=1,
                end_line=window_end,
            )

        # Locate function definition (supports Python, JS/TS, Go, etc.)
        pattern_str = (
            rf"^\s*(def|async def|function|func|public function)\s+"
            rf"{re.escape(function_name)}\b"
        )
        fn_pattern = re.compile(pattern_str)
        fn_start = -1
        for idx, line in enumerate(lines):
            if fn_pattern.search(line):
                fn_start = idx
                break

        if fn_start == -1:
            # Fallback search for bare name
            for idx, line in enumerate(lines):
                if function_name in line:
                    fn_start = idx
                    break

        if fn_start == -1:
            # Function not found; return head of file
            target_slice = "\n".join(lines[: min(total_lines, 20)])
            return CodeContext(
                file_path=file_path,
                function_name=function_name,
                before="",
                target=target_slice,
                after="",
                start_line=1,
                end_line=min(total_lines, 20),
            )

        # Find function end (indentation based for Python or brace/line heuristics)
        start_indent = len(lines[fn_start]) - len(lines[fn_start].lstrip())
        fn_end = fn_start
        for idx in range(fn_start + 1, total_lines):
            line = lines[idx]
            if not line.strip():
                fn_end = idx
                continue
            cur_indent = len(line) - len(line.lstrip())
            if cur_indent <= start_indent:
                break
            fn_end = idx

        before_start = max(0, fn_start - context_lines)
        before_lines = lines[before_start:fn_start]

        target_lines = lines[fn_start : fn_end + 1]

        after_end = min(total_lines, fn_end + 1 + context_lines)
        after_lines = lines[fn_end + 1 : after_end]

        return CodeContext(
            file_path=file_path,
            function_name=function_name,
            before="\n".join(before_lines),
            target="\n".join(target_lines),
            after="\n".join(after_lines),
            start_line=fn_start + 1,
            end_line=fn_end + 1,
        )
