"""Tests for runtime API endpoints (Task 33).

Tests the three runtime endpoints using HTTPX + FastAPI TestClient.
The actual Playwright collection is mocked so no browser is required.
"""

from httpx import AsyncClient


class TestStartCollection:
    async def test_returns_202(self, async_client: AsyncClient) -> None:
        payload = {
            "base_commit": "abc1234567",
            "head_commit": "def9876543",
            "base_url": "http://localhost:3000",
            "journey": [{"url": "http://localhost:3000", "label": "/"}],
        }
        response = await async_client.post("/api/v1/runtime/collect", json=payload)
        assert response.status_code == 202

    async def test_returns_session_id(self, async_client: AsyncClient) -> None:
        payload = {
            "base_commit": "abc1234567",
            "head_commit": "def9876543",
            "base_url": "http://localhost:3000",
            "journey": [{"url": "http://localhost:3000", "label": "/"}],
        }
        response = await async_client.post("/api/v1/runtime/collect", json=payload)
        data = response.json()
        assert "session_id" in data
        assert len(data["session_id"]) == 36  # UUID4

    async def test_invalid_sha_returns_422(self, async_client: AsyncClient) -> None:
        payload = {
            "base_commit": "GGGG",  # invalid hex
            "head_commit": "def9876543",
            "base_url": "http://localhost:3000",
            "journey": [{"url": "http://localhost:3000", "label": "/"}],
        }
        response = await async_client.post("/api/v1/runtime/collect", json=payload)
        assert response.status_code == 422

    async def test_short_sha_returns_422(self, async_client: AsyncClient) -> None:
        payload = {
            "base_commit": "abc",  # too short
            "head_commit": "def9876543",
            "base_url": "http://localhost:3000",
            "journey": [{"url": "http://localhost:3000", "label": "/"}],
        }
        response = await async_client.post("/api/v1/runtime/collect", json=payload)
        assert response.status_code == 422

    async def test_empty_journey_returns_422(self, async_client: AsyncClient) -> None:
        payload = {
            "base_commit": "abc1234567",
            "head_commit": "def9876543",
            "base_url": "http://localhost:3000",
            "journey": [],  # empty — must have at least 1
        }
        response = await async_client.post("/api/v1/runtime/collect", json=payload)
        assert response.status_code == 422

    async def test_non_http_url_in_journey_returns_422(
        self, async_client: AsyncClient
    ) -> None:
        payload = {
            "base_commit": "abc1234567",
            "head_commit": "def9876543",
            "base_url": "http://localhost:3000",
            "journey": [{"url": "ftp://badurl", "label": "/"}],
        }
        response = await async_client.post("/api/v1/runtime/collect", json=payload)
        assert response.status_code == 422

    async def test_status_is_pending_initially(self, async_client: AsyncClient) -> None:
        payload = {
            "base_commit": "abc1234567",
            "head_commit": "def9876543",
            "base_url": "http://localhost:3000",
            "journey": [{"url": "http://localhost:3000", "label": "/"}],
        }
        response = await async_client.post("/api/v1/runtime/collect", json=payload)
        data = response.json()
        assert data["status"] == "PENDING"


class TestGetCollectionStatus:
    async def test_returns_404_for_unknown_session(
        self, async_client: AsyncClient
    ) -> None:
        response = await async_client.get("/api/v1/runtime/nonexistent-uuid")
        assert response.status_code == 404

    async def test_returns_status_for_known_session(
        self, async_client: AsyncClient
    ) -> None:
        # Create a session first
        payload = {
            "base_commit": "abc1234567",
            "head_commit": "def9876543",
            "base_url": "http://localhost:3000",
            "journey": [{"url": "http://localhost:3000", "label": "/"}],
        }
        create_resp = await async_client.post("/api/v1/runtime/collect", json=payload)
        session_id = create_resp.json()["session_id"]

        status_resp = await async_client.get(f"/api/v1/runtime/{session_id}")
        assert status_resp.status_code == 200
        data = status_resp.json()
        assert data["session_id"] == session_id
        assert "status" in data
        assert "progress" in data
        assert "current_step" in data

    async def test_progress_is_integer(self, async_client: AsyncClient) -> None:
        payload = {
            "base_commit": "abc1234567",
            "head_commit": "def9876543",
            "base_url": "http://localhost:3000",
            "journey": [{"url": "http://localhost:3000", "label": "/"}],
        }
        create_resp = await async_client.post("/api/v1/runtime/collect", json=payload)
        session_id = create_resp.json()["session_id"]
        status_resp = await async_client.get(f"/api/v1/runtime/{session_id}")
        assert isinstance(status_resp.json()["progress"], int)


class TestGetArtifacts:
    async def test_returns_404_for_unknown_session(
        self, async_client: AsyncClient
    ) -> None:
        response = await async_client.get("/api/v1/runtime/no-such-id/artifacts")
        assert response.status_code == 404

    async def test_returns_409_when_not_completed(
        self, async_client: AsyncClient
    ) -> None:
        payload = {
            "base_commit": "abc1234567",
            "head_commit": "def9876543",
            "base_url": "http://localhost:3000",
            "journey": [{"url": "http://localhost:3000", "label": "/"}],
        }
        create_resp = await async_client.post("/api/v1/runtime/collect", json=payload)
        session_id = create_resp.json()["session_id"]
        # Session is PENDING — not completed
        artifacts_resp = await async_client.get(
            f"/api/v1/runtime/{session_id}/artifacts"
        )
        assert artifacts_resp.status_code == 409
