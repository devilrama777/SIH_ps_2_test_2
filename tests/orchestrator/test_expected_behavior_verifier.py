"""
Unit and integration tests for Section 45: Expected Development Behavior & Modular Swappability.
"""
import pytest
from fastapi.testclient import TestClient

from apps.processing.server import app
from core.orchestrator.expected_behavior_verifier import (
    ArchitecturalPriority,
    CORE_AUDITED_COMPONENTS,
    ExpectedBehaviorVerifier,
    PRIORITY_RANKING,
    SECTION_45_SWAP_CONTRACTS,
)


@pytest.fixture
def verifier():
    return ExpectedBehaviorVerifier()


@pytest.fixture
def api_client():
    return TestClient(app)


def test_audit_all_core_components_7_inquiries(verifier):
    """Verify that all core components pass the 7 Section 45 architectural inquiries."""
    report = verifier.run_full_audit()

    assert report.all_components_compliant is True
    assert len(report.audited_components) == len(CORE_AUDITED_COMPONENTS)

    for comp in report.audited_components:
        assert comp.all_satisfied is True
        assert len(comp.inquiries) == 7

        inquiry_names = [q.inquiry_name for q in comp.inquiries]
        assert "Responsibility" in inquiry_names
        assert "Inputs" in inquiry_names
        assert "Outputs" in inquiry_names
        assert "Dependencies" in inquiry_names
        assert "Failure Modes" in inquiry_names
        assert "Security Implications" in inquiry_names
        assert "Test Strategy" in inquiry_names

        for q in comp.inquiries:
            assert q.satisfied is True, f"Inquiry '{q.inquiry_name}' failed for {comp.component_name}"


def test_verify_5_modular_swappability_contracts(verifier):
    """Verify that the 5 modular swappability interfaces are decoupled and importable."""
    contracts = verifier.verify_modular_swappability()

    assert len(contracts) == 5
    assert len(contracts) == len(SECTION_45_SWAP_CONTRACTS)

    keys = {c.subsystem_key for c in contracts}
    assert keys == {"llm", "connector", "template", "database", "ocr"}

    for c in contracts:
        assert c.interface_verified is True, f"Interface unverified for {c.subsystem_key}"
        assert c.source_verified is True, f"Source unverified for {c.subsystem_key}"
        assert c.target_verified is True, f"Target unverified for {c.subsystem_key}"
        assert c.decoupled is True, f"Decoupling failed for {c.subsystem_key}"


def test_simulate_hot_swaps_all_5_subsystems(verifier):
    """Simulate live hot-swap across all 5 decoupled subsystems."""
    for key in ["llm", "connector", "template", "database", "ocr"]:
        result = verifier.simulate_swap(key)
        assert result.success is True, f"Swap simulation failed for {key}: {result.message}"
        assert result.contract_adhered is True, f"Contract violated for {key}"
        assert result.affected_unrelated_modules == 0, f"Unrelated modules affected for {key}"
        assert result.latency_ms >= 0.0

    # Test unrecognized key handling
    invalid_result = verifier.simulate_swap("nonexistent_subsystem")
    assert invalid_result.success is False
    assert invalid_result.contract_adhered is False
    assert "not recognized" in invalid_result.message


def test_validate_priority_hierarchy(verifier):
    """Verify that the 6-level architectural priority hierarchy is strictly monotonic and enforced."""
    prio_data = verifier.validate_priority_hierarchy()

    assert prio_data["valid_monotonic_ordering"] is True
    assert prio_data["all_invariants_enforced"] is True

    hierarchy = prio_data["hierarchy"]
    assert hierarchy == [
        "correctness",
        "traceability",
        "security",
        "maintainability",
        "performance",
        "visual_polish",
    ]

    # Verify rank comparison
    assert PRIORITY_RANKING[ArchitecturalPriority.CORRECTNESS] < PRIORITY_RANKING[ArchitecturalPriority.TRACEABILITY]
    assert PRIORITY_RANKING[ArchitecturalPriority.TRACEABILITY] < PRIORITY_RANKING[ArchitecturalPriority.SECURITY]
    assert PRIORITY_RANKING[ArchitecturalPriority.SECURITY] < PRIORITY_RANKING[ArchitecturalPriority.MAINTAINABILITY]
    assert PRIORITY_RANKING[ArchitecturalPriority.MAINTAINABILITY] < PRIORITY_RANKING[ArchitecturalPriority.PERFORMANCE]
    assert PRIORITY_RANKING[ArchitecturalPriority.PERFORMANCE] < PRIORITY_RANKING[ArchitecturalPriority.VISUAL_POLISH]


def test_expected_behavior_api_endpoints(api_client):
    """Verify Section 45 REST API endpoints in server.py."""
    # 1. Audit endpoint
    audit_res = api_client.get("/api/v1/system/expected-behavior/audit")
    assert audit_res.status_code == 200
    data = audit_res.json()
    assert data["overall_compliance_score"] == 100.0
    assert data["all_components_compliant"] is True
    assert data["all_swaps_verified"] is True
    assert data["priority_hierarchy_enforced"] is True
    assert len(data["audited_components"]) == 5
    assert len(data["swappability_contracts"]) == 5

    # 2. Verify component endpoint
    comp_res = api_client.post(
        "/api/v1/system/expected-behavior/verify-component",
        json={"component_name": "ReportDatabase"},
    )
    assert comp_res.status_code == 200
    comp_data = comp_res.json()
    assert comp_data["component_name"] == "ReportDatabase"
    assert comp_data["all_satisfied"] is True
    assert len(comp_data["inquiries"]) == 7

    # 3. Simulate swap endpoint
    for key in ["llm", "connector", "template", "database", "ocr"]:
        swap_res = api_client.post(
            "/api/v1/system/expected-behavior/simulate-swap",
            json={"subsystem_key": key},
        )
        assert swap_res.status_code == 200
        swap_data = swap_res.json()
        assert swap_data["success"] is True
        assert swap_data["affected_unrelated_modules"] == 0
        assert swap_data["contract_adhered"] is True
