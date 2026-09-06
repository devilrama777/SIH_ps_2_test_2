"""
Tests for Phase 39 Master Development Phases & Definition-of-Done System Integration Audit.
Covers:
- Section 39: DEVELOPMENT PHASES (Phases 0 through 12)
- Section 42: DEFINITION OF DONE (8 mandatory criteria per phase)
- Section 43: IMPORTANT ARCHITECTURAL PRINCIPLE (Independence from local LLM)
- REST API endpoints GET and POST /api/v1/system/phases-audit
"""

import json
from pathlib import Path
from fastapi.testclient import TestClient
import pytest

from core.orchestrator.development_phases_audit import (
    DevelopmentPhasesAuditor,
    DoDScorecard,
    PhaseAuditResult,
)
from apps.processing.server import app


@pytest.fixture
def repo_root():
    return Path(__file__).resolve().parent.parent.parent


@pytest.fixture
def auditor(repo_root):
    return DevelopmentPhasesAuditor(repo_root=str(repo_root))


@pytest.fixture
def client():
    return TestClient(app)


def test_dod_scorecard_calculation():
    """Validates the 8 mandatory engineering criteria scoring calculation from Section 42."""
    perfect_scorecard = DoDScorecard(
        has_implementation=True,
        has_unit_tests=True,
        has_integration_tests=True,
        has_error_handling=True,
        has_logging=True,
        has_documentation=True,
        has_security_review=True,
        has_performance_measurement=True,
    )
    assert perfect_scorecard.score() == 1.0
    d = perfect_scorecard.to_dict()
    assert d["score"] == 1.0
    assert d["has_documentation"] is True

    partial_scorecard = DoDScorecard(
        has_implementation=True,
        has_unit_tests=True,
        has_integration_tests=False,
        has_error_handling=True,
        has_logging=True,
        has_documentation=False,
        has_security_review=False,
        has_performance_measurement=False,
    )
    # 4 out of 8 = 0.50
    assert partial_scorecard.score() == 0.5


def test_development_phases_auditor_all_13_phases(auditor):
    """
    Validates Section 39:
    All 13 development phases (0 through 12) must be evaluated, achieving 100% completion
    and an average Definition-of-Done score >= 0.95.
    """
    report = auditor.run_comprehensive_audit()

    assert report["total_phases"] == 13
    assert report["completed_phases"] == 13
    assert report["completion_percentage"] == 100.0
    assert report["average_dod_score"] >= 0.95
    assert report["overall_certified"] is True

    # Verify phase numbers and ordering
    phases = report["phases"]
    assert len(phases) == 13
    for idx, p in enumerate(phases):
        assert p["phase_number"] == idx
        assert p["is_complete"] is True
        assert p["dod_score"] >= 0.85
        assert len(p["deliverables"]) > 0
        assert len(p["primary_code_files"]) > 0
        assert len(p["associated_tests"]) > 0
        assert p["documentation_record"].endswith(".md")


def test_section_43_llm_independence_principle(auditor):
    """
    Validates Section 43:
    'The system's source data, structured evidence, deterministic calculations, provenance,
    validation and report model must remain independent of the local LLM.'
    """
    res = auditor.verify_section_43_architectural_principle()

    assert res["compliant"] is True
    checks = res["checks"]
    assert checks["deterministic_canonical_model"] is True
    assert checks["deterministic_calculations"] is True
    assert checks["sqlite_fts5_indexing"] is True
    assert checks["provenance_tracker"] is True
    assert checks["tamper_evident_audit"] is True
    assert checks["dual_template_renderer"] is True


def test_audit_persistence_file(auditor, repo_root):
    """Validates that the comprehensive audit writes a persistent JSON artifact."""
    report = auditor.run_comprehensive_audit()
    artifact_path = repo_root / "data" / "workspace" / "audit_logs" / "development_phases_audit.json"

    assert artifact_path.exists()
    loaded = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert loaded["total_phases"] == report["total_phases"]
    assert loaded["completion_percentage"] == report["completion_percentage"]
    assert loaded["overall_certified"] is True


def test_phases_audit_api_endpoints(client):
    """Validates REST API endpoints GET and POST /api/v1/system/phases-audit."""
    # GET endpoint
    resp_get = client.get("/api/v1/system/phases-audit")
    assert resp_get.status_code == 200
    data_get = resp_get.json()
    assert data_get["total_phases"] == 13
    assert data_get["completed_phases"] == 13
    assert data_get["completion_percentage"] == 100.0
    assert data_get["overall_certified"] is True

    # POST run endpoint (triggers audit and logs audit event)
    resp_post = client.post("/api/v1/system/phases-audit/run")
    assert resp_post.status_code == 200
    data_post = resp_post.json()
    assert data_post["total_phases"] == 13
    assert data_post["overall_certified"] is True
    assert data_post["section_43_llm_independence"]["compliant"] is True
