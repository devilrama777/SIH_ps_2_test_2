"""
Tests for Section 44: Master 30-Step Execution Order Verification & Dependency Progression Engine.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from apps.processing.server import app
from core.orchestrator.implementation_order_engine import (
    ImplementationOrderEngine,
    ImplementationOrderReport,
    StepAuditResult,
    SECTION_44_STEPS,
)


def test_dag_validity_and_topological_sort():
    engine = ImplementationOrderEngine()

    assert engine.validate_dependency_dag() is True
    topological_sequence = engine.compute_topological_sequence()
    assert len(topological_sequence) == 30

    # Ensure every prerequisite appears strictly before the dependent step
    seen_indices = {}
    for idx, step_num in enumerate(topological_sequence):
        seen_indices[step_num] = idx

    for step in SECTION_44_STEPS:
        step_pos = seen_indices[step.step_number]
        for prereq in step.prerequisites:
            prereq_pos = seen_indices[prereq]
            assert prereq_pos < step_pos, f"Prerequisite Step #{prereq} must precede Step #{step.step_number}"


def test_audit_all_steps_100_percent_completed():
    engine = ImplementationOrderEngine()
    report: ImplementationOrderReport = engine.audit_all_steps()

    assert report.total_steps == 30
    assert report.completed_steps == 30
    assert report.completion_pct == 100.0
    assert report.all_completed is True
    assert report.topological_order_valid is True
    assert "Section 44" in report.specification_section
    assert len(report.steps) == 30

    for step in report.steps:
        assert step.completed is True, f"Step #{step.step_number} ({step.title}) failed: {step.details}"
        assert step.artifact_exists is True
        assert step.test_exists is True
        assert step.prerequisites_satisfied is True
        assert step.contract_verified is True


def test_verify_individual_step():
    engine = ImplementationOrderEngine()

    # Step 1: Root foundation step
    step_1 = engine.verify_step(1)
    assert step_1.step_number == 1
    assert step_1.category == "FOUNDATION"
    assert step_1.prerequisites == []
    assert step_1.prerequisites_satisfied is True
    assert step_1.completed is True

    # Step 6: Canonical Document Model
    step_6 = engine.verify_step(6)
    assert step_6.step_number == 6
    assert step_6.category == "EVIDENCE_MODEL"
    assert step_6.prerequisites == [5]
    assert step_6.contract_verified is True
    assert step_6.completed is True

    # Step 30: Final Product Vision End-to-End
    step_30 = engine.verify_step(30)
    assert step_30.step_number == 30
    assert step_30.category == "END_TO_END"
    assert step_30.prerequisites == [27, 28, 29]
    assert step_30.completed is True

    # Out of range step
    step_invalid = engine.verify_step(999)
    assert step_invalid.completed is False
    assert "outside" in step_invalid.details


def test_implementation_order_api_endpoints():
    client = TestClient(app)

    # 1. Audit endpoint
    audit_resp = client.get("/api/v1/system/implementation-order/audit")
    assert audit_resp.status_code == 200
    data = audit_resp.json()
    assert data["total_steps"] == 30
    assert data["completed_steps"] == 30
    assert data["completion_pct"] == 100.0
    assert data["all_completed"] is True
    assert data["topological_order_valid"] is True
    assert len(data["steps"]) == 30

    # 2. Individual step verification endpoint
    step_resp = client.post(
        "/api/v1/system/implementation-order/verify-step",
        json={"step_number": 4},
    )
    assert step_resp.status_code == 200
    step_data = step_resp.json()
    assert step_data["step_number"] == 4
    assert step_data["completed"] is True
    assert step_data["category"] == "DATA_INGESTION"
    assert step_data["contract_verified"] is True
