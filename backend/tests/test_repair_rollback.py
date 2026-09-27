"""Unit tests for Rollback Generator Engine (Sprint 6 - Task 52)."""

from __future__ import annotations

from app.repair.rollback import RollbackGenerator, RollbackPlan


def test_rollback_plan_to_dict_and_masking() -> None:
    """RollbackPlan to_dict() serializes commands and precautions."""
    plan = RollbackPlan(
        strategy="Revert patch",
        commands=[
            "git apply -R repair.patch token=ghp_123456789012345678901234567890123456"
        ],
        precautions=["Check working tree"],
        verification_steps=["Run pytest"],
        database_caution=False,
    )
    d = plan.to_dict()
    assert d["strategy"] == "Revert patch"
    assert "ghp_" not in d["commands"][0]
    assert "[REDACTED]" in d["commands"][0]
    assert d["database_caution"] is False


def test_rollback_generator_commands_included() -> None:
    """RollbackGenerator includes git apply -R and git revert commands."""
    plan = RollbackGenerator.generate(
        target_file="app/auth/login.py",
        head_commit="abcdef1234567890",
        patch_filename="auth_fix.patch",
    )
    assert any("git apply -R auth_fix.patch" in cmd for cmd in plan.commands)
    assert any("git revert --no-edit abcdef12" in cmd for cmd in plan.commands)
    assert any("git checkout -- app/auth/login.py" in cmd for cmd in plan.commands)


def test_rollback_generator_verification_steps() -> None:
    """RollbackGenerator provides verification instructions."""
    plan = RollbackGenerator.generate(target_file="app/api/users.py")
    assert any("pytest" in step for step in plan.verification_steps)
    assert any("app/api/users.py" in step for step in plan.verification_steps)
    assert any("health" in step for step in plan.verification_steps)


def test_rollback_generator_precautions() -> None:
    """RollbackGenerator provides safety precautions before revert."""
    plan = RollbackGenerator.generate(target_file="app/main.py")
    assert any("uncommitted" in p.lower() for p in plan.precautions)


def test_rollback_generator_db_caution_flag() -> None:
    """RollbackGenerator flags database caution when database is involved."""
    plan = RollbackGenerator.generate(
        target_file="app/services/user.py",
        is_database_involved=True,
    )
    assert plan.database_caution is True
    assert any("Database interactions detected" in p for p in plan.precautions)


def test_rollback_generator_db_caution_by_filepath() -> None:
    """RollbackGenerator infers database caution from target_file path."""
    plan = RollbackGenerator.generate(target_file="app/db/repositories/item.py")
    assert plan.database_caution is True
    assert any("Database interactions detected" in p for p in plan.precautions)


def test_rollback_generator_short_commit_handling() -> None:
    """RollbackGenerator handles commit SHA shorter than 8 chars."""
    plan = RollbackGenerator.generate(target_file="app/main.py", head_commit="abc")
    assert any("git revert --no-edit abc" in cmd for cmd in plan.commands)
