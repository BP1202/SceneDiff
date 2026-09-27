"""Tests for runtime/storage.py — Storage Collector (Task 28)."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from unittest.mock import AsyncMock

import pytest

from app.runtime.storage import StorageSnapshot, capture_storage_snapshot


def _make_page(
    local_storage: dict[str, str] | None = None,
    session_storage: dict[str, str] | None = None,
) -> AsyncMock:
    page = AsyncMock()
    ls = local_storage or {}
    ss = session_storage or {}
    # evaluate is called twice: once for localStorage, once for sessionStorage
    page.evaluate = AsyncMock(side_effect=[ls, ss])
    return page


def _make_context(cookies: list[dict] | None = None) -> AsyncMock:
    ctx = AsyncMock()
    ctx.cookies = AsyncMock(return_value=cookies or [])
    return ctx


class TestCaptureStorageSnapshot:
    async def test_returns_storage_snapshot(self) -> None:
        page = _make_page()
        ctx = _make_context()
        result = await capture_storage_snapshot(page, ctx, "/home")
        assert isinstance(result, StorageSnapshot)

    async def test_route_is_set(self) -> None:
        page = _make_page()
        ctx = _make_context()
        result = await capture_storage_snapshot(page, ctx, "/profile")
        assert result.route == "/profile"

    async def test_local_storage_keys_preserved(self) -> None:
        page = _make_page(local_storage={"theme": "dark", "lang": "en"})
        ctx = _make_context()
        result = await capture_storage_snapshot(page, ctx, "/")
        assert "theme" in result.local_storage
        assert "lang" in result.local_storage

    async def test_local_storage_safe_value_preserved(self) -> None:
        page = _make_page(local_storage={"theme": "dark"})
        ctx = _make_context()
        result = await capture_storage_snapshot(page, ctx, "/")
        assert result.local_storage["theme"] == "dark"

    async def test_local_storage_secret_masked(self) -> None:
        jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjoiYWRtaW4ifQ.abc123"
        page = _make_page(
            local_storage={
                "token": jwt,
                "auth": f"Bearer {jwt}",
            }
        )
        ctx = _make_context()
        result = await capture_storage_snapshot(page, ctx, "/")
        assert result.local_storage["token"] == "[REDACTED]"
        assert "[REDACTED]" in result.local_storage["auth"]

    async def test_cookies_always_redacted(self) -> None:
        raw_cookies = [
            {
                "name": "session",
                "value": "super-secret-session-token",
                "domain": "localhost",
                "path": "/",
                "httpOnly": True,
                "secure": False,
                "sameSite": "Lax",
            }
        ]
        page = _make_page()
        ctx = _make_context(cookies=raw_cookies)
        result = await capture_storage_snapshot(page, ctx, "/")
        assert len(result.cookies) == 1
        assert result.cookies[0].value == "[REDACTED]"
        assert result.cookies[0].name == "session"

    async def test_cookie_flags_preserved(self) -> None:
        raw_cookies = [
            {
                "name": "auth",
                "value": "secret",
                "domain": "app.com",
                "path": "/",
                "httpOnly": True,
                "secure": True,
                "sameSite": "Strict",
            }
        ]
        page = _make_page()
        ctx = _make_context(cookies=raw_cookies)
        result = await capture_storage_snapshot(page, ctx, "/")
        c = result.cookies[0]
        assert c.http_only is True
        assert c.secure is True
        assert c.same_site == "Strict"

    async def test_empty_storage_returns_empty_dicts(self) -> None:
        page = _make_page()
        ctx = _make_context()
        result = await capture_storage_snapshot(page, ctx, "/")
        assert result.local_storage == {}
        assert result.session_storage == {}
        assert result.cookies == ()

    async def test_snapshot_is_frozen(self) -> None:
        page = _make_page()
        ctx = _make_context()
        result = await capture_storage_snapshot(page, ctx, "/")
        with pytest.raises(FrozenInstanceError):
            result.route = "mutated"  # type: ignore[misc]
