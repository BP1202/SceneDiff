"""Tests for runtime/dom.py — DOM Snapshot Collector (Task 25).

All tests mock the Playwright Page interface so no browser is required.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from unittest.mock import AsyncMock

import pytest

from app.runtime.dom import DomSnapshot, capture_dom_snapshot


def _make_page(
    *,
    title: str = "Test Page",
    element_count: int = 100,
    button_count: int = 5,
    form_count: int = 2,
    input_count: int = 3,
    link_count: int = 10,
    image_count: int = 4,
    hidden_count: int = 8,
    body_text: str = "Hello world",
    html: str = "<html><body>Hello</body></html>",
) -> AsyncMock:
    """Build a mock Playwright Page with configurable evaluate returns."""
    page = AsyncMock()
    page.title = AsyncMock(return_value=title)
    page.content = AsyncMock(return_value=html)

    # evaluate() is called multiple times — return values in order
    page.evaluate = AsyncMock(
        side_effect=[
            element_count,
            button_count,
            form_count,
            input_count,
            link_count,
            image_count,
            hidden_count,
            body_text,
            html,  # content() equivalent — actually called via page.content()
        ]
    )
    # Override content() to return html directly
    page.content = AsyncMock(return_value=html)
    return page


class TestCaptureDomSnapshot:
    async def test_returns_dom_snapshot_instance(self) -> None:
        page = _make_page()
        result = await capture_dom_snapshot(page, "/test")
        assert isinstance(result, DomSnapshot)

    async def test_route_is_set(self) -> None:
        page = _make_page()
        result = await capture_dom_snapshot(page, "/dashboard")
        assert result.route == "/dashboard"

    async def test_title_captured(self) -> None:
        page = _make_page(title="Dashboard")
        result = await capture_dom_snapshot(page, "/dashboard")
        assert result.title == "Dashboard"

    async def test_element_count_captured(self) -> None:
        page = _make_page(element_count=248)
        result = await capture_dom_snapshot(page, "/")
        assert result.element_count == 248

    async def test_button_count_captured(self) -> None:
        page = _make_page(button_count=14)
        result = await capture_dom_snapshot(page, "/")
        assert result.button_count == 14

    async def test_form_count_captured(self) -> None:
        page = _make_page(form_count=3)
        result = await capture_dom_snapshot(page, "/")
        assert result.form_count == 3

    async def test_hidden_count_captured(self) -> None:
        page = _make_page(hidden_count=6)
        result = await capture_dom_snapshot(page, "/")
        assert result.hidden_element_count == 6

    async def test_html_snapshot_set(self) -> None:
        html = "<html><body>content</body></html>"
        page = _make_page(html=html)
        result = await capture_dom_snapshot(page, "/")
        assert result.html_snapshot == html

    async def test_snapshot_is_frozen(self) -> None:
        page = _make_page()
        result = await capture_dom_snapshot(page, "/")
        with pytest.raises(FrozenInstanceError):
            result.route = "mutated"  # type: ignore[misc]

    async def test_text_sample_captured(self) -> None:
        page = _make_page(body_text="Welcome to SceneDiff")
        result = await capture_dom_snapshot(page, "/")
        assert result.text_sample == "Welcome to SceneDiff"
