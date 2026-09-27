"""Evidence Correlation Engine (Sprint 5 - Task 35).

Merges behavioral divergence reports with Git diff file modifications, groups
evidence by route, sorts by causal timeline, and normalizes evidence items.
"""

from __future__ import annotations

from typing import Any

from app.root_cause.evidence import (
    CorrelatedEvidenceItem,
    EvidenceCategory,
    EvidenceSeverity,
    RouteEvidenceGroup,
)
from app.services.secret_shield import mask_string


def _map_category(raw_cat: str) -> EvidenceCategory:
    """Map string category to EvidenceCategory enum safely."""
    raw_lower = raw_cat.strip().lower()
    for cat in EvidenceCategory:
        if cat.value == raw_lower:
            return cat
    return EvidenceCategory.DOM


def _map_severity(raw_sev: str) -> EvidenceSeverity:
    """Map string severity to EvidenceSeverity enum safely."""
    raw_upper = raw_sev.strip().upper()
    for sev in EvidenceSeverity:
        if sev.value == raw_upper:
            return sev
    return EvidenceSeverity.INFO


def _guess_file_correlation(
    route: str,
    event_type: str,
    git_modified_files: list[str] | None,
) -> tuple[str | None, str | None]:
    """Correlate a divergence route and event type with modified Git files."""
    if not git_modified_files:
        return None, None

    route_clean = route.strip("/").lower()
    tokens = [t for t in route_clean.split("/") if t]

    for file_path in git_modified_files:
        path_lower = file_path.lower()
        if any(token in path_lower for token in tokens):
            return file_path, None

    # Fallback to first modified file if only one file was changed
    if len(git_modified_files) == 1:
        return git_modified_files[0], None

    return None, None


def correlate_evidence(
    divergences: list[dict[str, Any]],
    git_diff_files: list[str] | None = None,
) -> tuple[list[CorrelatedEvidenceItem], list[RouteEvidenceGroup]]:
    """Correlate runtime divergences with Git diff metadata.

    Args:
        divergences: Serialized BehaviorDivergence list from BehaviorDiffReport.
        git_diff_files: Optional list of modified file paths from Git diff.

    Returns:
        tuple (correlated_items, route_groups)
    """
    items: list[CorrelatedEvidenceItem] = []
    route_map: dict[str, RouteEvidenceGroup] = {}

    for d in divergences:
        cat = _map_category(str(d.get("category", "dom")))
        sev = _map_severity(str(d.get("severity", "INFO")))
        route = mask_string(str(d.get("route", "global")))
        ev_type = str(d.get("event_type", "UNKNOWN"))
        title = mask_string(str(d.get("title", "")))
        desc = mask_string(str(d.get("description", "")))
        order = int(d.get("divergence_order", 0))
        is_root = bool(d.get("is_root_cause_candidate", False))

        evidence_dict = d.get("evidence")
        clean_evidence = (
            {k: mask_string(str(v)) for k, v in evidence_dict.items()}
            if isinstance(evidence_dict, dict)
            else {}
        )

        matched_file, matched_func = _guess_file_correlation(
            route=route,
            event_type=ev_type,
            git_modified_files=git_diff_files,
        )

        item = CorrelatedEvidenceItem(
            category=cat,
            severity=sev,
            route=route,
            event_type=ev_type,
            title=title,
            description=desc,
            divergence_order=order,
            is_root_cause_candidate=is_root,
            file_path=matched_file,
            function_name=matched_func,
            evidence_metadata=clean_evidence,
        )
        items.append(item)

        if route not in route_map:
            route_map[route] = RouteEvidenceGroup(route=route)
        route_map[route].events.append(item)

    # Sort items by divergence_order
    sorted_items = sorted(items, key=lambda x: x.divergence_order)
    groups = sorted(route_map.values(), key=lambda g: g.route)

    return sorted_items, groups
