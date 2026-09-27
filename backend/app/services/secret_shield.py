"""Secret Shield — metadata masking utility.

Scans arbitrary string values (and recursively dict/list structures) for
secret patterns and replaces matched values with a safe placeholder.

Supported detectors:
- JWT tokens (three-part base64url format)
- AWS Access Keys (AKIA…)
- GitHub personal access tokens (ghp_, gho_, ghs_, ghr_)
- Bearer / Authorization header values
- Passwords (key=value patterns with "password" in the key)
- Generic API keys (key=value patterns with "api_key", "apikey", "token")
- OAuth tokens
- Cookie header values
- SSH private key blocks

Design rules:
- Patterns are compiled once at module import.
- Masking never logs the original secret value, only the pattern category.
- Returns new objects; input is never mutated.
- All public functions are pure (no side effects).

This module contains NO AI-generated secret detection — only deterministic
regex patterns reviewed by the engineering team.
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

_MASK = "[REDACTED]"

# ---------------------------------------------------------------------------
# Pattern registry — each entry is (category_name, compiled_regex).
# Patterns match the full secret value or key=value pair.
# ---------------------------------------------------------------------------

_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    # JWT: header.payload.signature (base64url segments, no padding)
    (
        "JWT",
        re.compile(
            r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+",
            re.IGNORECASE,
        ),
    ),
    # AWS Access Key ID
    (
        "AWS_ACCESS_KEY",
        re.compile(r"\b(AKIA|AGPA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}\b"),
    ),
    # AWS Secret Access Key (40-char alphanumeric+/+)
    (
        "AWS_SECRET_KEY",
        re.compile(r"(?<![A-Za-z0-9/+=])[A-Za-z0-9/+=]{40}(?![A-Za-z0-9/+=])"),
    ),
    # GitHub tokens (ghp_, gho_, ghs_, ghr_, github_pat_)
    (
        "GITHUB_TOKEN",
        re.compile(r"\b(ghp|gho|ghs|ghr|github_pat)_[A-Za-z0-9_]{36,255}\b"),
    ),
    # Bearer / Authorization header values
    (
        "BEARER_TOKEN",
        re.compile(
            r"(?i)bearer\s+[A-Za-z0-9\-._~+/]+=*",
            re.IGNORECASE,
        ),
    ),
    # OAuth tokens (oauth_token=… or access_token=…)
    (
        "OAUTH_TOKEN",
        re.compile(
            r"(?i)(?:oauth_token|access_token|refresh_token)\s*[:=]\s*[\"']?[A-Za-z0-9\-._~+/]+=*[\"']?",
            re.IGNORECASE,
        ),
    ),
    # Generic API key patterns (api_key=, apikey=, x-api-key:)
    (
        "API_KEY",
        re.compile(
            r"(?i)(?:api[_-]?key|x-api-key)\s*[:=]\s*[\"']?[A-Za-z0-9\-._~+/]{16,}[\"']?",
            re.IGNORECASE,
        ),
    ),
    # Password key=value patterns
    (
        "PASSWORD",
        re.compile(
            r"(?i)password\s*[:=]\s*[\"']?[^\s\"']{4,}[\"']?",
            re.IGNORECASE,
        ),
    ),
    # Cookie header values
    (
        "COOKIE",
        re.compile(
            r"(?i)(?:cookie|set-cookie)\s*:\s*.+",
            re.IGNORECASE,
        ),
    ),
    # SSH private key block
    (
        "SSH_PRIVATE_KEY",
        re.compile(
            r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"
            r".*?"
            r"-----END (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
            re.DOTALL | re.IGNORECASE,
        ),
    ),
]


# ---------------------------------------------------------------------------
# Core masking functions
# ---------------------------------------------------------------------------


def mask_string(value: str, log_detections: bool = False) -> str:
    """Scan a string for secrets and replace all matches with [REDACTED].

    Args:
        value:           The raw string to scan.
        log_detections:  If True, log a WARNING with the pattern category
                         (never the matched value) when a secret is detected.

    Returns:
        String with all detected secrets replaced by ``[REDACTED]``.
    """
    result = value
    for category, pattern in _PATTERNS:
        if pattern.search(result):
            if log_detections:
                logger.warning("Secret Shield: detected pattern category=%s", category)
            result = pattern.sub(_MASK, result)
    return result


def mask_metadata(
    metadata: dict[str, Any],
    log_detections: bool = False,
) -> dict[str, Any]:
    """Recursively scan and mask secrets in a metadata dictionary.

    Traverses dict and list values depth-first.  Non-string leaf values are
    left unchanged.  Input is never mutated; a new dict is always returned.

    Args:
        metadata:        Arbitrary metadata dict.
        log_detections:  Passed through to mask_string for logging control.

    Returns:
        Deep copy of ``metadata`` with all secret strings replaced.
    """
    return {k: _mask_value(v, log_detections) for k, v in metadata.items()}


def _mask_value(value: Any, log_detections: bool) -> Any:  # noqa: ANN401
    """Recursively mask a single value.

    Args:
        value:           Any value — str, dict, list, or other.
        log_detections:  Passed through to mask_string.

    Returns:
        Masked version of the value (same type where possible).
    """
    if isinstance(value, str):
        return mask_string(value, log_detections=log_detections)
    if isinstance(value, dict):
        return {k: _mask_value(v, log_detections) for k, v in value.items()}
    if isinstance(value, list):
        return [_mask_value(item, log_detections) for item in value]
    return value


def contains_secret(value: str) -> bool:
    """Return True if any secret pattern matches in ``value``.

    Intended for use when ``SECRET_SHIELD_BLOCK_ON_DETECT`` is True and the
    caller wants to reject a trace rather than mask it.

    Args:
        value: String to test.

    Returns:
        True if at least one secret pattern matches.
    """
    return any(pattern.search(value) for _, pattern in _PATTERNS)


def contains_secret_in_metadata(metadata: dict[str, Any]) -> bool:
    """Return True if any secret pattern is found anywhere in ``metadata``.

    Recursively checks string values inside dicts and lists.

    Args:
        metadata: Arbitrary metadata dict.

    Returns:
        True if at least one secret is detected.
    """
    return any(_value_contains_secret(v) for v in metadata.values())


def _value_contains_secret(value: Any) -> bool:  # noqa: ANN401
    """Recursive helper for contains_secret_in_metadata."""
    if isinstance(value, str):
        return contains_secret(value)
    if isinstance(value, dict):
        return any(_value_contains_secret(v) for v in value.values())
    if isinstance(value, list):
        return any(_value_contains_secret(item) for item in value)
    return False
