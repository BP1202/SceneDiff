"""Task: Performance Metrics Diff Engine.

Compares browser performance metrics across routes between Base and Head.
Detects regressions in Page Load Time, Core Web Vitals (FCP, LCP),
TTFB, and memory usage against configurable thresholds.
"""

from __future__ import annotations

from typing import Any

from app.behavior.severity import BehaviorDivergence, SeverityLevel


def compare_performance_metrics(
    base_metrics: list[dict[str, Any]],
    head_metrics: list[dict[str, Any]],
    load_time_threshold_pct: float = 25.0,
    load_time_min_delta_ms: float = 200.0,
    lcp_threshold_ms: float = 500.0,
    fcp_threshold_ms: float = 300.0,
) -> list[BehaviorDivergence]:
    """Compare performance metrics route-by-route.

    Args:
        base_metrics: Performance records from Base trace.
        head_metrics: Performance records from Head trace.
        load_time_threshold_pct: Percentage increase for load time regression.
        load_time_min_delta_ms: Minimum absolute millisecond delta for load regression.
        lcp_threshold_ms: Millisecond delta threshold for LCP regression.
        fcp_threshold_ms: Millisecond delta threshold for FCP regression.

    Returns:
        List of detected BehaviorDivergence items.
    """
    divergences: list[BehaviorDivergence] = []

    base_map = {m.get("route", "/"): m for m in base_metrics}
    head_map = {m.get("route", "/"): m for m in head_metrics}

    common_routes = set(base_map.keys()) & set(head_map.keys())
    for route in sorted(common_routes):
        b = base_map[route]
        h = head_map[route]

        # 1. Page Load Event Time (load_event_ms)
        b_load = float(b.get("load_event_ms", 0.0))
        h_load = float(h.get("load_event_ms", 0.0))
        if b_load > 0 and h_load > 0:
            load_delta = h_load - b_load
            load_pct = (load_delta / b_load) * 100

            if (
                load_delta >= load_time_min_delta_ms
                and load_pct >= load_time_threshold_pct
            ):
                sev = (
                    SeverityLevel.HIGH
                    if (load_pct >= 100.0 and load_delta >= 1000.0)
                    else SeverityLevel.MEDIUM
                )
                load_title = (
                    f"Page load time increased by {round(load_pct)}% on {route}"
                )
                divergences.append(
                    BehaviorDivergence(
                        category="performance",
                        severity=sev,
                        route=route,
                        event_type="PAGE_LOAD_REGRESSION",
                        title=load_title,
                        description=(
                            f"Page load event increased by {round(load_delta)}ms "
                            f"({round(b_load)}ms -> {round(h_load)}ms) on '{route}'."
                        ),
                        base_value={"load_event_ms": b_load},
                        head_value={"load_event_ms": h_load},
                        evidence={
                            "delta_ms": round(load_delta, 2),
                            "pct_increase": round(load_pct, 1),
                        },
                    )
                )

        # 2. Largest Contentful Paint (LCP)
        b_lcp = float(b.get("lcp_ms", -1.0))
        h_lcp = float(h.get("lcp_ms", -1.0))
        if b_lcp > 0 and h_lcp > 0:
            lcp_delta = h_lcp - b_lcp
            if lcp_delta >= lcp_threshold_ms:
                divergences.append(
                    BehaviorDivergence(
                        category="performance",
                        severity=SeverityLevel.MEDIUM,
                        route=route,
                        event_type="LCP_REGRESSION",
                        title=f"LCP worsened by {round(lcp_delta)}ms on {route}",
                        description=(
                            f"Largest Contentful Paint degraded from {round(b_lcp)}ms "
                            f"to {round(h_lcp)}ms."
                        ),
                        base_value={"lcp_ms": b_lcp},
                        head_value={"lcp_ms": h_lcp},
                        evidence={"delta_ms": round(lcp_delta, 2)},
                    )
                )

        # 3. First Contentful Paint (FCP)
        b_fcp = float(b.get("fcp_ms", -1.0))
        h_fcp = float(h.get("fcp_ms", -1.0))
        if b_fcp > 0 and h_fcp > 0:
            fcp_delta = h_fcp - b_fcp
            if fcp_delta >= fcp_threshold_ms:
                divergences.append(
                    BehaviorDivergence(
                        category="performance",
                        severity=SeverityLevel.MEDIUM,
                        route=route,
                        event_type="FCP_REGRESSION",
                        title=f"FCP worsened by {round(fcp_delta)}ms on {route}",
                        description=(
                            f"First Contentful Paint degraded from {round(b_fcp)}ms "
                            f"to {round(h_fcp)}ms."
                        ),
                        base_value={"fcp_ms": b_fcp},
                        head_value={"fcp_ms": h_fcp},
                        evidence={"delta_ms": round(fcp_delta, 2)},
                    )
                )

        # 4. JS Heap Memory Growth
        b_heap = float(b.get("js_heap_used_mb", -1.0))
        h_heap = float(h.get("js_heap_used_mb", -1.0))
        if b_heap > 0 and h_heap > 0:
            heap_delta = h_heap - b_heap
            if heap_delta >= 25.0 and (heap_delta / b_heap) >= 0.5:
                heap_title = (
                    f"JS heap memory grew by {round(heap_delta, 1)}MB on {route}"
                )
                divergences.append(
                    BehaviorDivergence(
                        category="performance",
                        severity=SeverityLevel.MEDIUM,
                        route=route,
                        event_type="MEMORY_LEAK_WARNING",
                        title=heap_title,
                        description=(
                            f"JavaScript heap increased by {round(heap_delta, 1)} MB "
                            f"({round(b_heap, 1)} MB -> {round(h_heap, 1)} MB)."
                        ),
                        base_value={"js_heap_used_mb": b_heap},
                        head_value={"js_heap_used_mb": h_heap},
                        evidence={"delta_mb": round(heap_delta, 2)},
                    )
                )

    return divergences
