"""Unit tests for Repair Planning Engine (Sprint 6 - Task 47)."""

from __future__ import annotations

from app.repair.planner import RepairAction, RepairPlan, RepairPlanner


def test_repair_action_to_dict_and_masking() -> None:
    """RepairAction serializes and masks potential secrets."""
    action = RepairAction(
        step=1,
        description="Inspect token eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.signature",
        rationale="Fix secret leakage",
        is_automated=True,
    )
    data = action.to_dict()
    assert data["step"] == 1
    assert "eyJ" not in data["description"]
    assert "[REDACTED]" in data["description"]
    assert data["is_automated"] is True


def test_repair_plan_to_dict() -> None:
    """RepairPlan to_dict() serializes all fields properly."""
    plan = RepairPlan(
        summary="Fix auth token null guard",
        target_file="app/auth/login.py",
        target_function="validate_token",
        actions=[
            RepairAction(
                step=1,
                description="Add check",
                rationale="Protect against None",
            )
        ],
        prerequisites=["Check tree"],
        validation_checklist=["Run pytest"],
        metadata={"version": "1.0"},
    )
    serialized = plan.to_dict()
    assert serialized["summary"] == "Fix auth token null guard"
    assert serialized["target_file"] == "app/auth/login.py"
    assert serialized["target_function"] == "validate_token"
    assert len(serialized["actions"]) == 1
    assert serialized["prerequisites"] == ["Check tree"]
    assert serialized["validation_checklist"] == ["Run pytest"]
    assert serialized["metadata"] == {"version": "1.0"}


def test_planner_null_handling_strategy() -> None:
    """Planner generates null guard strategy when reason involves None/null."""
    report_dict = {
        "primary_candidate": {
            "file_path": "app/auth/login.py",
            "function_name": "validate_token",
            "reason": "validate_token returns None unexpectedly",
            "evidence_type": "null_return",
        },
        "summary": "validate_token returned None",
    }
    plan = RepairPlanner.plan(report_dict)
    assert plan.target_file == "app/auth/login.py"
    assert plan.target_function == "validate_token"
    assert "null handling" in plan.summary.lower()
    assert len(plan.actions) == 4
    descriptions = [a.description.lower() for a in plan.actions]
    assert any("null guard" in d for d in descriptions)
    assert any("domain exception" in d for d in descriptions)


def test_planner_500_server_error_strategy() -> None:
    """Planner generates exception handler strategy for 500 status / server error."""
    report_dict = {
        "primary_candidate": {
            "file_path": "app/api/checkout.py",
            "function_name": "process_payment",
            "reason": "Internal server crash during credit card charge",
            "evidence_type": "HTTP_500",
        },
        "summary": "500 Internal Server Error in payment endpoint",
    }
    plan = RepairPlanner.plan(report_dict)
    assert "500 server error" in plan.summary.lower()
    assert len(plan.actions) == 3
    descriptions = [a.description.lower() for a in plan.actions]
    assert any("exception handler" in d for d in descriptions)
    assert any("domain error response" in d for d in descriptions)


def test_planner_route_not_found_strategy() -> None:
    """Planner generates routing fix strategy for 404 not found."""
    report_dict = {
        "primary_candidate": {
            "file_path": "app/api/users.py",
            "function_name": "get_user_profile",
            "reason": "Route path /users/v2 not found",
            "evidence_type": "HTTP_404",
        },
        "summary": "404 route missing",
    }
    plan = RepairPlanner.plan(report_dict)
    assert "route availability" in plan.summary.lower()
    assert len(plan.actions) == 2
    assert any("route handler" in a.description.lower() for a in plan.actions)


def test_planner_storage_state_strategy() -> None:
    """Planner generates storage synchronization strategy for token/state issues."""
    report_dict = {
        "primary_candidate": {
            "file_path": "src/services/session.ts",
            "function_name": "saveToken",
            "reason": "LocalStorage token key missing after reload",
            "evidence_type": "storage_discrepancy",
        },
        "summary": "Missing auth token in storage",
    }
    plan = RepairPlanner.plan(report_dict)
    assert "state synchronization" in plan.summary.lower()
    assert len(plan.actions) == 2
    assert any("state persistence" in a.description.lower() for a in plan.actions)


def test_planner_generic_fallback_strategy() -> None:
    """Planner falls back to defensive boundary check for unclassified issues."""
    report_dict = {
        "primary_candidate": {
            "file_path": "src/utils/calc.py",
            "function_name": "compute_total",
            "reason": "Calculation variance across commits",
            "evidence_type": "divergence",
        },
        "summary": "Value calculation mismatch",
    }
    plan = RepairPlanner.plan(report_dict)
    assert "repair logic" in plan.summary.lower()
    assert len(plan.actions) == 3
    assert any(
        "defensive boundary guard" in a.description.lower() for a in plan.actions
    )


def test_planner_resolves_from_raw_repair_plan() -> None:
    """Planner falls back to raw_repair_plan if primary_candidate has missing paths."""
    report_dict = {
        "primary_candidate": {},
        "repair_plan": [
            {
                "target_file": "app/core/engine.py",
                "target_function": "execute_step",
            }
        ],
        "summary": "Step failure",
    }
    plan = RepairPlanner.plan(report_dict)
    assert plan.target_file == "app/core/engine.py"
    assert plan.target_function == "execute_step"


def test_planner_with_object_input() -> None:
    """Planner works when passed a model-like object with attributes."""

    class DummyReport:
        def __init__(self) -> None:
            self.primary_candidate = {
                "file_path": "app/auth/jwt.py",
                "function_name": "decode_token",
                "reason": "token decode null pointer",
                "evidence_type": "error",
            }
            self.summary = "JWT null pointer"
            self.repair_plan = []

    plan = RepairPlanner.plan(DummyReport())
    assert plan.target_file == "app/auth/jwt.py"
    assert plan.target_function == "decode_token"
    assert "null handling" in plan.summary.lower()


def test_planner_prerequisites_and_checklists() -> None:
    """Planner includes default safety prerequisites and verification checklist."""
    report_dict = {
        "primary_candidate": {
            "file_path": "backend/app/main.py",
            "function_name": "lifespan",
        },
        "summary": "Startup crash",
    }
    plan = RepairPlanner.plan(report_dict)
    assert any("clean" in p.lower() for p in plan.prerequisites)
    assert any("syntax" in c.lower() for c in plan.validation_checklist)
    assert any("secret shield" in c.lower() for c in plan.validation_checklist)
