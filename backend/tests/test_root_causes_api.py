"""API tests for /api/v1/root-causes endpoints (Sprint 5 - Task 43).

Uses HTTPX AsyncClient with mocked database and services.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
import uuid

from httpx import AsyncClient

from app.models.root_cause_evidence import RootCauseEvidence
from app.models.root_cause_report import (
    AnalysisStatus,
    ConfidenceLevel,
    RootCauseReport,
)


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _make_report(**kwargs: object) -> RootCauseReport:
    now = _utcnow()
    return RootCauseReport(
        id=kwargs.get("id", uuid.uuid4()),
        comparison_id=kwargs.get("comparison_id", uuid.uuid4()),
        repository_name=str(kwargs.get("repository_name", "SceneDiff")),
        base_commit=str(kwargs.get("base_commit", "abc1234")),
        head_commit=str(kwargs.get("head_commit", "def5678")),
        status=kwargs.get("status", AnalysisStatus.COMPLETED),
        summary=str(kwargs.get("summary", "Root cause identified.")),
        confidence_score=int(kwargs.get("confidence_score", 92)),
        confidence_band=kwargs.get("confidence_band", ConfidenceLevel.VERY_HIGH),
        primary_candidate=kwargs.get(
            "primary_candidate",
            {
                "reason": "HTTP 500 on /login",
                "evidence_type": "STATUS_CODE_5XX_INTRODUCED",
                "severity": "CRITICAL",
                "score": 95.0,
            },
        ),
        secondary_candidates=kwargs.get("secondary_candidates", []),
        repair_plan=kwargs.get("repair_plan", []),
        explanation=kwargs.get("explanation", {}),
        bob_prompt=str(kwargs.get("bob_prompt", "# Bob Prompt")),
        created_at=kwargs.get("created_at", now),
        updated_at=kwargs.get("updated_at", now),
    )


class TestCreateRootCauseAnalysis:
    async def test_create_returns_201_on_success(
        self,
        async_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        rep = _make_report()
        payload = {
            "comparison_id": str(rep.comparison_id),
            "git_diff_files": ["src/login.py"],
        }

        with patch(
            "app.services.root_cause_service.create_root_cause_analysis",
            new=AsyncMock(return_value=rep),
        ):
            resp = await async_client.post("/api/v1/root-causes", json=payload)

        assert resp.status_code == 201
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["id"] == str(rep.id)
        assert body["data"]["confidence_score"] == 92

    async def test_create_returns_404_when_comparison_missing(
        self,
        async_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        payload = {"comparison_id": str(uuid.uuid4())}

        with patch(
            "app.services.root_cause_service.create_root_cause_analysis",
            side_effect=ValueError("BehaviorComparison not found."),
        ):
            resp = await async_client.post("/api/v1/root-causes", json=payload)

        assert resp.status_code == 404
        assert resp.json()["success"] is False


class TestGetRootCauseAnalysis:
    async def test_get_by_id_returns_200(
        self,
        async_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        rep = _make_report()

        with patch(
            "app.services.root_cause_service.get_root_cause_report_by_id",
            new=AsyncMock(return_value=rep),
        ):
            resp = await async_client.get(f"/api/v1/root-causes/{rep.id}")

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["id"] == str(rep.id)

    async def test_get_by_id_returns_404_when_not_found(
        self,
        async_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        with patch(
            "app.services.root_cause_service.get_root_cause_report_by_id",
            new=AsyncMock(return_value=None),
        ):
            resp = await async_client.get(f"/api/v1/root-causes/{uuid.uuid4()}")

        assert resp.status_code == 404


class TestGetRootCauseReport:
    async def test_get_report_returns_prompt_and_repair_plan(
        self,
        async_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        rep = _make_report(bob_prompt="# Bob Prompt Content")

        with patch(
            "app.services.root_cause_service.get_root_cause_report_by_id",
            new=AsyncMock(return_value=rep),
        ):
            resp = await async_client.get(f"/api/v1/root-causes/{rep.id}/report")

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["bob_prompt"] == "# Bob Prompt Content"
        assert body["data"]["confidence_score"] == 92


class TestGetRootCauseEvidence:
    async def test_get_evidence_returns_ordered_items(
        self,
        async_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        rep = _make_report()
        ev = RootCauseEvidence(
            id=uuid.uuid4(),
            report_id=rep.id,
            category="network",
            severity="CRITICAL",
            route="/api/login",
            event_type="STATUS_CODE_5XX_INTRODUCED",
            title="500 on login",
            description="",
            divergence_order=1,
            is_root_cause_candidate=True,
            evidence_metadata={},
            created_at=_utcnow(),
        )

        with (
            patch(
                "app.services.root_cause_service.get_root_cause_report_by_id",
                new=AsyncMock(return_value=rep),
            ),
            patch(
                "app.services.root_cause_service.get_root_cause_evidence",
                new=AsyncMock(return_value=[ev]),
            ),
        ):
            resp = await async_client.get(f"/api/v1/root-causes/{rep.id}/evidence")

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert len(body["data"]) == 1
        assert body["data"][0]["event_type"] == "STATUS_CODE_5XX_INTRODUCED"


class TestListRootCauses:
    async def test_list_returns_paginated_reports(
        self,
        async_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        rep = _make_report()

        with patch(
            "app.services.root_cause_service.list_root_cause_reports",
            new=AsyncMock(return_value=([rep], 1)),
        ):
            resp = await async_client.get("/api/v1/root-causes?limit=10&offset=0")

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert len(body["data"]) == 1
        assert body["metadata"]["pagination"]["total"] == 1
