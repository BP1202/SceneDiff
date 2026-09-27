"""Tests for services/comparison_service.py — Comparison Service (Sprint 4)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
import uuid

import pytest

from app.models.behavior_comparison import BehaviorComparison, ComparisonStatus
from app.services import comparison_service


class TestComparisonService:
    @pytest.mark.asyncio()
    async def test_create_comparison_persists(self) -> None:
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        base_artifact = {
            "commit_ref": "aaaaaaa",
            "dom_snapshots": [],
            "network_events": [],
        }
        head_artifact = {
            "commit_ref": "bbbbbbb",
            "dom_snapshots": [],
            "network_events": [],
        }

        comparison, report = await comparison_service.create_comparison(
            db,
            repository_name="SceneDiff",
            base_commit="aaaaaaa",
            head_commit="bbbbbbb",
            base_artifact=base_artifact,
            head_artifact=head_artifact,
        )

        assert comparison.repository_name == "SceneDiff"
        assert comparison.base_commit == "aaaaaaa"
        assert comparison.head_commit == "bbbbbbb"
        assert comparison.status == ComparisonStatus.COMPLETED
        db.flush.assert_awaited_once()
        db.commit.assert_awaited_once()

    @pytest.mark.asyncio()
    async def test_get_comparison_by_id(self) -> None:
        db = AsyncMock()
        mock_comp = MagicMock(spec=BehaviorComparison)
        db.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=mock_comp))
        )

        comp_id = uuid.uuid4()
        result = await comparison_service.get_comparison_by_id(db, comp_id)
        assert result is mock_comp

    @pytest.mark.asyncio()
    async def test_get_comparison_events(self) -> None:
        db = AsyncMock()
        mock_events = [MagicMock(), MagicMock()]
        db.execute = AsyncMock(
            return_value=MagicMock(
                scalars=MagicMock(
                    return_value=MagicMock(all=MagicMock(return_value=mock_events))
                )
            )
        )

        comp_id = uuid.uuid4()
        events = await comparison_service.get_comparison_events(
            db, comp_id, category="network", severity="CRITICAL"
        )
        assert len(events) == 2
