"""Unit tests for Repair Service (Sprint 6 - Task 57)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.repair_report import RepairReport, RepairStatus
from app.models.root_cause_report import RootCauseReport
from app.repair.risk import RiskLevel
from app.services import repair_service


def _build_mock_root_cause(
    rc_id: uuid.UUID | None = None,
    comp_id: uuid.UUID | None = None,
) -> RootCauseReport:
    report = RootCauseReport(
        id=rc_id or uuid.uuid4(),
        comparison_id=comp_id or uuid.uuid4(),
        repository_name="SceneDiff/demo",
        base_commit="commitA123",
        head_commit="commitB456",
        summary="validate_token returned None unexpectedly",
        confidence_score=90,
        primary_candidate={
            "file_path": "app/auth/login.py",
            "function_name": "validate_token",
            "reason": "validate_token returned None",
            "evidence_type": "null_return",
        },
        repair_plan=[],
    )
    return report


@pytest.mark.asyncio
async def test_create_repair_report_success() -> None:
    """Service successfully builds and saves RepairReport and RepairPatch."""
    rc_id = uuid.uuid4()
    mock_rc = _build_mock_root_cause(rc_id=rc_id)

    db = AsyncMock(spec=AsyncSession)
    db.add = MagicMock()
    mock_scalar = MagicMock()
    mock_scalar.scalar_one_or_none.return_value = mock_rc
    db.execute.return_value = mock_scalar

    report = await repair_service.create_repair_report(
        db=db,
        root_cause_id=rc_id,
        virtual_files={
            "app/auth/login.py": "def validate_token(token):\n    return token"
        },
    )

    assert report.root_cause_id == rc_id
    assert report.repository_name == "SceneDiff/demo"
    assert report.status == RepairStatus.COMPLETED
    assert report.repair_confidence >= 80
    assert len(report.patches) == 1
    assert report.patches[0].target_file == "app/auth/login.py"
    assert report.markdown_report.startswith("# IBM Bob")
    assert "## IBM Bob Repair Summary" in report.pr_summary
    db.add.assert_called_once()
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_repair_report_not_found() -> None:
    """Service raises ValueError if RootCauseReport does not exist."""
    db = AsyncMock(spec=AsyncSession)
    mock_scalar = MagicMock()
    mock_scalar.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_scalar

    with pytest.raises(ValueError, match="not found"):
        await repair_service.create_repair_report(db, root_cause_id=uuid.uuid4())


@pytest.mark.asyncio
async def test_create_repair_report_override_target_file() -> None:
    """Service respects override_target_file parameter."""
    rc_id = uuid.uuid4()
    mock_rc = _build_mock_root_cause(rc_id=rc_id)

    db = AsyncMock(spec=AsyncSession)
    db.add = MagicMock()
    mock_scalar = MagicMock()
    mock_scalar.scalar_one_or_none.return_value = mock_rc
    db.execute.return_value = mock_scalar

    report = await repair_service.create_repair_report(
        db=db,
        root_cause_id=rc_id,
        override_target_file="app/custom/target.py",
        virtual_files={"app/custom/target.py": "def target(): return None"},
    )

    assert report.patches[0].target_file == "app/custom/target.py"


@pytest.mark.asyncio
async def test_create_repair_report_with_mock_provider() -> None:
    """Service executes with MockPatchProvider."""
    rc_id = uuid.uuid4()
    mock_rc = _build_mock_root_cause(rc_id=rc_id)

    db = AsyncMock(spec=AsyncSession)
    db.add = MagicMock()
    mock_scalar = MagicMock()
    mock_scalar.scalar_one_or_none.return_value = mock_rc
    db.execute.return_value = mock_scalar

    report = await repair_service.create_repair_report(
        db=db,
        root_cause_id=rc_id,
        provider_name="MockPatchProvider",
    )

    assert "mock fix" in report.patches[0].diff_content


@pytest.mark.asyncio
async def test_get_repair_report_by_id_found() -> None:
    """Service returns report when found."""
    mock_report = RepairReport(
        id=uuid.uuid4(),
        root_cause_id=uuid.uuid4(),
        comparison_id=uuid.uuid4(),
        repository_name="SceneDiff/demo",
        status=RepairStatus.COMPLETED,
        summary="Fixed",
        risk_level=RiskLevel.LOW,
        risk_score=20,
        repair_confidence=90,
    )

    db = AsyncMock(spec=AsyncSession)
    mock_scalar = MagicMock()
    mock_scalar.scalar_one_or_none.return_value = mock_report
    db.execute.return_value = mock_scalar

    res = await repair_service.get_repair_report_by_id(db, mock_report.id)
    assert res is not None
    assert res.id == mock_report.id


@pytest.mark.asyncio
async def test_get_repair_report_by_id_not_found() -> None:
    """Service returns None when report is not found."""
    db = AsyncMock(spec=AsyncSession)
    mock_scalar = MagicMock()
    mock_scalar.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_scalar

    res = await repair_service.get_repair_report_by_id(db, uuid.uuid4())
    assert res is None


@pytest.mark.asyncio
async def test_list_repair_reports() -> None:
    """Service returns paginated list and total count."""
    db = AsyncMock(spec=AsyncSession)
    mock_count_scalar = MagicMock()
    mock_count_scalar.scalar_one.return_value = 1
    mock_records_scalar = MagicMock()
    mock_records_scalar.scalars.return_value.all.return_value = [
        RepairReport(
            id=uuid.uuid4(),
            root_cause_id=uuid.uuid4(),
            comparison_id=uuid.uuid4(),
            repository_name="SceneDiff/demo",
            status=RepairStatus.COMPLETED,
            summary="Fixed",
            risk_level=RiskLevel.LOW,
            risk_score=15,
            repair_confidence=95,
        )
    ]
    db.execute.side_effect = [mock_count_scalar, mock_records_scalar]

    records, total = await repair_service.list_repair_reports(
        db, page=1, page_size=10, repository_name="SceneDiff/demo"
    )
    assert total == 1
    assert len(records) == 1
    assert records[0].repository_name == "SceneDiff/demo"
