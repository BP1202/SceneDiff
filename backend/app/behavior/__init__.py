"""Behavior Comparator Engine package (Sprint 4).

Compares runtime trace evidence from Base and Head executions to produce
a deterministic BehaviorDiffReport detailing the first meaningful runtime
divergence and categorized regression findings for IBM Bob.
"""

from app.behavior.comparator import (
    BehaviorDiffReport,
    ComparisonSummary,
    compare_runtime_artifacts,
)
from app.behavior.severity import (
    BehaviorDivergence,
    ComparisonVerdict,
    SeverityLevel,
    determine_verdict,
    get_highest_severity,
)
from app.behavior.timeline import build_divergence_timeline

__all__ = [
    "BehaviorDiffReport",
    "BehaviorDivergence",
    "ComparisonSummary",
    "ComparisonVerdict",
    "SeverityLevel",
    "build_divergence_timeline",
    "compare_runtime_artifacts",
    "determine_verdict",
    "get_highest_severity",
]
