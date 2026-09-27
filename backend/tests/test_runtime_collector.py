"""Tests for runtime/collector.py — Playwright Execution Pipeline (Task 32)."""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.runtime.collector import (
    CollectionResult,
    JourneyStep,
    collect_commit,
    run_collection,
)
from app.runtime.dom import DomSnapshot
from app.runtime.normalizer import RuntimeTraceArtifact
from app.runtime.performance import PerformanceMetrics
from app.runtime.screenshots import ScreenshotArtifact
from app.runtime.storage import StorageSnapshot


def _mock_journey() -> list[JourneyStep]:
    return [
        JourneyStep(url="http://localhost:3000/", label="/"),
        JourneyStep(
            url="http://localhost:3000/dashboard",
            label="/dashboard",
            wait_for_selector="#main",
        ),
    ]


class TestJourneyStep:
    def test_instantiation(self) -> None:
        step = JourneyStep(
            url="http://localhost:3000/login",
            label="/login",
            wait_for_selector="#login-btn",
        )
        assert step.url == "http://localhost:3000/login"
        assert step.label == "/login"
        assert step.wait_for_selector == "#login-btn"

    def test_default_wait_selector_is_none(self) -> None:
        step = JourneyStep(url="http://localhost:3000/", label="/")
        assert step.wait_for_selector is None


class TestCollectPipeline:
    @pytest.mark.asyncio()
    async def test_collect_commit_orchestration(self) -> None:
        mock_page = AsyncMock()
        mock_page.on = MagicMock()
        mock_page.viewport_size = {"width": 1280, "height": 720}

        mock_context = AsyncMock()
        mock_context.set_default_timeout = MagicMock()
        mock_context.set_default_navigation_timeout = MagicMock()

        mock_browser = AsyncMock()

        @asynccontextmanager
        async def _mock_launch():
            yield mock_browser

        @asynccontextmanager
        async def _mock_isolated(browser, ref):
            yield mock_context

        @asynccontextmanager
        async def _mock_page_ctx(context):
            yield mock_page

        mock_dom = DomSnapshot(
            route="/",
            title="App",
            element_count=10,
            button_count=2,
            form_count=1,
            input_count=1,
            link_count=2,
            image_count=0,
            hidden_element_count=0,
            text_sample="Hello",
            html_snapshot="<html></html>",
        )
        mock_storage = StorageSnapshot(
            route="/",
            local_storage={},
            session_storage={},
            cookies=(),
        )
        mock_perf = PerformanceMetrics(
            route="/",
            dns_ms=0,
            tcp_connect_ms=0,
            ttfb_ms=0,
            dom_interactive_ms=0,
            dom_content_loaded_ms=0,
            load_event_ms=100,
            fcp_ms=50,
            lcp_ms=80,
            js_heap_used_mb=10,
        )
        mock_screenshot = ScreenshotArtifact(
            route="/",
            screenshot_type="full_page",
            format="png",
            width=1280,
            height=720,
            data_base64="abc",
            truncated=False,
        )

        with (
            patch("app.runtime.collector.launch_browser", side_effect=_mock_launch),
            patch("app.runtime.collector.isolated_context", side_effect=_mock_isolated),
            patch("app.runtime.collector.new_page", side_effect=_mock_page_ctx),
            patch(
                "app.runtime.collector.capture_dom_snapshot",
                AsyncMock(return_value=mock_dom),
            ),
            patch(
                "app.runtime.collector.capture_storage_snapshot",
                AsyncMock(return_value=mock_storage),
            ),
            patch(
                "app.runtime.collector.capture_performance",
                AsyncMock(return_value=mock_perf),
            ),
            patch(
                "app.runtime.collector.capture_screenshot",
                AsyncMock(return_value=mock_screenshot),
            ),
        ):
            artifact = await collect_commit(
                commit_ref="abc1234",
                base_url="http://localhost:3000",
                journey=_mock_journey(),
                capture_screenshots=True,
            )

            assert isinstance(artifact, RuntimeTraceArtifact)
            assert artifact.commit_ref == "abc1234"
            assert len(artifact.dom_snapshots) == 2
            assert len(artifact.storage_snapshots) == 2
            assert len(artifact.performance_metrics) == 2
            assert len(artifact.screenshots) == 2
            assert mock_page.goto.await_count == 2
            mock_page.wait_for_selector.assert_awaited_once_with(
                "#main", timeout=10_000
            )

    @pytest.mark.asyncio()
    async def test_run_collection_returns_both_commits(self) -> None:
        mock_artifact_base = AsyncMock(spec=RuntimeTraceArtifact)
        mock_artifact_head = AsyncMock(spec=RuntimeTraceArtifact)

        with patch(
            "app.runtime.collector.collect_commit",
            AsyncMock(side_effect=[mock_artifact_base, mock_artifact_head]),
        ) as mock_collect:
            result = await run_collection(
                base_commit="1111111",
                head_commit="2222222",
                base_url="http://localhost:3000",
                journey=_mock_journey(),
            )

            assert isinstance(result, CollectionResult)
            assert result.base_commit == "1111111"
            assert result.head_commit == "2222222"
            assert result.base is mock_artifact_base
            assert result.head is mock_artifact_head
            assert mock_collect.await_count == 2
