"""API tests for /api/v1/repairs endpoints (Sprint 6 - Task 57).

Uses HTTPX AsyncClient with mocked database and services.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch
import uuid

if TYPE_CHECKING:
    from httpx import AsyncClient

import pytest

from app.models.repair_patch import RepairPatch
from app.models.repair_report import RepairReport, RepairStatus
from app.repair.risk import RiskLevel


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _make_report(
    report_id: uuid.UUID | None = None,
    rc_id: uuid.UUID | None = None,
    comp_id: uuid.UUID | None = None,
) -> RepairReport:
    now = _utcnow()
    rid = report_id or uuid.uuid4()
    rep = RepairReport(
        id=rid,
        root_cause_id=rc_id or uuid.uuid4(),
        comparison_id=comp_id or uuid.uuid4(),
        repository_name="SceneDiff",
        status=RepairStatus.COMPLETED,
        summary="Fix validate_token null handling",
        risk_level=RiskLevel.HIGH,
        risk_score=75,
        repair_confidence=88,
        plan={
            "summary": "Fix validate_token null handling",
            "actions": [{"step": 1, "description": "Add guard"}],
        },
        rollback_plan={
            "strategy": "Revert",
            "commands": ["git apply -R repair.patch"],
        },
        markdown_report="# IBM Bob Repair Report\nAll good.",
        pr_summary="## IBM Bob Repair Summary\nFix details.",
        created_at=now,
        updated_at=now,
    )
    diff_str = (
        "diff --git a/app/auth/login.py b/app/auth/login.py\n+if payload is None: raise"
    )
    patch_item = RepairPatch(
        id=uuid.uuid4(),
        report_id=rid,
        target_file="app/auth/login.py",
        diff_content=diff_str,
        lines_added=1,
        lines_removed=0,
        is_validated=True,
        risk_level=RiskLevel.HIGH,
        validation_notes=[{"type": "note", "message": "Syntax valid"}],
        created_at=now,
    )
    rep.patches = [patch_item]
    return rep


@pytest.mark.asyncio
class TestCreateRepair:
    async def test_create_repair_success(
        self,
        async_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        rep = _make_report()
        payload = {
            "root_cause_id": str(rep.root_cause_id),
            "provider": "TemplatePatchProvider",
        }

        with patch(
            "app.services.repair_service.create_repair_report", new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = rep
            resp = await async_client.post("/api/v1/repairs", json=payload)

        assert resp.status_code == 201
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["id"] == str(rep.id)
        assert data["data"]["risk_level"] == "HIGH"
        assert data["data"]["repair_confidence"] == 88

    async def test_create_repair_not_found(
        self,
        async_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        payload = {"root_cause_id": str(uuid.uuid4())}

        with patch(
            "app.services.repair_service.create_repair_report", new_callable=AsyncMock
        ) as mock_create:
            mock_create.side_effect = ValueError("RootCauseReport not found")
            resp = await async_client.post("/api/v1/repairs", json=payload)

        assert resp.status_code == 404
        assert resp.json()["success"] is False
        assert "not found" in resp.json()["error"]["message"].lower()

    async def test_create_repair_missing_body(
        self,
        async_client: AsyncClient,
    ) -> None:
        resp = await async_client.post("/api/v1/repairs", json={})
        assert resp.status_code == 422


@pytest.mark.asyncio
class TestGetRepair:
    async def test_get_repair_summary_success(
        self,
        async_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        rep = _make_report()

        with patch(
            "app.services.repair_service.get_repair_report_by_id",
            new_callable=AsyncMock,
        ) as mock_get:
            mock_get.return_value = rep
            resp = await async_client.get(f"/api/v1/repairs/{rep.id}")

        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["id"] == str(rep.id)
        assert data["data"]["risk_level"] == "HIGH"

    async def test_get_repair_summary_not_found(
        self,
        async_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        with patch(
            "app.services.repair_service.get_repair_report_by_id",
            new_callable=AsyncMock,
        ) as mock_get:
            mock_get.return_value = None
            resp = await async_client.get(f"/api/v1/repairs/{uuid.uuid4()}")

        assert resp.status_code == 404


@pytest.mark.asyncio
class TestGetRepairReport:
    async def test_get_full_report_success(
        self,
        async_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        rep = _make_report()

        with patch(
            "app.services.repair_service.get_repair_report_by_id",
            new_callable=AsyncMock,
        ) as mock_get:
            mock_get.return_value = rep
            resp = await async_client.get(f"/api/v1/repairs/{rep.id}/report")

        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "markdown_report" in data["data"]
        assert "pr_summary" in data["data"]
        assert len(data["data"]["patches"]) == 1

    async def test_get_full_report_not_found(
        self,
        async_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        with patch(
            "app.services.repair_service.get_repair_report_by_id",
            new_callable=AsyncMock,
        ) as mock_get:
            mock_get.return_value = None
            resp = await async_client.get(f"/api/v1/repairs/{uuid.uuid4()}/report")

        assert resp.status_code == 404


@pytest.mark.asyncio
class TestGetRepairPatch:
    async def test_get_patch_json_success(
        self,
        async_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        rep = _make_report()

        with patch(
            "app.services.repair_service.get_repair_report_by_id",
            new_callable=AsyncMock,
        ) as mock_get:
            mock_get.return_value = rep
            resp = await async_client.get(f"/api/v1/repairs/{rep.id}/patch")

        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["target_file"] == "app/auth/login.py"
        assert "diff --git" in data["data"]["raw_git_patch"]

    async def test_get_patch_raw_success(
        self,
        async_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        rep = _make_report()

        with patch(
            "app.services.repair_service.get_repair_report_by_id",
            new_callable=AsyncMock,
        ) as mock_get:
            mock_get.return_value = rep
            resp = await async_client.get(f"/api/v1/repairs/{rep.id}/patch?format=raw")

        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/x-diff")
        assert (
            f'filename="repair_{rep.id}.patch"' in resp.headers["content-disposition"]
        )
        assert "diff --git" in resp.text

    async def test_get_patch_not_found(
        self,
        async_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        with patch(
            "app.services.repair_service.get_repair_report_by_id",
            new_callable=AsyncMock,
        ) as mock_get:
            mock_get.return_value = None
            resp = await async_client.get(f"/api/v1/repairs/{uuid.uuid4()}/patch")

        assert resp.status_code == 404


@pytest.mark.asyncio
class TestListRepairs:
    async def test_list_repairs_success(
        self,
        async_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        rep = _make_report()

        with patch(
            "app.services.repair_service.list_repair_reports", new_callable=AsyncMock
        ) as mock_list:
            mock_list.return_value = ([rep], 1)
            resp = await async_client.get("/api/v1/repairs?page=1&page_size=10")

        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["metadata"]["pagination"]["total"] == 1
