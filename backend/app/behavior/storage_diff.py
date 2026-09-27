"""Task: Storage Diff Engine (LocalStorage / SessionStorage / Cookies).

Observes browser storage changes across user journey checkpoints.
Enforces Secret Shield:
- Cookie values are always redacted.
- Sensitive localStorage tokens are masked.
- Never reveals raw secret credentials in diff output.
"""

from __future__ import annotations

from typing import Any

from app.behavior.severity import BehaviorDivergence, SeverityLevel

_AUTH_KEY_SUBSTRINGS = ("auth", "token", "session", "jwt", "key", "secret", "user")


def _is_auth_key(key: str) -> bool:
    low = key.lower()
    return any(sub in low for sub in _AUTH_KEY_SUBSTRINGS)


def compare_storage_snapshots(
    base_snapshots: list[dict[str, Any]],
    head_snapshots: list[dict[str, Any]],
) -> list[BehaviorDivergence]:
    """Compare storage snapshots across routes between Base and Head.

    Args:
        base_snapshots: Storage snapshots from Base trace.
        head_snapshots: Storage snapshots from Head trace.

    Returns:
        List of detected BehaviorDivergence items.
    """
    divergences: list[BehaviorDivergence] = []

    base_map = {s.get("route", "/"): s for s in base_snapshots}
    head_map = {s.get("route", "/"): s for s in head_snapshots}

    common_routes = set(base_map.keys()) & set(head_map.keys())
    for route in sorted(common_routes):
        b = base_map[route]
        h = head_map[route]

        # 1. LocalStorage key set diff
        b_local_keys = set(b.get("local_storage_keys", []))
        h_local_keys = set(h.get("local_storage_keys", []))

        removed_local = b_local_keys - h_local_keys
        added_local = h_local_keys - b_local_keys

        for key in sorted(removed_local):
            sev = SeverityLevel.HIGH if _is_auth_key(key) else SeverityLevel.LOW
            divergences.append(
                BehaviorDivergence(
                    category="storage",
                    severity=sev,
                    route=route,
                    event_type="LOCAL_STORAGE_KEY_REMOVED",
                    title=f"LocalStorage key '{key}' removed on {route}",
                    description=(
                        f"Key '{key}' was present in Base local storage on '{route}' "
                        "but was removed in Head."
                    ),
                    base_value={"key": key},
                    head_value=None,
                    evidence={"is_auth_key": _is_auth_key(key)},
                )
            )

        for key in sorted(added_local):
            divergences.append(
                BehaviorDivergence(
                    category="storage",
                    severity=SeverityLevel.LOW,
                    route=route,
                    event_type="LOCAL_STORAGE_KEY_ADDED",
                    title=f"LocalStorage key '{key}' added on {route}",
                    description=f"New key '{key}' written to local storage in Head.",
                    base_value=None,
                    head_value={"key": key},
                    evidence={"is_auth_key": _is_auth_key(key)},
                )
            )

        # 2. SessionStorage key set diff
        b_session_keys = set(b.get("session_storage_keys", []))
        h_session_keys = set(h.get("session_storage_keys", []))

        removed_session = b_session_keys - h_session_keys
        added_session = h_session_keys - b_session_keys

        for key in sorted(removed_session):
            sev = SeverityLevel.MEDIUM if _is_auth_key(key) else SeverityLevel.LOW
            divergences.append(
                BehaviorDivergence(
                    category="storage",
                    severity=sev,
                    route=route,
                    event_type="SESSION_STORAGE_KEY_REMOVED",
                    title=f"SessionStorage key '{key}' removed on {route}",
                    description=(
                        f"Key '{key}' removed from session storage on '{route}'."
                    ),
                    base_value={"key": key},
                    head_value=None,
                )
            )

        for key in sorted(added_session):
            divergences.append(
                BehaviorDivergence(
                    category="storage",
                    severity=SeverityLevel.LOW,
                    route=route,
                    event_type="SESSION_STORAGE_KEY_ADDED",
                    title=f"SessionStorage key '{key}' added on {route}",
                    description=f"New session storage key '{key}' on '{route}'.",
                    base_value=None,
                    head_value={"key": key},
                )
            )

        # 3. Cookie changes (names and counts only, values always redacted)
        b_cookies = set(b.get("cookie_names", []))
        h_cookies = set(h.get("cookie_names", []))

        for cookie in sorted(b_cookies - h_cookies):
            divergences.append(
                BehaviorDivergence(
                    category="storage",
                    severity=SeverityLevel.MEDIUM,
                    route=route,
                    event_type="COOKIE_REMOVED",
                    title=f"Cookie '{cookie}' no longer set on {route}",
                    description=(
                        f"Cookie '{cookie}' was present in Base but absent in Head."
                    ),
                    base_value={"cookie_name": cookie, "value": "[REDACTED]"},
                    head_value=None,
                )
            )

        for cookie in sorted(h_cookies - b_cookies):
            divergences.append(
                BehaviorDivergence(
                    category="storage",
                    severity=SeverityLevel.LOW,
                    route=route,
                    event_type="COOKIE_ADDED",
                    title=f"New cookie '{cookie}' set on {route}",
                    description=f"Cookie '{cookie}' was introduced in Head.",
                    base_value=None,
                    head_value={"cookie_name": cookie, "value": "[REDACTED]"},
                )
            )

    return divergences
