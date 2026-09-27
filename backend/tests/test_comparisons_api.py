"""API tests for /api/v1/comparisons endpoints (Sprint 4).

Uses HTTPX AsyncClient with mocked database and services.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
import uuid

from httpx import AsyncClient

from app.behavior.comparator import BehaviorDiffReport, ComparisonSummary
from app.behavior.severity import ComparisonVerdict, SeverityLevel
from app.models.behavior_comparison import (
    BehaviorComparison,
    ComparisonEvent,
    ComparisonStatus,
)


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _make_comparison(**kwargs: object) -> BehaviorComparison:
    now = _utcnow()
    return BehaviorComparison(
        id=kwargs.get("id", uuid.uuid4()),
        repository_name=str(kwargs.get("repository_name", "SceneDiff")),
        base_commit=str(kwargs.get("base_commit", "abc1234")),
        head_commit=str(kwargs.get("head_commit", "def5678")),
        status=kwargs.get("status", ComparisonStatus.COMPLETED),
        verdict=str(kwargs.get("verdict", "CLEAN")),
        highest_severity=str(kwargs.get("highest_severity", "INFO")),
        total_divergences=int(kwargs.get("total_divergences", 0)),
        summary=kwargs.get("summary", {}),
        first_divergence=kwargs.get("first_divergence"),
        created_at=kwargs.get("created_at", now),
        updated_at=kwargs.get("updated_at", now),
    )


class TestCreateComparison:
    async def test_create_comparison_returns_201(
        self,
        async_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        comp = _make_comparison(
            verdict="REGRESSION", highest_severity="CRITICAL", total_divergences=2
        )
        summary = ComparisonSummary(
            total_divergences=2,
            critical_count=1,
            high_count=1,
            medium_count=0,
            low_count=0,
            info_count=0,
            dom_count=0,
            network_count=1,
            console_count=1,
            storage_count=0,
            performance_count=0,
        )
        report = BehaviorDiffReport(
            repository_name="SceneDiff",
            base_commit="abc1234",
            head_commit="def5678",
            verdict=ComparisonVerdict.REGRESSION,
            highest_severity=SeverityLevel.CRITICAL,
            summary=summary,
            first_meaningful_divergence=None,
            divergence_timeline=[],
        )

        with patch(
            "app.services.comparison_service.create_comparison",
            AsyncMock(return_value=(comp, report)),
        ):
            payload = {
                "repository_name": "SceneDiff",
                "base_commit": "abc1234",
                "head_commit": "def5678",
                "base_artifact": {},
                "head_artifact": {},
            }
            response = await async_client.post("/api/v1/comparisons", json=payload)
            assert response.status_code == 201
            data = response.json()
            assert data["success"] is True
            assert data["data"]["verdict"] == "REGRESSION"
            assert data["metadata"]["total_divergences"] == 2

    async def test_invalid_sha_returns_422(
        self,
        async_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        payload = {
            "repository_name": "SceneDiff",
            "base_commit": "not-hex!",
            "head_commit": "def5678",
        }
        response = await async_client.post("/api/v1/comparisons", json=payload)
        assert response.status_code == 422


class TestGetComparison:
    async def test_get_comparison_found(
        self,
        async_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        comp_id = uuid.uuid4()
        comp = _make_comparison(id=comp_id, verdict="WARNING")

        with patch(
            "app.services.comparison_service.get_comparison_by_id",
            AsyncMock(return_value=comp),
        ):
            response = await async_client.get(f"/api/v1/comparisons/{comp_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["verdict"] == "WARNING"

    async def test_get_comparison_not_found(
        self,
        async_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        with patch(
            "app.services.comparison_service.get_comparison_by_id",
            AsyncMock(return_value=None),
        ):
            response = await async_client.get(f"/api/v1/comparisons/{uuid.uuid4()}")
            assert response.status_code == 404


class TestGetComparisonReport:
    async def test_get_report_returns_canonical_structure(
        self,
        async_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        comp_id = uuid.uuid4()
        comp = _make_comparison(
            id=comp_id,
            verdict="REGRESSION",
            highest_severity="HIGH",
            summary={"total_divergences": 1, "high_count": 1},
            first_divergence={
                "category": "dom",
                "severity": "HIGH",
                "route": "/login",
                "event_type": "BUTTON_REMOVED",
                "title": "Button removed",
                "description": "Submit button missing",
                "divergence_order": 1,
            },
        )
        event = ComparisonEvent(
            id=uuid.uuid4(),
            comparison_id=comp_id,
            category="dom",
            severity="HIGH",
            route="/login",
            event_type="BUTTON_REMOVED",
            title="Button removed",
            description="Submit button missing",
            divergence_order=1,
            created_at=_utcnow(),
        )

        with (
            patch(
                "app.services.comparison_service.get_comparison_by_id",
                AsyncMock(return_value=comp),
            ),
            patch(
                "app.services.comparison_service.get_comparison_events",
                AsyncMock(return_value=[event]),
            ),
        ):
            response = await async_client.get(f"/api/v1/comparisons/{comp_id}/report")
            assert response.status_code == 200
            data = response.json()["data"]
            assert data["verdict"] == "REGRESSION"
            assert data["first_meaningful_divergence"]["event_type"] == "BUTTON_REMOVED"
            assert len(data["divergence_timeline"]) == 1


class TestGetComparisonEvents:
    async def test_get_events_list(
        self,
        async_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        comp_id = uuid.uuid4()
        comp = _make_comparison(id=comp_id)
        event = ComparisonEvent(
            id=uuid.uuid4(),
            comparison_id=comp_id,
            category="network",
            severity="CRITICAL",
            route="/api",
            event_type="500",
            title="Internal error",
            description="500",
            divergence_order=1,
            created_at=_utcnow(),
        )

        with (
            patch(
                "app.services.comparison_service.get_comparison_by_id",
                AsyncMock(return_value=comp),
            ),
            patch(
                "app.services.comparison_service.get_comparison_events",
                AsyncMock(return_value=[event]),
            ),
        ):
            response = await async_client.get(
                f"/api/v1/comparisons/{comp_id}/events?category=network"
            )
            assert response.status_code == 200
            data = response.json()["data"]
            assert len(data) == 1
            assert data[0]["category"] == "network"
