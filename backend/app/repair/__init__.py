"""AI Repair Engine package (Sprint 6).

Exports core planning, context retrieval, patch generation, validation, risk
assessment, rollback calculation, and reporting components.
"""

from app.repair.context import CodeContext, CodeContextRetriever
from app.repair.exporter import PatchExporter
from app.repair.patch_generator import (
    GeneratedPatch,
    MockPatchProvider,
    OllamaPatchProvider,
    PatchProvider,
    TemplatePatchProvider,
)
from app.repair.planner import RepairAction, RepairPlan, RepairPlanner
from app.repair.report import RepairReportBuilder, RepairReportData
from app.repair.risk import RiskAssessmentEngine, RiskAssessmentResult, RiskLevel
from app.repair.rollback import RollbackGenerator, RollbackPlan
from app.repair.validator import PatchValidator, ValidationResult

__all__ = [
    "CodeContext",
    "CodeContextRetriever",
    "GeneratedPatch",
    "MockPatchProvider",
    "OllamaPatchProvider",
    "PatchExporter",
    "PatchProvider",
    "PatchValidator",
    "RepairAction",
    "RepairPlan",
    "RepairPlanner",
    "RepairReportBuilder",
    "RepairReportData",
    "RiskAssessmentEngine",
    "RiskAssessmentResult",
    "RiskLevel",
    "RollbackGenerator",
    "RollbackPlan",
    "TemplatePatchProvider",
    "ValidationResult",
]
