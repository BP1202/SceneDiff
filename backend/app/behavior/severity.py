"""Task: Behavior Severity Engine.

Evaluates detected runtime differences against deterministic severity criteria:

CRITICAL:
- HTTP 5xx errors introduced in Head that did not exist in Base.
- Missing required page / route completely disappeared.
- Missing critical interactive components (e.g. form count drops to 0).

HIGH:
- Buttons removed.
- Forms removed.
- New unhandled JavaScript exceptions or console errors.
- HTTP 4xx errors introduced.

MEDIUM:
- Performance metric regressions exceeding configured threshold (e.g. LCP, TTFB, load).
- New console warnings.
- Removal/mutation of authentication/session keys in LocalStorage/SessionStorage.

LOW:
- Cosmetic DOM additions or removals (links, images, minor elements).
- Metadata or text-only changes.

INFO:
- Non-breaking additions (e.g. new routes visited, performance improvements).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
import enum
from typing import Any


class SeverityLevel(enum.StrEnum):
    """Deterministic severity ranking."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class ComparisonVerdict(enum.StrEnum):
    """High-level behavior regression verdict."""

    REGRESSION = "REGRESSION"
    WARNING = "WARNING"
    CLEAN = "CLEAN"


_SEVERITY_ORDER: dict[SeverityLevel, int] = {
    SeverityLevel.CRITICAL: 50,
    SeverityLevel.HIGH: 40,
    SeverityLevel.MEDIUM: 30,
    SeverityLevel.LOW: 20,
    SeverityLevel.INFO: 10,
}


@dataclass(frozen=True)
class BehaviorDivergence:
    """A single normalized behavior divergence event between Base and Head."""

    category: str  # "dom" | "network" | "console" | "storage" | "performance"
    severity: SeverityLevel
    route: str
    event_type: str
    title: str
    description: str
    base_value: dict[str, Any] | None = None
    head_value: dict[str, Any] | None = None
    evidence: dict[str, Any] | None = None
    divergence_order: int = 0
    is_root_cause_candidate: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-safe dictionary."""
        return {
            "category": self.category,
            "severity": self.severity.value,
            "route": self.route,
            "event_type": self.event_type,
            "title": self.title,
            "description": self.description,
            "base_value": self.base_value,
            "head_value": self.head_value,
            "evidence": self.evidence,
            "divergence_order": self.divergence_order,
            "is_root_cause_candidate": self.is_root_cause_candidate,
        }


def get_highest_severity(
    severities: Iterable[str | SeverityLevel],
) -> SeverityLevel:
    """Return the highest severity among an iterable of severities."""
    highest = SeverityLevel.INFO
    highest_weight = _SEVERITY_ORDER[highest]

    for item in severities:
        level = item if isinstance(item, SeverityLevel) else SeverityLevel(item.upper())
        weight = _SEVERITY_ORDER.get(level, 0)
        if weight > highest_weight:
            highest = level
            highest_weight = weight

    return highest


def determine_verdict(
    divergences: Iterable[BehaviorDivergence],
) -> ComparisonVerdict:
    """Determine the overall comparison verdict based on observed divergences.

    - Any CRITICAL or HIGH severity -> REGRESSION
    - Any MEDIUM severity -> WARNING
    - Otherwise -> CLEAN
    """
    has_warning = False
    for div in divergences:
        if div.severity in (SeverityLevel.CRITICAL, SeverityLevel.HIGH):
            return ComparisonVerdict.REGRESSION
        if div.severity == SeverityLevel.MEDIUM:
            has_warning = True

    return ComparisonVerdict.WARNING if has_warning else ComparisonVerdict.CLEAN
