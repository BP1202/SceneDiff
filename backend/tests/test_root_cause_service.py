"""Tests for root_cause_service.py (Sprint 5 - Task 43)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
import uuid

import pytest

from app.models.behavior_comparison import BehaviorComparison, ComparisonEvent
from app.models.root_cause_report import (
    AnalysisStatus,
    ConfidenceLevel,
    RootCauseReport,
)
from app.services import root_cause_service


class TestRootCauseService:
    async def test_create_analysis_raises_if_comparison_not_found(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="not found"):
            await root_cause_service.create_root_cause_analysis(
                db,
                comparison_id=uuid.uuid4(),
            )

    async def test_create_analysis_success(self) -> None:
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        comp_id = uuid.uuid4()
        comp = BehaviorComparison(
            id=comp_id,
            repository_name="SceneDiff",
            base_commit="1111111",
            head_commit="2222222",
        )
        ev = ComparisonEvent(
            id=uuid.uuid4(),
            comparison_id=comp_id,
            category="network",
            severity="CRITICAL",
            route="/api/pay",
            event_type="STATUS_CODE_5XX_INTRODUCED",
            title="500 on pay",
            description="",
            divergence_order=1,
            evidence={},
        )

        mock_comp_res = MagicMock()
        mock_comp_res.scalar_one_or_none.return_value = comp

        mock_ev_res = MagicMock()
        mock_ev_res.scalars.return_value.all.return_value = [ev]

        db.execute.side_effect = [mock_comp_res, mock_ev_res]

        report = await root_cause_service.create_root_cause_analysis(
            db,
            comparison_id=comp_id,
            git_diff_files=["src/pay.py"],
        )

        assert report.comparison_id == comp_id
        assert report.repository_name == "SceneDiff"
        assert report.status == AnalysisStatus.COMPLETED
        assert db.add.call_count >= 2  # report + evidence
        db.commit.assert_awaited_once()

    async def test_get_report_by_id(self) -> None:
        db = AsyncMock()
        rep_id = uuid.uuid4()
        expected = RootCauseReport(
            id=rep_id,
            comparison_id=uuid.uuid4(),
            repository_name="SceneDiff",
            base_commit="111",
            head_commit="222",
            summary="test",
            confidence_score=90,
            confidence_band=ConfidenceLevel.VERY_HIGH,
            primary_candidate={},
        )

        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = expected
        db.execute.return_value = mock_res

        result = await root_cause_service.get_root_cause_report_by_id(db, rep_id)
        assert result is not None
        assert result.id == rep_id
