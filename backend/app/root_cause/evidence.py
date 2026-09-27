"""Evidence Data Structures (Sprint 5 - Task 35).

Defines strongly-typed representations for correlated runtime evidence,
linking behavioral divergences with Git diff metadata and route groupings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import enum
from typing import Any

from app.services.secret_shield import mask_string


class EvidenceCategory(enum.StrEnum):
    """Browser runtime evidence categories."""

    NETWORK = "network"
    CONSOLE = "console"
    DOM = "dom"
    STORAGE = "storage"
    PERFORMANCE = "performance"
    GIT = "git"


class EvidenceSeverity(enum.StrEnum):
    """Severity classification matching Sprint 4 behavior engine."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


@dataclass(frozen=True)
class CorrelatedEvidenceItem:
    """Single normalized evidence item correlated with source and route."""

    category: EvidenceCategory
    severity: EvidenceSeverity
    route: str
    event_type: str
    title: str
    description: str
    divergence_order: int = 0
    is_root_cause_candidate: bool = False
    file_path: str | None = None
    function_name: str | None = None
    evidence_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize evidence item into clean dictionary."""
        return {
            "category": self.category.value,
            "severity": self.severity.value,
            "route": mask_string(self.route),
            "event_type": self.event_type,
            "title": mask_string(self.title),
            "description": mask_string(self.description),
            "divergence_order": self.divergence_order,
            "is_root_cause_candidate": self.is_root_cause_candidate,
            "file_path": self.file_path,
            "function_name": self.function_name,
            "evidence_metadata": self.evidence_metadata,
        }


@dataclass
class RouteEvidenceGroup:
    """Group of correlated evidence items belonging to a specific route."""

    route: str
    events: list[CorrelatedEvidenceItem] = field(default_factory=list)

    @property
    def total_events(self) -> int:
        """Return total number of evidence events on this route."""
        return len(self.events)

    @property
    def highest_severity(self) -> EvidenceSeverity:
        """Determine highest severity across all events in this route."""
        severities = [ev.severity for ev in self.events]
        for target in (
            EvidenceSeverity.CRITICAL,
            EvidenceSeverity.HIGH,
            EvidenceSeverity.MEDIUM,
            EvidenceSeverity.LOW,
        ):
            if target in severities:
                return target
        return EvidenceSeverity.INFO

    def to_dict(self) -> dict[str, Any]:
        """Serialize route group to dictionary."""
        return {
            "route": mask_string(self.route),
            "total_events": self.total_events,
            "highest_severity": self.highest_severity.value,
            "events": [ev.to_dict() for ev in self.events],
        }
