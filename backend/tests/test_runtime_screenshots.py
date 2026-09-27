"""Tests for runtime/screenshots.py — Screenshot Collector (Task 29)."""

from __future__ import annotations

import base64
from dataclasses import FrozenInstanceError
from unittest.mock import AsyncMock

import pytest

from app.runtime.screenshots import capture_screenshot


class TestCaptureScreenshot:
    @pytest.mark.asyncio()
    async def test_full_page_screenshot(self) -> None:
        sample_bytes = b"fake-png-data-stream"
        page = AsyncMock()
        page.screenshot = AsyncMock(return_value=sample_bytes)
        page.viewport_size = {"width": 1280, "height": 720}

        artifact = await capture_screenshot(page, "/home", "full_page")

        page.screenshot.assert_awaited_once_with(full_page=True, type="png")
        assert artifact.route == "/home"
        assert artifact.screenshot_type == "full_page"
        assert artifact.format == "png"
        assert artifact.width == 1280
        assert artifact.height == 720
        assert artifact.data_base64 == base64.b64encode(sample_bytes).decode("ascii")
        assert artifact.truncated is False

    @pytest.mark.asyncio()
    async def test_viewport_screenshot(self) -> None:
        sample_bytes = b"viewport-png-bytes"
        page = AsyncMock()
        page.screenshot = AsyncMock(return_value=sample_bytes)
        page.viewport_size = {"width": 1920, "height": 1080}

        artifact = await capture_screenshot(page, "/dashboard", "viewport")

        page.screenshot.assert_awaited_once_with(full_page=False, type="png")
        assert artifact.width == 1920
        assert artifact.height == 1080
        assert artifact.screenshot_type == "viewport"

    @pytest.mark.asyncio()
    async def test_truncation_when_exceeding_max_bytes(self) -> None:
        oversized_bytes = b"A" * (2 * 1024 * 1024 + 100)
        page = AsyncMock()
        page.screenshot = AsyncMock(return_value=oversized_bytes)
        page.viewport_size = None

        artifact = await capture_screenshot(page, "/large", "full_page")

        assert artifact.truncated is True
        decoded = base64.b64decode(artifact.data_base64)
        assert len(decoded) == 2 * 1024 * 1024
        assert artifact.width == 1280
        assert artifact.height == 720

    @pytest.mark.asyncio()
    async def test_artifact_is_frozen(self) -> None:
        page = AsyncMock()
        page.screenshot = AsyncMock(return_value=b"data")
        page.viewport_size = None

        artifact = await capture_screenshot(page, "/", "viewport")
        with pytest.raises(FrozenInstanceError):
            artifact.route = "mutated"  # type: ignore[misc]
