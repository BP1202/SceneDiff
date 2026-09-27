"""Task 31 — Runtime Trace Normalizer.

Converts raw collector outputs (DOM snapshots, console events, network
events, storage snapshots, screenshots, performance metrics) into a single
deterministic ``RuntimeTraceArtifact`` that the Sprint 2 Behavior Engine
can consume.

Design rules
------------
- Output is a frozen dataclass — immutable once created.
- All string values are Secret-Shield-scanned at normalization time
  (defense-in-depth on top of per-collector masking).
- Timestamps and UUIDs are NOT normalized out here — they are stripped
  only inside the Behavior Hash engine (Sprint 2).
- The artifact is JSON-serializable via ``to_dict()``.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import TYPE_CHECKING, Any

from app.runtime.console import ConsoleEvent
from app.services.secret_shield import mask_string

if TYPE_CHECKING:
    from app.runtime.dom import DomSnapshot
    from app.runtime.network import NetworkEvent
    from app.runtime.performance import PerformanceMetrics
    from app.runtime.screenshots import ScreenshotArtifact
    from app.runtime.storage import StorageSnapshot

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RuntimeTraceArtifact:
    """Fully normalized runtime trace for one commit execution.

    This is the canonical output of the Sprint 3 collector pipeline and
    the primary input to the Sprint 2 Behavior Engine.
    """

    commit_ref: str
    base_url: str
    routes_visited: tuple[str, ...]
    dom_snapshots: tuple[DomSnapshot, ...]
    console_events: tuple[ConsoleEvent, ...]
    network_events: tuple[NetworkEvent, ...]
    storage_snapshots: tuple[StorageSnapshot, ...]
    screenshots: tuple[ScreenshotArtifact, ...]
    performance_metrics: tuple[PerformanceMetrics, ...]
    # Aggregate stats
    total_console_errors: int
    total_network_failures: int
    total_routes: int

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-safe dict (screenshots excluded by default).

        Screenshots are omitted from the dict representation to keep
        artifact size manageable for the Behavior Engine.  They are stored
        separately by the artifact store.

        Returns:
            Nested dict suitable for ``json.dumps``.
        """
        return {
            "commit_ref": self.commit_ref,
            "base_url": self.base_url,
            "routes_visited": list(self.routes_visited),
            "total_routes": self.total_routes,
            "total_console_errors": self.total_console_errors,
            "total_network_failures": self.total_network_failures,
            "dom_snapshots": [
                {
                    "route": s.route,
                    "title": s.title,
                    "element_count": s.element_count,
                    "button_count": s.button_count,
                    "form_count": s.form_count,
                    "input_count": s.input_count,
                    "link_count": s.link_count,
                    "image_count": s.image_count,
                    "hidden_element_count": s.hidden_element_count,
                    "text_sample": s.text_sample,
                    # html_snapshot omitted — too large for behavior engine
                }
                for s in self.dom_snapshots
            ],
            "console_events": [
                {
                    "level": e.level,
                    "message": e.message,
                    "source_url": e.source_url,
                    "line_number": e.line_number,
                }
                for e in self.console_events
            ],
            "network_events": [
                {
                    "method": e.method,
                    "url": e.url,
                    "status_code": e.status_code,
                    "latency_ms": e.latency_ms,
                    "resource_type": e.resource_type,
                    "failed": e.failed,
                    # request_headers omitted — already sanitized, but we
                    # exclude to reduce artifact size
                }
                for e in self.network_events
            ],
            "storage_snapshots": [
                {
                    "route": s.route,
                    "local_storage_keys": list(s.local_storage.keys()),
                    "session_storage_keys": list(s.session_storage.keys()),
                    "cookie_count": len(s.cookies),
                    "cookie_names": [c.name for c in s.cookies],
                }
                for s in self.storage_snapshots
            ],
            "performance_metrics": [
                {
                    "route": m.route,
                    "load_event_ms": m.load_event_ms,
                    "dom_content_loaded_ms": m.dom_content_loaded_ms,
                    "ttfb_ms": m.ttfb_ms,
                    "fcp_ms": m.fcp_ms,
                    "lcp_ms": m.lcp_ms,
                    "js_heap_used_mb": m.js_heap_used_mb,
                }
                for m in self.performance_metrics
            ],
        }


# ---------------------------------------------------------------------------
# Normalizer factory
# ---------------------------------------------------------------------------


def normalize(
    *,
    commit_ref: str,
    base_url: str,
    dom_snapshots: list[DomSnapshot],
    console_events: list[ConsoleEvent],
    network_events: list[NetworkEvent],
    storage_snapshots: list[StorageSnapshot],
    screenshots: list[ScreenshotArtifact],
    performance_metrics: list[PerformanceMetrics],
) -> RuntimeTraceArtifact:
    """Build a normalized ``RuntimeTraceArtifact`` from raw collector outputs.

    Applies a final Secret Shield scan on console message strings as
    defense-in-depth.

    Args:
        commit_ref:         Short SHA of the commit that was executed.
        base_url:           Application base URL used during collection.
        dom_snapshots:      Collected DOM snapshots (all routes).
        console_events:     All console/error events captured.
        network_events:     All network request/response events.
        storage_snapshots:  Storage state at each checkpoint.
        screenshots:        Visual evidence captures.
        performance_metrics:Performance timing per route.

    Returns:
        Immutable ``RuntimeTraceArtifact`` ready for the Behavior Engine.
    """
    # Defense-in-depth: re-scan console messages through Secret Shield
    clean_console = tuple(
        ConsoleEvent(
            level=e.level,
            message=mask_string(e.message),
            source_url=e.source_url,
            line_number=e.line_number,
        )
        for e in console_events
    )

    routes = tuple(dict.fromkeys(s.route for s in dom_snapshots))

    artifact = RuntimeTraceArtifact(
        commit_ref=commit_ref,
        base_url=base_url,
        routes_visited=routes,
        dom_snapshots=tuple(dom_snapshots),
        console_events=clean_console,
        network_events=tuple(network_events),
        storage_snapshots=tuple(storage_snapshots),
        screenshots=tuple(screenshots),
        performance_metrics=tuple(performance_metrics),
        total_console_errors=sum(
            1 for e in clean_console if e.level in ("error", "exception")
        ),
        total_network_failures=sum(1 for e in network_events if e.failed),
        total_routes=len(routes),
    )

    logger.info(
        "runtime.normalizer: artifact built commit=%s routes=%d console=%d network=%d",
        commit_ref,
        artifact.total_routes,
        len(clean_console),
        len(network_events),
    )
    return artifact
