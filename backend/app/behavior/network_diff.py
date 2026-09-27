"""Task: Network Traffic Diff Engine.

Detects HTTP status changes, latency spikes, request failures, and endpoint
regressions between Base and Head executions.
Enforces Secret Shield sanitization on all URLs and payloads.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from app.behavior.severity import BehaviorDivergence, SeverityLevel
from app.services.secret_shield import mask_string


def _normalize_url(raw_url: str) -> str:
    """Normalize URL by stripping host/port and query params for matching."""
    parsed = urlparse(raw_url)
    path = parsed.path or "/"
    return mask_string(path)


def compare_network_events(
    base_events: list[dict[str, Any]],
    head_events: list[dict[str, Any]],
    latency_threshold_pct: float = 50.0,
    latency_min_delta_ms: float = 250.0,
) -> list[BehaviorDivergence]:
    """Compare network request events between Base and Head.

    Args:
        base_events: Serialized network events from Base trace.
        head_events: Serialized network events from Head trace.
        latency_threshold_pct: Percentage increase to trigger latency regression.
        latency_min_delta_ms: Absolute minimum millisecond increase for regression.

    Returns:
        List of detected BehaviorDivergence items.
    """
    divergences: list[BehaviorDivergence] = []

    # Map by (method, normalized_path)
    base_by_endpoint: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for ev in base_events:
        key = (ev.get("method", "GET").upper(), _normalize_url(ev.get("url", "")))
        base_by_endpoint.setdefault(key, []).append(ev)

    head_by_endpoint: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for ev in head_events:
        key = (ev.get("method", "GET").upper(), _normalize_url(ev.get("url", "")))
        head_by_endpoint.setdefault(key, []).append(ev)

    # 1. Check every head event for new 5xx/4xx or hard failure
    for key, h_list in head_by_endpoint.items():
        method, endpoint = key
        b_list = base_by_endpoint.get(key, [])

        for idx, h_ev in enumerate(h_list):
            h_status = int(h_ev.get("status_code", 0))
            h_failed = bool(h_ev.get("failed", False))

            # Correlate with corresponding base call if present
            b_ev = b_list[idx] if idx < len(b_list) else (b_list[0] if b_list else None)
            b_status = int(b_ev.get("status_code", 0)) if b_ev else 0
            b_failed = bool(b_ev.get("failed", False)) if b_ev else False

            # Hard network failure
            if h_failed and not b_failed:
                divergences.append(
                    BehaviorDivergence(
                        category="network",
                        severity=SeverityLevel.CRITICAL,
                        route=endpoint,
                        event_type="NETWORK_REQUEST_FAILED",
                        title=f"{method} {endpoint} network call failed",
                        description=(
                            f"HTTP request to {method} {endpoint} failed in Head."
                        ),
                        base_value={"status_code": b_status, "failed": b_failed}
                        if b_ev
                        else None,
                        head_value={"status_code": h_status, "failed": True},
                        evidence={"url": mask_string(h_ev.get("url", ""))},
                    )
                )

            # 5xx HTTP server error introduced
            if 500 <= h_status < 600 and not (500 <= b_status < 600):
                divergences.append(
                    BehaviorDivergence(
                        category="network",
                        severity=SeverityLevel.CRITICAL,
                        route=endpoint,
                        event_type="STATUS_CODE_5XX_INTRODUCED",
                        title=f"{method} {endpoint} returned HTTP {h_status}",
                        description=(
                            f"Server returned HTTP {h_status} for {method} {endpoint}. "
                            f"Base response was HTTP {b_status}."
                        ),
                        base_value={"status_code": b_status} if b_ev else None,
                        head_value={"status_code": h_status},
                        evidence={"url": mask_string(h_ev.get("url", ""))},
                    )
                )

            # 4xx HTTP client error introduced
            elif 400 <= h_status < 500 and not (400 <= b_status < 500):
                divergences.append(
                    BehaviorDivergence(
                        category="network",
                        severity=SeverityLevel.HIGH,
                        route=endpoint,
                        event_type="STATUS_CODE_4XX_INTRODUCED",
                        title=f"{method} {endpoint} returned HTTP {h_status}",
                        description=(
                            f"HTTP {h_status} for {method} {endpoint}. "
                            f"Base response was HTTP {b_status}."
                        ),
                        base_value={"status_code": b_status} if b_ev else None,
                        head_value={"status_code": h_status},
                        evidence={"url": mask_string(h_ev.get("url", ""))},
                    )
                )

            # Latency spike comparison (when both succeeded)
            if b_ev and b_status == h_status and not h_failed:
                b_latency = float(b_ev.get("latency_ms", 0.0))
                h_latency = float(h_ev.get("latency_ms", 0.0))
                delta_ms = h_latency - b_latency
                pct_increase = (delta_ms / b_latency * 100) if b_latency > 0 else 0

                if (
                    delta_ms >= latency_min_delta_ms
                    and pct_increase >= latency_threshold_pct
                ):
                    reg_title = (
                        f"Latency regression on {method} {endpoint} "
                        f"(+{round(delta_ms)}ms)"
                    )
                    divergences.append(
                        BehaviorDivergence(
                            category="network",
                            severity=SeverityLevel.MEDIUM,
                            route=endpoint,
                            event_type="LATENCY_REGRESSION",
                            title=reg_title,
                            description=(
                                f"Response latency grew by {round(pct_increase, 1)}% "
                                f"({round(b_latency)}ms -> {round(h_latency)}ms)."
                            ),
                            base_value={"latency_ms": b_latency},
                            head_value={"latency_ms": h_latency},
                            evidence={"delta_ms": round(delta_ms, 2)},
                        )
                    )

    # 2. Missing endpoint calls (endpoints present in base but never called in head)
    for key, b_list in base_by_endpoint.items():
        if key not in head_by_endpoint:
            method, endpoint = key
            divergences.append(
                BehaviorDivergence(
                    category="network",
                    severity=SeverityLevel.HIGH,
                    route=endpoint,
                    event_type="ENDPOINT_CALL_MISSING",
                    title=f"Endpoint call missing: {method} {endpoint}",
                    description=(
                        f"Base execution performed {len(b_list)} request(s) to "
                        f"{method} {endpoint}, but Head never called this endpoint."
                    ),
                    base_value={"call_count": len(b_list)},
                    head_value={"call_count": 0},
                )
            )

    return divergences
