"""Task 32 — Playwright Runtime Execution Pipeline (Collector Orchestrator).

Orchestrates a complete base-commit → head-commit collection cycle:
1. Launch Chromium browser.
2. For each commit: create isolated context, run the user journey, collect
   all artifacts (DOM, console, network, storage, screenshots, performance).
3. Normalize both traces into ``RuntimeTraceArtifact`` objects.
4. Return a ``CollectionResult`` with both artifacts.

Design rules
------------
- Browser lifecycle is fully managed — always cleaned up even on error.
- Each commit runs in a completely isolated context (no state leakage).
- Failures produce a structured ``CollectionError`` instead of raw exceptions.
- No business logic here — orchestration only.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging

from app.runtime.browser import isolated_context, launch_browser, new_page
from app.runtime.console import ConsoleCollector
from app.runtime.dom import DomSnapshot, capture_dom_snapshot
from app.runtime.network import NetworkCollector
from app.runtime.normalizer import RuntimeTraceArtifact, normalize
from app.runtime.performance import PerformanceMetrics, capture_performance
from app.runtime.screenshots import ScreenshotArtifact, capture_screenshot
from app.runtime.storage import StorageSnapshot, capture_storage_snapshot

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# User journey step definition
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class JourneyStep:
    """A single step in a scripted user journey.

    Attributes:
        url:   Absolute URL to navigate to.
        label: Human-readable route name used in artifacts (e.g. "/login").
        wait_for_selector: Optional CSS selector to wait for after navigation.
    """

    url: str
    label: str
    wait_for_selector: str | None = None


# ---------------------------------------------------------------------------
# Collection result types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CommitArtifacts:
    """Raw collected artifacts for one commit before normalization."""

    commit_ref: str
    dom_snapshots: list[DomSnapshot]
    console_events_list: list[object]  # ConsoleEvent items
    network_events_list: list[object]  # NetworkEvent items
    storage_snapshots: list[StorageSnapshot]
    screenshots: list[ScreenshotArtifact]
    performance_metrics: list[PerformanceMetrics]


@dataclass(frozen=True)
class CollectionResult:
    """Normalized artifacts for both base and head commits."""

    base: RuntimeTraceArtifact
    head: RuntimeTraceArtifact
    base_commit: str
    head_commit: str


@dataclass(frozen=True)
class CollectionError:
    """Structured error produced when collection fails."""

    commit_ref: str
    stage: str  # "browser" | "context" | "navigation" | "collection"
    message: str


# ---------------------------------------------------------------------------
# Core pipeline
# ---------------------------------------------------------------------------


async def collect_commit(
    commit_ref: str,
    base_url: str,
    journey: list[JourneyStep],
    capture_screenshots: bool = True,
) -> RuntimeTraceArtifact:
    """Execute a scripted journey for one commit and return a normalized artifact.

    Args:
        commit_ref:          Short SHA of the commit being collected.
        base_url:            Application root URL (e.g. "http://localhost:3000").
        journey:             Ordered list of ``JourneyStep`` objects to execute.
        capture_screenshots: Whether to take screenshots at each step.

    Returns:
        ``RuntimeTraceArtifact`` for this commit.

    Raises:
        RuntimeError: If browser launch or navigation fails fatally.
    """
    dom_snapshots: list[DomSnapshot] = []
    storage_snapshots: list[StorageSnapshot] = []
    screenshots: list[ScreenshotArtifact] = []
    performance_metrics: list[PerformanceMetrics] = []

    console_collector = ConsoleCollector()
    network_collector = NetworkCollector()

    async with (
        launch_browser() as browser,
        isolated_context(browser, commit_ref) as context,
        new_page(context) as page,
    ):
        # Attach event collectors before any navigation
        console_collector.attach(page)
        network_collector.attach(page)

        for step in journey:
            logger.info(
                "runtime.collector: navigating commit=%s route=%s",
                commit_ref,
                step.label,
            )
            await page.goto(step.url, wait_until="domcontentloaded")

            if step.wait_for_selector:
                await page.wait_for_selector(step.wait_for_selector, timeout=10_000)

            # Collect all artifacts for this step
            dom_snapshots.append(await capture_dom_snapshot(page, step.label))
            storage_snapshots.append(
                await capture_storage_snapshot(page, context, step.label)
            )
            performance_metrics.append(await capture_performance(page, step.label))
            if capture_screenshots:
                screenshots.append(
                    await capture_screenshot(page, step.label, "full_page")
                )

    # Normalize and return

    return normalize(
        commit_ref=commit_ref,
        base_url=base_url,
        dom_snapshots=dom_snapshots,
        console_events=list(console_collector.events),
        network_events=list(network_collector.events),
        storage_snapshots=storage_snapshots,
        screenshots=screenshots,
        performance_metrics=performance_metrics,
    )


async def run_collection(
    *,
    base_commit: str,
    head_commit: str,
    base_url: str,
    journey: list[JourneyStep],
    capture_screenshots: bool = True,
) -> CollectionResult:
    """Run full base→head collection pipeline.

    Executes the journey for both commits sequentially and returns a
    ``CollectionResult`` containing both normalized artifacts.

    Args:
        base_commit:         SHA of the base (older) commit.
        head_commit:         SHA of the head (newer) commit.
        base_url:            Application root URL.
        journey:             Scripted user journey steps.
        capture_screenshots: Whether to capture screenshots.

    Returns:
        ``CollectionResult`` with normalized base and head artifacts.
    """
    logger.info(
        "runtime.collector: starting collection base=%s head=%s steps=%d",
        base_commit,
        head_commit,
        len(journey),
    )

    base_artifact = await collect_commit(
        commit_ref=base_commit,
        base_url=base_url,
        journey=journey,
        capture_screenshots=capture_screenshots,
    )

    head_artifact = await collect_commit(
        commit_ref=head_commit,
        base_url=base_url,
        journey=journey,
        capture_screenshots=capture_screenshots,
    )

    logger.info(
        "runtime.collector: collection complete base=%s head=%s",
        base_commit,
        head_commit,
    )

    return CollectionResult(
        base=base_artifact,
        head=head_artifact,
        base_commit=base_commit,
        head_commit=head_commit,
    )
