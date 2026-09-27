"""Diff Parser Engine.

Parses Git unified diff output into structured dataclasses.

Supported languages (file extension detection):
- Python  (.py)
- TypeScript (.ts, .tsx)
- JavaScript (.js, .jsx, .mjs, .cjs)

No shell execution — pure Python parsing only.

Design notes:
- Uses dataclasses for immutable, typed output.
- Language is inferred from the file extension; unknown extensions yield
  UNKNOWN language, which is still parseable.
- Function-name extraction uses heuristic regex patterns per language.
  It does NOT execute or import the source code.
"""

from dataclasses import dataclass
import enum
import re

# ---------------------------------------------------------------------------
# Domain types
# ---------------------------------------------------------------------------


class Language(enum.StrEnum):
    """Source language inferred from file extension."""

    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ChangeHunk:
    """A single contiguous block of changes within a diff."""

    old_start: int
    old_count: int
    new_start: int
    new_count: int
    added_lines: tuple[str, ...]
    removed_lines: tuple[str, ...]
    context_lines: tuple[str, ...]


@dataclass(frozen=True)
class ParsedDiff:
    """Structured representation of a single file's diff."""

    file_path: str
    language: Language
    added_functions: tuple[str, ...]
    removed_functions: tuple[str, ...]
    modified_functions: tuple[str, ...]
    line_numbers: tuple[int, ...]
    hunks: tuple[ChangeHunk, ...]


# ---------------------------------------------------------------------------
# Language detection
# ---------------------------------------------------------------------------

_EXTENSION_TO_LANGUAGE: dict[str, Language] = {
    ".py": Language.PYTHON,
    ".ts": Language.TYPESCRIPT,
    ".tsx": Language.TYPESCRIPT,
    ".js": Language.JAVASCRIPT,
    ".jsx": Language.JAVASCRIPT,
    ".mjs": Language.JAVASCRIPT,
    ".cjs": Language.JAVASCRIPT,
}


def _detect_language(file_path: str) -> Language:
    """Infer Language from the file extension.

    Args:
        file_path: Repository-relative or absolute file path.

    Returns:
        Language enum value (UNKNOWN for unrecognised extensions).
    """
    dot_idx = file_path.rfind(".")
    if dot_idx == -1:
        return Language.UNKNOWN
    ext = file_path[dot_idx:].lower()
    return _EXTENSION_TO_LANGUAGE.get(ext, Language.UNKNOWN)


# ---------------------------------------------------------------------------
# Function-name extractors (per language)
# ---------------------------------------------------------------------------

# Python: def func_name( or async def func_name(
_PY_FUNC_RE = re.compile(r"^\+?\s*(?:async\s+)?def\s+([a-zA-Z_]\w*)\s*\(")

# TypeScript / JavaScript:
#   function name(   |  name = function(  |  name = () =>  |  name(  {
_TS_FUNC_RE = re.compile(
    r"^\+?\s*(?:"
    r"(?:export\s+)?(?:async\s+)?function\s+([a-zA-Z_$][\w$]*)\s*[\(<]"
    r"|(?:const|let|var)\s+([a-zA-Z_$][\w$]*)\s*=\s*(?:async\s+)?(?:function|\()"
    r"|(?:(?:public|private|protected|static|async|override)\s+)*([a-zA-Z_$][\w$]*)\s*\([^)]*\)\s*(?::\s*\S+\s*)?\{"
    r")"
)

_LANGUAGE_FUNC_RE: dict[Language, re.Pattern[str]] = {
    Language.PYTHON: _PY_FUNC_RE,
    Language.TYPESCRIPT: _TS_FUNC_RE,
    Language.JAVASCRIPT: _TS_FUNC_RE,
}


def _extract_function_names(lines: list[str], language: Language) -> list[str]:
    """Extract function names from a list of diff lines.

    Args:
        lines:    Lines from the diff (may include +/- prefix).
        language: Source language for regex selection.

    Returns:
        Deduplicated list of function name strings in appearance order.
    """
    pattern = _LANGUAGE_FUNC_RE.get(language)
    if pattern is None:
        return []

    seen: set[str] = set()
    names: list[str] = []
    for line in lines:
        m = pattern.match(line)
        if m:
            # Pick first non-None group
            name = next((g for g in m.groups() if g is not None), None)
            if name and name not in seen:
                seen.add(name)
                names.append(name)
    return names


# ---------------------------------------------------------------------------
# Hunk parsing
# ---------------------------------------------------------------------------

