"""Tests for behavior/severity.py — Severity & Verdict Engine (Sprint 4)."""

from __future__ import annotations

from app.behavior.severity import (
    BehaviorDivergence,
    ComparisonVerdict,
    SeverityLevel,
    determine_verdict,
    get_highest_severity,
)


def _make_div(severity: SeverityLevel) -> BehaviorDivergence:
    return BehaviorDivergence(
        category="dom",
        severity=severity,
        route="/",
        event_type="TEST_EVENT",
        title="Test Title",
        description="Test Description",
    )


class TestSeverityEngine:
    def test_highest_severity_empty(self) -> None:
        assert get_highest_severity([]) == SeverityLevel.INFO

    def test_highest_severity_critical(self) -> None:
        sevs = [SeverityLevel.LOW, SeverityLevel.CRITICAL, SeverityLevel.MEDIUM]
        assert get_highest_severity(sevs) == SeverityLevel.CRITICAL

    def test_highest_severity_string_inputs(self) -> None:
        assert get_highest_severity(["low", "high", "medium"]) == SeverityLevel.HIGH

    def test_determine_verdict_regression_when_critical(self) -> None:
        divs = [_make_div(SeverityLevel.LOW), _make_div(SeverityLevel.CRITICAL)]
        assert determine_verdict(divs) == ComparisonVerdict.REGRESSION

    def test_determine_verdict_regression_when_high(self) -> None:
        divs = [_make_div(SeverityLevel.HIGH)]
        assert determine_verdict(divs) == ComparisonVerdict.REGRESSION

    def test_determine_verdict_warning_when_medium(self) -> None:
        divs = [_make_div(SeverityLevel.LOW), _make_div(SeverityLevel.MEDIUM)]
        assert determine_verdict(divs) == ComparisonVerdict.WARNING

    def test_determine_verdict_clean_when_low_or_info(self) -> None:
        divs = [_make_div(SeverityLevel.LOW), _make_div(SeverityLevel.INFO)]
        assert determine_verdict(divs) == ComparisonVerdict.CLEAN

    def test_determine_verdict_clean_when_empty(self) -> None:
        assert determine_verdict([]) == ComparisonVerdict.CLEAN

    def test_divergence_to_dict(self) -> None:
        div = _make_div(SeverityLevel.HIGH)
        d = div.to_dict()
        assert d["severity"] == "HIGH"
        assert d["category"] == "dom"
        assert d["event_type"] == "TEST_EVENT"
