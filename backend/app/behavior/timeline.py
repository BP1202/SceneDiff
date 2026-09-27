"""Task: Runtime Divergence Timeline Engine.

Sorts and correlates divergences across all collectors to pinpoint the
FIRST MEANINGFUL RUNTIME DIVERGENCE and construct the regression timeline.

Causation priority (within the same route/step):
1. Network errors (e.g. 500, network drop)
2. Console runtime exceptions (e.g. uncaught TypeError)
3. DOM failures (e.g. button missing, form broken)
4. Storage state anomalies
5. Performance degradation
"""

from __future__ import annotations

from app.behavior.severity import BehaviorDivergence, SeverityLevel

_CATEGORY_CAUSATION_WEIGHT: dict[str, int] = {
    "network": 10,
    "console": 20,
    "dom": 30,
    "storage": 40,
    "performance": 50,
}


def build_divergence_timeline(
    divergences: list[BehaviorDivergence],
    journey_routes: list[str] | None = None,
) -> tuple[list[BehaviorDivergence], BehaviorDivergence | None]:
    """Sort divergences into a causal execution timeline.

    Also identifies the first meaningful divergence (root cause candidate).

    Args:
        divergences: Unsorted list of BehaviorDivergence items from all collectors.
        journey_routes: Optional ordered list of routes as visited in the journey.

    Returns:
        tuple (ordered_divergences, first_divergence)
    """
    if not divergences:
        return [], None

    route_indices = {r: i for i, r in enumerate(journey_routes or [])}

    def _sort_key(d: BehaviorDivergence) -> tuple[int, int, int]:
        # 1. Route order (0-indexed position in journey; unknown routes placed at end)
        r_order = route_indices.get(d.route, 9999)
        # 2. Causation order: network -> console -> dom -> storage -> performance
        c_order = _CATEGORY_CAUSATION_WEIGHT.get(d.category, 100)
        # 3. Severity order: CRITICAL (0), HIGH (1), MEDIUM (2), LOW (3), INFO (4)
        s_order = {
            SeverityLevel.CRITICAL: 0,
            SeverityLevel.HIGH: 1,
            SeverityLevel.MEDIUM: 2,
            SeverityLevel.LOW: 3,
            SeverityLevel.INFO: 4,
        }.get(d.severity, 10)
        return (r_order, c_order, s_order)

    sorted_raw = sorted(divergences, key=_sort_key)

    # Find first meaningful regression (prioritizing CRITICAL, HIGH, MEDIUM)
    first_meaningful_idx = -1
    for target_sev in (
        SeverityLevel.CRITICAL,
        SeverityLevel.HIGH,
        SeverityLevel.MEDIUM,
    ):
        for idx, d in enumerate(sorted_raw):
            if d.severity == target_sev:
                first_meaningful_idx = idx
                break
        if first_meaningful_idx != -1:
            break

    ordered_divergences: list[BehaviorDivergence] = []
    first_divergence: BehaviorDivergence | None = None

    for idx, d in enumerate(sorted_raw, start=1):
        is_first = (idx - 1) == first_meaningful_idx
        updated = BehaviorDivergence(
            category=d.category,
            severity=d.severity,
            route=d.route,
            event_type=d.event_type,
            title=d.title,
            description=d.description,
            base_value=d.base_value,
            head_value=d.head_value,
            evidence=d.evidence,
            divergence_order=idx,
            is_root_cause_candidate=is_first,
        )
        ordered_divergences.append(updated)
        if is_first:
            first_divergence = updated

    # Fallback to the first item if no CRITICAL/HIGH regression was found
    if first_divergence is None and ordered_divergences:
        first_divergence = ordered_divergences[0]

    return ordered_divergences, first_divergence
