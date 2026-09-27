"""Tests for runtime/network.py — Network Request Collector (Task 27)."""

from __future__ import annotations

from unittest.mock import MagicMock

from app.runtime.network import (
    NetworkCollector,
    _sanitize_headers,
    _strip_fragment,
)


def _make_request(
    method: str = "GET",
    url: str = "http://localhost/api",
    resource_type: str = "fetch",
    headers: dict[str, str] | None = None,
) -> MagicMock:
    req = MagicMock()
    req.method = method
    req.url = url
    req.resource_type = resource_type
    req.headers = headers or {}
    return req


def _make_response(
    status: int = 200,
    url: str = "http://localhost/api",
    request: MagicMock | None = None,
    content_length: str = "512",
) -> MagicMock:
    resp = MagicMock()
    resp.status = status
    resp.url = url
    resp.request = request or _make_request(url=url)
    resp.headers = {"content-length": content_length}
    return resp


class TestNetworkCollector:
    def test_initial_events_empty(self) -> None:
        c = NetworkCollector()
        assert c.events == ()

    def test_attach_registers_listeners(self) -> None:
        c = NetworkCollector()
        page = MagicMock()
        c.attach(page)
        assert page.on.call_count == 3

    def test_response_captured(self) -> None:
        c = NetworkCollector()
        req = _make_request(method="GET", url="http://app/api/users")
        c._on_request(req)
        resp = _make_response(status=200, url="http://app/api/users", request=req)
        c._on_response(resp)
        assert len(c.events) == 1
        ev = c.events[0]
        assert ev.method == "GET"
        assert ev.status_code == 200
        assert not ev.failed

    def test_failed_request_captured(self) -> None:
        c = NetworkCollector()
        req = _make_request(url="http://app/broken")
        c._on_request(req)
        c._on_request_failed(req)
        assert len(c.events) == 1
        assert c.events[0].failed is True
        assert c.events[0].status_code == -1

    def test_failed_count(self) -> None:
        c = NetworkCollector()
        req = _make_request()
        c._on_request(req)
        c._on_request_failed(req)
        assert c.failed_count == 1

    def test_error_count_counts_4xx_5xx(self) -> None:
        c = NetworkCollector()
        req = _make_request(url="http://app/api")
        c._on_request(req)
        resp = _make_response(status=500, url="http://app/api", request=req)
        c._on_response(resp)
        assert c.error_count == 1

    def test_events_tuple_is_immutable(self) -> None:
        c = NetworkCollector()
        assert isinstance(c.events, tuple)

    def test_response_size_parsed(self) -> None:
        c = NetworkCollector()
        req = _make_request(url="http://app/api")
        c._on_request(req)
        resp = _make_response(
            status=200, url="http://app/api", request=req, content_length="1024"
        )
        c._on_response(resp)
        assert c.events[0].response_size == 1024

    def test_response_size_minus_one_when_missing(self) -> None:
        c = NetworkCollector()
        req = _make_request(url="http://app/api")
        c._on_request(req)
        resp = _make_response(
            status=200, url="http://app/api", request=req, content_length=""
        )
        c._on_response(resp)
        assert c.events[0].response_size == -1


class TestSanitizeHeaders:
    def test_authorization_redacted(self) -> None:
        h = _sanitize_headers(
            {"authorization": "Bearer tok123", "content-type": "application/json"}
        )
        assert h["authorization"] == "[REDACTED]"
        assert h["content-type"] == "application/json"

    def test_cookie_redacted(self) -> None:
        h = _sanitize_headers({"cookie": "session=abc123"})
        assert h["cookie"] == "[REDACTED]"

    def test_set_cookie_redacted(self) -> None:
        h = _sanitize_headers({"set-cookie": "id=xyz; HttpOnly"})
        assert h["set-cookie"] == "[REDACTED]"

    def test_x_api_key_redacted(self) -> None:
        h = _sanitize_headers({"x-api-key": "secret-key-value"})
        assert h["x-api-key"] == "[REDACTED]"

    def test_safe_headers_preserved(self) -> None:
        h = _sanitize_headers({"content-type": "application/json", "accept": "*/*"})
        assert h["content-type"] == "application/json"
        assert h["accept"] == "*/*"


class TestStripFragment:
    def test_fragment_stripped(self) -> None:
        assert _strip_fragment("http://app/page#section") == "http://app/page"

    def test_no_fragment_unchanged(self) -> None:
        assert _strip_fragment("http://app/page") == "http://app/page"

    def test_query_preserved(self) -> None:
        assert _strip_fragment("http://app/api?q=1#top") == "http://app/api?q=1"
