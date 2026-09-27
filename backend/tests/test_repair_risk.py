"""Unit tests for Risk Assessment Engine (Sprint 6 - Task 51)."""

from __future__ import annotations

from app.repair.patch_generator import GeneratedPatch
from app.repair.risk import RiskAssessmentEngine, RiskAssessmentResult, RiskLevel
from app.repair.validator import ValidationResult


def _mock_patch(
    target_file: str = "app/utils/calc.py",
    lines_added: int = 3,
    lines_removed: int = 1,
) -> GeneratedPatch:
    return GeneratedPatch(
        target_file=target_file,
        diff_content="diff --git a/test b/test",
        lines_added=lines_added,
        lines_removed=lines_removed,
        provider="TemplatePatchProvider",
        description="Fix calculation",
    )


def _mock_validation(
    is_valid: bool = True,
    secret_scan: str = "passed",
    ast_valid: bool = True,
) -> ValidationResult:
    return ValidationResult(
        is_valid=is_valid,
        syntax_valid=True,
        ast_valid=ast_valid,
        secret_scan=secret_scan,
        scope_valid=True,
    )


def test_risk_result_to_dict() -> None:
    """RiskAssessmentResult serializes correctly."""
    res = RiskAssessmentResult(
        level=RiskLevel.LOW,
        score=20,
        reasons=["Minimal churn"],
        repair_confidence=92,
        breakdown={"churn": 4},
    )
    d = res.to_dict()
    assert d["level"] == "LOW"
    assert d["score"] == 20
    assert d["repair_confidence"] == 92
    assert d["reasons"] == ["Minimal churn"]


def test_risk_low_tier_assessment() -> None:
    """Small patch in non-sensitive utility file is scored LOW."""
    patch = _mock_patch("app/utils/format.py", lines_added=2, lines_removed=1)
    validation = _mock_validation()
    res = RiskAssessmentEngine.assess(patch, validation)
    assert res.level == RiskLevel.LOW
    assert res.score < 50
    assert any("Minimal churn" in r for r in res.reasons)


def test_risk_moderate_churn_tier() -> None:
    """Moderate churn increases risk score."""
    patch = _mock_patch("app/services/analytics.py", lines_added=35, lines_removed=5)
    validation = _mock_validation()
    res = RiskAssessmentEngine.assess(patch, validation)
    assert res.score >= 35
    assert any("Moderate churn" in r for r in res.reasons)


def test_risk_sensitive_directory_auth() -> None:
    """Modification to authentication module triggers HIGH risk."""
    patch = _mock_patch("app/auth/login.py", lines_added=5, lines_removed=2)
    validation = _mock_validation()
    res = RiskAssessmentEngine.assess(patch, validation)
    assert res.score >= 50
    assert any("Authentication/Security module" in r for r in res.reasons)


def test_risk_sensitive_directory_database() -> None:
    """Modification to db module triggers sensitive penalty."""
    patch = _mock_patch("app/db/session.py", lines_added=4, lines_removed=1)
    validation = _mock_validation()
    res = RiskAssessmentEngine.assess(patch, validation)
    assert any("Authentication/Security module" in r for r in res.reasons)


def test_risk_public_api_endpoint() -> None:
    """Public API modification is flagged in reasons."""
    patch = _mock_patch("app/api/v1/routes/users.py", lines_added=5, lines_removed=1)
    validation = _mock_validation()
    res = RiskAssessmentEngine.assess(patch, validation)
    assert any("Public API endpoint modified" in r for r in res.reasons)


def test_risk_validation_failure_escalates_score() -> None:
    """Validation failure escalates risk score to high tier."""
    patch = _mock_patch("app/utils/calc.py", lines_added=2, lines_removed=1)
    validation = _mock_validation(is_valid=False)
    res = RiskAssessmentEngine.assess(patch, validation)
    assert res.score >= 90
    assert any("failed one or more validation checks" in r for r in res.reasons)


def test_risk_secret_shield_failure_is_critical() -> None:
    """Secret Shield failure flags CRITICAL risk level."""
    patch = _mock_patch("app/auth/login.py")
    validation = _mock_validation(is_valid=False, secret_scan="failed")
    res = RiskAssessmentEngine.assess(patch, validation)
    assert res.level == RiskLevel.CRITICAL
    assert res.score == 100
    assert any("Secret Shield detected credentials" in r for r in res.reasons)


def test_repair_confidence_computation() -> None:
    """Valid AST + small churn improves repair confidence."""
    patch = _mock_patch("app/auth/login.py", lines_added=4, lines_removed=1)
    validation = _mock_validation(is_valid=True, ast_valid=True)
    res = RiskAssessmentEngine.assess(patch, validation, root_cause_confidence=85)
    assert res.repair_confidence >= 95


def test_repair_confidence_penalized_on_invalid() -> None:
    """Failed validation significantly decreases repair confidence."""
    patch = _mock_patch("app/utils/calc.py", lines_added=4, lines_removed=1)
    validation = _mock_validation(is_valid=False, ast_valid=False)
    res = RiskAssessmentEngine.assess(patch, validation, root_cause_confidence=80)
    assert res.repair_confidence < 60
