"""Behavior Hash Engine.

Generates deterministic SHA-256 hashes from code behavior signatures.

Design rules:
- Whitespace is stripped and normalized before hashing.
- Comment lines (# and //) are removed before hashing.
- Input components are sorted for stable ordering.
- Output is a 64-character lowercase hex digest.
- Deterministic across platforms and Python versions.

No external dependencies — stdlib only.
"""

import hashlib
import re

# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------

# Matches whole-line Python-style comments (# …) and
# C-style single-line comments (// …).
_COMMENT_LINE_RE = re.compile(r"^\s*(#|//).*$", re.MULTILINE)

# Matches inline trailing comments — // … at end of a code line.
_INLINE_COMMENT_RE = re.compile(r"\s*(//|#)[^\n]*")

# Collapses multiple whitespace characters (including newlines) to a single
# space, making the hash insensitive to formatting differences.
_WHITESPACE_RE = re.compile(r"\s+")


def _normalize(text: str) -> str:
    """Strip comments and collapse whitespace for platform-stable hashing.

    Args:
        text: Raw source code or diff snippet.

    Returns:
        Normalized text suitable for deterministic hashing.
    """
    # Remove whole-line comments first to avoid stripping code after them.
    text = _COMMENT_LINE_RE.sub("", text)
    # Remove inline trailing comments (e.g. x = 1  # set x).
    text = _INLINE_COMMENT_RE.sub("", text)
    # Collapse all whitespace runs to a single space and strip edges.
    return _WHITESPACE_RE.sub(" ", text).strip()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_behavior_hash(
    file_path: str,
    function_name: str,
    diff_snippet: str,
) -> str:
    """Return a deterministic SHA-256 hash identifying this behavior change.

    The hash is stable as long as the logical content is unchanged —
    formatting, whitespace, and comments do not affect the output.

    Inputs are sorted before concatenation so that the hash is insensitive
    to the order in which components are supplied by callers.

    Args:
        file_path:     Repository-relative path of the changed file.
        function_name: Name of the changed function (or empty string if N/A).
        diff_snippet:  The unified diff hunk or extracted code fragment.

    Returns:
        64-character lowercase hex SHA-256 digest.

    Example:
        >>> h = generate_behavior_hash(  # noqa: E501
        ...     "src/app.py", "handle_request", "- x = 1\\n+ x = 2"
        ... )
        >>> len(h)
        64
        >>> h == generate_behavior_hash("src/app.py", "handle_request", "- x=1\\n+ x=2")
        True
    """
    normalized_path = _normalize(file_path)
    normalized_function = _normalize(function_name)
    normalized_diff = _normalize(diff_snippet)

    # Sort components so callers don't need to worry about argument order.
    components = sorted([normalized_path, normalized_function, normalized_diff])
    payload = "|".join(components)

    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def hash_metadata(metadata: dict[str, object]) -> str:
    """Return a deterministic hash of a flat or nested metadata dictionary.

    Keys and values are sorted and normalized before hashing so that dict
    insertion order does not affect the result.

    Args:
        metadata: Arbitrary key-value metadata dict (values must be str-able).

    Returns:
        64-character lowercase hex SHA-256 digest.
    """
    # Sort by key to achieve stable ordering regardless of insertion order.
    parts = [f"{k}={_normalize(str(v))}" for k, v in sorted(metadata.items())]
    payload = "|".join(parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