# Matches @@ -old_start[,old_count] +new_start[,new_count] @@
_HUNK_HEADER_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def _parse_hunk(hunk_header: str, hunk_lines: list[str]) -> ChangeHunk:
    """Build a ChangeHunk from a raw hunk header and its body lines.

    Args:
        hunk_header: The @@ … @@ header line.
        hunk_lines:  Lines that follow the header (including +/-/ prefix).

    Returns:
        ChangeHunk dataclass.
    """
    m = _HUNK_HEADER_RE.match(hunk_header)
    if not m:
        # Malformed header — return a zero-position hunk.
        return ChangeHunk(
            old_start=0,
            old_count=0,
            new_start=0,
            new_count=0,
            added_lines=(),
            removed_lines=(),
            context_lines=(),
        )

    old_start = int(m.group(1))
    old_count = int(m.group(2)) if m.group(2) is not None else 1
    new_start = int(m.group(3))
    new_count = int(m.group(4)) if m.group(4) is not None else 1

    added: list[str] = []
    removed: list[str] = []
    context: list[str] = []

    for line in hunk_lines:
        if line.startswith("+"):
            added.append(line[1:])
        elif line.startswith("-"):
            removed.append(line[1:])
        else:
            context.append(line[1:] if line.startswith(" ") else line)

    return ChangeHunk(
        old_start=old_start,
        old_count=old_count,
        new_start=new_start,
        new_count=new_count,
        added_lines=tuple(added),
        removed_lines=tuple(removed),
        context_lines=tuple(context),
    )


# ---------------------------------------------------------------------------
# Top-level diff parser
# ---------------------------------------------------------------------------

# Matches the --- a/path or +++ b/path file header lines.
_FILE_HEADER_RE = re.compile(r"^(?:---|\+\+\+)\s+(?:[ab]/)?(.+)$")
_DEV_NULL = "/dev/null"


def parse_diff(unified_diff: str) -> list[ParsedDiff]:
    """Parse a Git unified diff string into a list of ParsedDiff objects.

    Each file changed in the diff produces one ParsedDiff entry.  The parser
    is stateless and reads the diff text linearly without subprocess calls.

    Args:
        unified_diff: Raw output of ``git diff`` or ``git show``.

    Returns:
        List of ParsedDiff, one per modified file.  Empty list if the diff
        has no file changes.
    """
    results: list[ParsedDiff] = []

    current_file: str | None = None
    hunks: list[ChangeHunk] = []
    current_hunk_header: str | None = None
    current_hunk_lines: list[str] = []

    def _flush_hunk() -> None:
        nonlocal current_hunk_header, current_hunk_lines
        if current_hunk_header is not None:
            hunks.append(_parse_hunk(current_hunk_header, current_hunk_lines))
            current_hunk_header = None
            current_hunk_lines = []

    def _flush_file() -> None:
        nonlocal current_file, hunks
        _flush_hunk()
        if current_file is not None and current_file != _DEV_NULL:
            results.append(_build_parsed_diff(current_file, hunks))
        current_file = None
        hunks = []

    for raw_line in unified_diff.splitlines():
        if raw_line.startswith("diff --git"):
            _flush_file()
        elif raw_line.startswith("--- "):
            m = _FILE_HEADER_RE.match(raw_line)
            # --- line indicates the old file; we prefer +++ for the path.
            if m and current_file is None:
                current_file = m.group(1)
        elif raw_line.startswith("+++ "):
            m = _FILE_HEADER_RE.match(raw_line)
            if m:
                # +++ gives us the canonical new path.
                candidate = m.group(1)
                if candidate != _DEV_NULL:
                    current_file = candidate
        elif raw_line.startswith("@@ "):
            _flush_hunk()
            current_hunk_header = raw_line
        elif current_hunk_header is not None:
            current_hunk_lines.append(raw_line)

    _flush_file()
    return results


def _build_parsed_diff(file_path: str, hunks: list[ChangeHunk]) -> ParsedDiff:
    """Assemble a ParsedDiff from collected hunks.

    Args:
        file_path: Canonical file path (post-processing of +++ line).
        hunks:     All ChangeHunks parsed for this file.

    Returns:
        ParsedDiff with function classifications and line-number list.
    """
    language = _detect_language(file_path)

    all_added_lines: list[str] = []
    all_removed_lines: list[str] = []
    line_numbers: list[int] = []

    for hunk in hunks:
        all_added_lines.extend(hunk.added_lines)
        all_removed_lines.extend(hunk.removed_lines)
        # Record first line of each changed region.
        if hunk.new_start > 0:
            line_numbers.append(hunk.new_start)

    added_fns = _extract_function_names(
        [f"+{line}" for line in all_added_lines], language
    )
    removed_fns = _extract_function_names(
        [f"+{line}" for line in all_removed_lines], language
    )

    # Functions appearing in both added and removed sets are modifications.
    added_set = set(added_fns)
    removed_set = set(removed_fns)
    modified = sorted(added_set & removed_set)
    only_added = [f for f in added_fns if f not in removed_set]
    only_removed = [f for f in removed_fns if f not in added_set]

    return ParsedDiff(
        file_path=file_path,
        language=language,
        added_functions=tuple(only_added),
        removed_functions=tuple(only_removed),
        modified_functions=tuple(modified),
        line_numbers=tuple(sorted(set(line_numbers))),
        hunks=tuple(hunks),
    )
