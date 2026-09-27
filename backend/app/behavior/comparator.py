"""Task: Behavior Comparator Engine (Core Orchestrator).

Coordinates comparisons across all runtime dimensions:
- DOM structure
- Network traffic
- Console events
- Storage states
- Performance metrics

Produces a unified, deterministic BehaviorDiffReport consumed by IBM Bob.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import logging
from typing import Any

from app.behavior.console_diff import compare_console_events
from app.behavior.dom_diff import compare_dom_snapshots
from app.behavior.network_diff import compare_network_events
from app.behavior.performance_diff import compare_performance_metrics
from app.behavior.severity import (
    BehaviorDivergence,
    ComparisonVerdict,
    SeverityLevel,
    determine_verdict,
    get_highest_severity,
)
from app.behavior.storage_diff import compare_storage_snapshots
from app.behavior.timeline import build_divergence_timeline

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ComparisonSummary:
    """Aggregated numerical summary of behavior divergences."""

    total_divergences: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    info_count: int
    dom_count: int
    network_count: int
    console_count: int
    storage_count: int
    performance_count: int

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


@dataclass(frozen=True)
class BehaviorDiffReport:
    """The complete Behavior Diff Report consumed by IBM Bob's repair engine."""

    repository_name: str
    base_commit: str
    head_commit: str
    verdict: ComparisonVerdict
    highest_severity: SeverityLevel
    summary: ComparisonSummary
    first_meaningful_divergence: BehaviorDivergence | None
    divergence_timeline: list[BehaviorDivergence]

    def to_dict(self) -> dict[str, Any]:
        return {
            "repository_name": self.repository_name,
            "base_commit": self.base_commit,
            "head_commit": self.head_commit,
            "verdict": self.verdict.value,
            "highest_severity": self.highest_severity.value,
            "summary": self.summary.to_dict(),
            "first_meaningful_divergence": (
                self.first_meaningful_divergence.to_dict()
                if self.first_meaningful_divergence
                else None
            ),
            "divergence_timeline": [d.to_dict() for d in self.divergence_timeline],
        }


def compare_runtime_artifacts(
    base_artifact: dict[str, Any],
    head_artifact: dict[str, Any],
    repository_name: str = "SceneDiff",
) -> BehaviorDiffReport:
    """Execute complete behavior comparison between Base and Head runtime artifacts.

    Args:
        base_artifact: Dict output of Base commit RuntimeTraceArtifact.to_dict().
        head_artifact: Dict output of Head commit RuntimeTraceArtifact.to_dict().
        repository_name: Repository name for context.

    Returns:
        Immutable ``BehaviorDiffReport``.
    """
    base_commit = str(base_artifact.get("commit_ref", "base"))
    head_commit = str(head_artifact.get("commit_ref", "head"))

    # Extract component artifacts
    base_dom = list(base_artifact.get("dom_snapshots", []))
    head_dom = list(head_artifact.get("dom_snapshots", []))

    base_net = list(base_artifact.get("network_events", []))
    head_net = list(head_artifact.get("network_events", []))

    base_con = list(base_artifact.get("console_events", []))
    head_con = list(head_artifact.get("console_events", []))

    base_sto = list(base_artifact.get("storage_snapshots", []))
    head_sto = list(head_artifact.get("storage_snapshots", []))

    base_prf = list(base_artifact.get("performance_metrics", []))
    head_prf = list(head_artifact.get("performance_metrics", []))

    journey_routes = list(base_artifact.get("routes_visited", []))

    # Run individual comparators
    raw_divergences: list[BehaviorDivergence] = []
    raw_divergences.extend(compare_dom_snapshots(base_dom, head_dom))
    raw_divergences.extend(compare_network_events(base_net, head_net))
    raw_divergences.extend(compare_console_events(base_con, head_con))
    raw_divergences.extend(compare_storage_snapshots(base_sto, head_sto))
    raw_divergences.extend(compare_performance_metrics(base_prf, head_prf))

    # Order into timeline & identify first divergence
    ordered_timeline, first_div = build_divergence_timeline(
        raw_divergences, journey_routes=journey_routes
    )

    # Compute summaries
    severities = [d.severity for d in ordered_timeline]
    highest_sev = get_highest_severity(severities) if severities else SeverityLevel.INFO
    verdict = determine_verdict(ordered_timeline)

    summary = ComparisonSummary(
        total_divergences=len(ordered_timeline),
        critical_count=sum(
            1 for d in ordered_timeline if d.severity == SeverityLevel.CRITICAL
        ),
        high_count=sum(1 for d in ordered_timeline if d.severity == SeverityLevel.HIGH),
        medium_count=sum(
            1 for d in ordered_timeline if d.severity == SeverityLevel.MEDIUM
        ),
        low_count=sum(1 for d in ordered_timeline if d.severity == SeverityLevel.LOW),
        info_count=sum(1 for d in ordered_timeline if d.severity == SeverityLevel.INFO),
        dom_count=sum(1 for d in ordered_timeline if d.category == "dom"),
        network_count=sum(1 for d in ordered_timeline if d.category == "network"),
        console_count=sum(1 for d in ordered_timeline if d.category == "console"),
        storage_count=sum(1 for d in ordered_timeline if d.category == "storage"),
        performance_count=sum(
            1 for d in ordered_timeline if d.category == "performance"
        ),
    )

    report = BehaviorDiffReport(
        repository_name=repository_name,
        base_commit=base_commit,
        head_commit=head_commit,
        verdict=verdict,
        highest_severity=highest_sev,
        summary=summary,
        first_meaningful_divergence=first_div,
        divergence_timeline=ordered_timeline,
    )

    logger.info(
        "behavior.comparator: complete base=%s head=%s verdict=%s divergences=%d",
        base_commit,
        head_commit,
        verdict.value,
        len(ordered_timeline),
    )

    return report
