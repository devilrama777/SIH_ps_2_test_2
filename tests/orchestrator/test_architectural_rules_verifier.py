"""
Comprehensive Test Suite for Phase 41: Master Architectural Rules, Invariants & Modular Swappability Audit.
Tests compliance with:
- Section 41: IMPLEMENTATION RULE FOR THE IDE AGENT (15 non-negotiable rules)
- Section 44: IMMEDIATE IMPLEMENTATION ORDER (30 foundation-first steps)
- Section 45: EXPECTED DEVELOPMENT BEHAVIOR & MODULAR SWAPPABILITY (5 interface swaps & priority hierarchy)
"""

import pytest
from fastapi.testclient import TestClient

from apps.processing.server import app
from core.orchestrator.architectural_rules_verifier import (
    PRIORITY_HIERARCHY,
    PRIORITY_HIERARCHY_STRING,
    ArchitecturalRulesVerifier,
)


@pytest.fixture
def verifier():
    return ArchitecturalRulesVerifier()


@pytest.fixture
def client():
    return TestClient(app)


def test_section_41_rules_audit_all_pass(verifier):
    """Verifies that all 15 rules from Section 41 pass with 100% compliance."""
    rules = verifier.audit_section_41_rules()
    assert len(rules) == 15, f"Expected 15 rules, got {len(rules)}"

    failed_rules = [r for r in rules if not r.passed]
    assert len(failed_rules) == 0, f"Failed rules: {[(r.rule_number, r.title, r.details) for r in failed_rules]}"

    # Verify key rules explicitly
    rule_map = {r.rule_number: r for r in rules}
    assert rule_map[1].title == "Inspect the existing workspace first"
    assert rule_map[11].title == "Keep AI providers behind the AI Gateway"
    assert rule_map[12].title == "Keep data sources behind DataConnector"
    assert rule_map[13].title == "Keep PDF templates behind the report renderer abstraction"
    assert rule_map[14].title == "Keep provenance independent of UI"
    assert rule_map[15].title == "Keep security controls independent of the LLM"


def test_section_44_steps_all_completed(verifier):
    """Verifies that all 30 immediate implementation steps from Section 44 exist and are complete."""
    steps = verifier.audit_section_44_steps()
    assert len(steps) == 30, f"Expected 30 steps, got {len(steps)}"

    missing_steps = [s for s in steps if not s.completed]
    assert len(missing_steps) == 0, f"Missing steps: {[(s.step_number, s.title, s.primary_artifact) for s in missing_steps]}"

    step_map = {s.step_number: s for s in steps}
    assert step_map[1].step_number == 1
    assert step_map[30].step_number == 30
    assert "final_product_vision.py" in step_map[30].primary_artifact


def test_section_45_modular_swappability(verifier):
    """Verifies that all 5 decoupled interface swaps from Section 45 function properly."""
    swappable_items = verifier.audit_section_45_swappability()
    assert len(swappable_items) == 5, f"Expected 5 swappable components, got {len(swappable_items)}"

    unswappable = [sw for sw in swappable_items if not sw.swappable]
    assert len(unswappable) == 0, f"Unswappable components: {[(sw.component_id, sw.title, sw.details) for sw in unswappable]}"

    item_map = {sw.component_id: sw for sw in swappable_items}
    # 1. Gemma -> another local model
    assert "ai_gateway" in item_map
    assert item_map["ai_gateway"].swappable is True
    # 2. LocalFolder -> CIL server
    assert "data_connector" in item_map
    assert item_map["data_connector"].swappable is True
    # 3. Classic template -> new template
    assert "report_renderer" in item_map
    assert item_map["report_renderer"].swappable is True
    # 4. SQLite -> future database
    assert "storage_database" in item_map
    assert item_map["storage_database"].swappable is True
    # 5. PaddleOCR -> another OCR engine
    assert "ocr_manager" in item_map
    assert item_map["ocr_manager"].swappable is True


def test_priority_hierarchy(verifier):
    """Verifies that the Section 45 priority hierarchy is strictly preserved."""
    assert PRIORITY_HIERARCHY == [
        "correctness",
        "traceability",
        "security",
        "maintainability",
        "performance",
        "visual_polish",
    ]
    assert PRIORITY_HIERARCHY_STRING == "correctness > traceability > security > maintainability > performance > visual polish"


def test_full_audit_certified_verdict(verifier):
    """Verifies that run_full_audit returns CERTIFIED_COMPLIANT with 50/50 checks passing."""
    report = verifier.run_full_audit()
    assert report.overall_verdict == "CERTIFIED_COMPLIANT"
    assert report.total_passed_checks == 50
    assert report.total_checks == 50
    assert report.section_41_compliance_pct == 100.0
    assert report.section_44_completion_pct == 100.0
    assert report.section_45_verified is True
    assert report.execution_time_ms > 0.0

    d = report.to_dict()
    assert d["overall_verdict"] == "CERTIFIED_COMPLIANT"
    assert len(d["section_41_rules"]) == 15
    assert len(d["section_44_steps"]) == 30
    assert len(d["section_45_swappability"]) == 5


def test_rest_api_rules_audit_endpoints(client):
    """Verifies the GET and POST rules audit endpoints via FastAPI TestClient."""
    # 1. GET /api/v1/system/rules-audit
    resp = client.get("/api/v1/system/rules-audit")
    assert resp.status_code == 200
    data = resp.json()
    assert data["overall_verdict"] == "CERTIFIED_COMPLIANT"
    assert data["total_passed_checks"] == 50
    assert data["total_checks"] == 50
    assert data["section_41_compliance_pct"] == 100.0
    assert data["section_44_completion_pct"] == 100.0
    assert data["section_45_verified"] is True
    assert "correctness > traceability > security" in data["priority_hierarchy"]["statement"]

    # 2. POST /api/v1/system/rules-audit/verify-swappability
    post_resp = client.post("/api/v1/system/rules-audit/verify-swappability")
    assert post_resp.status_code == 200
    post_data = post_resp.json()
    assert post_data["all_swappable"] is True
    assert len(post_data["swappability_results"]) == 5
    assert "timestamp" in post_data
