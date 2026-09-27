"""Task: Console Log & Error Diff Engine.

Compares JavaScript console events between Base and Head executions.
Detects newly introduced exceptions, error spikes, and console warnings.
Applies Secret Shield sanitization to all error messages.
"""

from __future__ import annotations

from typing import Any

from app.behavior.severity import BehaviorDivergence, SeverityLevel
from app.services.secret_shield import mask_string


def compare_console_events(
    base_events: list[dict[str, Any]],
    head_events: list[dict[str, Any]],
) -> list[BehaviorDivergence]:
    """Compare console logs and error events between Base and Head.

    Args:
        base_events: Serialized console events from Base trace.
        head_events: Serialized console events from Head trace.

    Returns:
        List of detected BehaviorDivergence items.
    """
    divergences: list[BehaviorDivergence] = []

    # Map Base events by (level, normalized_message)
    base_known: set[tuple[str, str]] = {
        (ev.get("level", "log").lower(), mask_string(ev.get("message", "").strip()))
        for ev in base_events
    }

    head_errors = [
        ev
        for ev in head_events
        if ev.get("level", "").lower() in ("error", "exception")
    ]
    base_errors = [
        ev
        for ev in base_events
        if ev.get("level", "").lower() in ("error", "exception")
    ]

    # 1. Total error count increase
    if len(head_errors) > len(base_errors):
        diff_count = len(head_errors) - len(base_errors)
        divergences.append(
            BehaviorDivergence(
                category="console",
                severity=SeverityLevel.HIGH,
                route="global",
                event_type="CONSOLE_ERROR_COUNT_INCREASED",
                title=f"{diff_count} new console error(s) detected",
                description=(
                    f"Console error count increased from {len(base_errors)} in Base "
                    f"to {len(head_errors)} in Head."
                ),
                base_value={"error_count": len(base_errors)},
                head_value={"error_count": len(head_errors)},
                evidence={"new_error_count": diff_count},
            )
        )

    # 2. Inspect each Head event for brand new errors/exceptions
    for ev in head_events:
        level = ev.get("level", "log").lower()
        raw_msg = ev.get("message", "").strip()
        safe_msg = mask_string(raw_msg)
        source = ev.get("source_url") or "unknown"
        line = ev.get("line_number")
        key = (level, safe_msg)

        if key not in base_known:
            if level in ("exception", "error"):
                is_exception = level == "exception" or "uncaught" in safe_msg.lower()
                sev = SeverityLevel.CRITICAL if is_exception else SeverityLevel.HIGH
                ev_type = "RUNTIME_EXCEPTION" if is_exception else "NEW_CONSOLE_ERROR"

                divergences.append(
                    BehaviorDivergence(
                        category="console",
                        severity=sev,
                        route=source,
                        event_type=ev_type,
                        title=f"JavaScript {level.capitalize()}: {safe_msg[:60]}",
                        description=(
                            f"Console {level} in Head at {source}:{line}: "
                            f"{safe_msg[:120]}"
                        ),
                        base_value=None,
                        head_value={
                            "level": level,
                            "message": safe_msg,
                            "source_url": source,
                            "line_number": line,
                        },
                        evidence={"source_url": source, "line_number": line},
                    )
                )

            elif level == "warning":
                divergences.append(
                    BehaviorDivergence(
                        category="console",
                        severity=SeverityLevel.MEDIUM,
                        route=source,
                        event_type="NEW_CONSOLE_WARNING",
                        title=f"Console Warning: {safe_msg[:60]}",
                        description=(
                            f"Console warning in Head at {source}:{line}: "
                            f"{safe_msg[:120]}"
                        ),
                        base_value=None,
                        head_value={
                            "level": level,
                            "message": safe_msg,
                            "source_url": source,
                            "line_number": line,
                        },
                    )
                )

    return divergences
