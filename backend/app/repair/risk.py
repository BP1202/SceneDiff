"""Risk Assessment Engine (Sprint 6 - Task 51).

Evaluates the operational risk of applying an AI-generated patch and
calculates independent repair confidence (Mandatory Improvement 2).
"""

from __future__ import annotations

from dataclasses import dataclass, field
import enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.repair.patch_generator import GeneratedPatch
    from app.repair.validator import ValidationResult

from app.services.secret_shield import mask_string


class RiskLevel(enum.StrEnum):
    """Categorical risk tiers for repair patches."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class RiskAssessmentResult:
    """Detailed risk assessment outcome and repair confidence metrics."""

    level: RiskLevel
    score: int  # 0 to 100 (higher = riskier)
    reasons: list[str] = field(default_factory=list)
    repair_confidence: int = 80  # 0 to 100 (higher = more confident)
    breakdown: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert assessment result to dictionary."""
        return {
            "level": self.level.value,
            "score": self.score,
            "reasons": [mask_string(r) for r in self.reasons],
            "repair_confidence": self.repair_confidence,
            "breakdown": self.breakdown,
        }


class RiskAssessmentEngine:
    """Deterministic scoring engine for patch safety and repair confidence."""

    _SENSITIVE_PATHS = (
        "auth",
        "login",
        "security",
        "crypto",
        "token",
        "session",
        "credential",
        "secret",
        "db",
        "database",
        "permission",
    )

    _API_PATHS = (
        "api",
        "route",
        "endpoint",
        "controller",
        "v1",
        "v2",
    )

    @classmethod
    def assess(
        cls,
        patch: GeneratedPatch,
        validation: ValidationResult,
        root_cause_confidence: int = 85,
    ) -> RiskAssessmentResult:
        """Calculate risk level, score, reasons, and repair confidence.

        Args:
            patch: Generated Git unified patch.
            validation: Multi-layer validation result.
            root_cause_confidence: Confidence score from Sprint 5 diagnosis.

        Returns:
            RiskAssessmentResult with level, score, reasons, and repair_confidence.
        """
        score = 10  # Baseline
        reasons: list[str] = []
        breakdown: dict[str, Any] = {}

        target = patch.target_file.lower().replace("\\", "/")
        total_changed = patch.lines_added + patch.lines_removed

        # 1. Size penalty
        if total_changed > 100:
            score += 40
            reasons.append(f"High churn: {total_changed} lines changed (>100 lines)")
        elif total_changed > 30:
            score += 25
            reasons.append(f"Moderate churn: {total_changed} lines changed (>30 lines)")
        elif total_changed > 10:
            score += 10
            reasons.append(f"Small churn: {total_changed} lines changed")
        else:
            score += 5
            reasons.append(
                f"Minimal churn: {total_changed} lines changed (targeted fix)"
            )

        # 2. Sensitive directory check
        is_sensitive = any(term in target for term in cls._SENSITIVE_PATHS)
        if is_sensitive:
            score += 35
            reasons.append(
                f"Authentication/Security module modified: {patch.target_file}"
            )

        # 3. Public API / Route check
        is_api = any(term in target for term in cls._API_PATHS)
        if is_api and not is_sensitive:
            score += 20
            reasons.append(f"Public API endpoint modified: {patch.target_file}")

        # 4. Validation penalty
        if not validation.is_valid:
            score = max(score, 90)
            reasons.append("Patch failed one or more validation checks")
        if validation.secret_scan == "failed":  # noqa: S105
            score = 100
            reasons.append("CRITICAL: Secret Shield detected credentials inside patch")

        # Clamp risk score
        score = max(0, min(100, score))

        # Categorize risk level
        if score >= 80:
            is_secret_fail = validation.secret_scan == "failed"  # noqa: S105
            level = RiskLevel.CRITICAL if is_secret_fail else RiskLevel.HIGH
        elif score >= 50:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.LOW

        breakdown["churn_score"] = total_changed
        breakdown["is_sensitive"] = is_sensitive
        breakdown["is_api"] = is_api
        breakdown["validation_passed"] = validation.is_valid

        # -------------------------------------------------------------------
        # Mandatory Improvement 2: Independent Repair Confidence
        # -------------------------------------------------------------------
        # Starts from root cause confidence, adjusted by patch precision & validation
        confidence = root_cause_confidence

        if validation.is_valid:
            confidence += 5  # Bonus for AST & syntax validation passing
        else:
            confidence -= 35  # Major penalty for validation failure

        if validation.ast_valid and patch.target_file.endswith(".py"):
            confidence += 5  # Verified parseable AST

        if total_changed <= 15:
            confidence += 5  # Tight targeted fix
        elif total_changed > 80:
            confidence -= 15  # Loose high-churn edit

        # If risk is extremely high, repair confidence is tempered
        if level == RiskLevel.HIGH:
            confidence -= 5
        elif level == RiskLevel.CRITICAL:
            confidence -= 25

        repair_confidence = max(5, min(99, confidence))
        breakdown["repair_confidence"] = repair_confidence
        breakdown["root_cause_confidence"] = root_cause_confidence

        return RiskAssessmentResult(
            level=level,
            score=score,
            reasons=reasons,
            repair_confidence=repair_confidence,
            breakdown=breakdown,
        )
