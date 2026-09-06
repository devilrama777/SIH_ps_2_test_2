"""
Tests for Section 43: Strict LLM-Independence Invariant Verification & Deterministic Core Isolation.
"""

from __future__ import annotations

import os
from pathlib import Path
from fastapi.testclient import TestClient

from apps.processing.server import app
from core.orchestrator.llm_independence_engine import (
    LLMIndependenceAuditor,
    LLMIndependenceAuditReport,
    ZeroLLMGenerationResult,
)


def test_llm_independence_auditor_all_layers(tmp_path):
    auditor = LLMIndependenceAuditor(workspace_dir=str(tmp_path))
    report: LLMIndependenceAuditReport = auditor.audit_all_layers()

    assert report.passed is True
    assert report.compliance_score == 1.0
    assert report.total_layers == 6
    assert report.verified_layers == 6
    assert report.zero_llm_mode_supported is True
    assert "Section 43" in report.master_specification_reference

    layer_ids = [layer.layer_id for layer in report.layers]
    assert layer_ids == [1, 2, 3, 4, 5, 6]

    for layer in report.layers:
        assert layer.is_deterministic is True
        assert layer.status.startswith("VERIFIED")
        assert layer.details.get("requires_llm_for_core_path") is False


def test_execute_zero_llm_generation_creates_verified_pdf_and_report(tmp_path):
    auditor = LLMIndependenceAuditor(workspace_dir=str(tmp_path))
    result: ZeroLLMGenerationResult = auditor.execute_zero_llm_generation(
        output_pdf=True,
        template_name="modern",
    )

    assert result.llm_invocations_count == 0
    assert result.validation_passed is True
    assert result.calculation_checks_passed is True
    assert result.section_count == 5
    assert result.table_count == 3
    assert result.narrative_block_count >= 5
    assert result.page_count >= 1
    assert result.execution_time_ms > 0

    assert result.html_path is not None
    assert os.path.exists(result.html_path)

    assert result.pdf_path is not None
    assert os.path.exists(result.pdf_path)

    # Verify generated HTML content
    with open(result.html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    assert "Northern Coalfields Limited" in html_content
    assert "FY 2024-25" in html_content
    assert "142.60" in html_content  # Total production
    assert "62.1%" in html_content   # Rail dispatch share
    assert "22.7%" in html_content   # Road dispatch share
    assert "15.2%" in html_content   # MGR dispatch share


def test_llm_independence_api_endpoints(tmp_path):
    client = TestClient(app)

    # 1. Test audit endpoint
    audit_resp = client.get("/api/v1/system/llm-independence/audit")
    assert audit_resp.status_code == 200
    audit_data = audit_resp.json()
    assert audit_data["passed"] is True
    assert audit_data["compliance_score"] == 1.0
    assert audit_data["total_layers"] == 6
    assert len(audit_data["layers"]) == 6

    # 2. Test zero-LLM generation endpoint
    gen_resp = client.post(
        "/api/v1/system/llm-independence/zero-llm-generation",
        json={"template_name": "modern", "output_pdf": True},
    )
    assert gen_resp.status_code == 200
    gen_data = gen_resp.json()
    assert gen_data["llm_invocations_count"] == 0
    assert gen_data["validation_passed"] is True
    assert gen_data["calculation_checks_passed"] is True
    assert gen_data["section_count"] >= 3
    assert gen_data["table_count"] >= 2
    assert gen_data["pdf_path"] is not None


def test_layer_audit_serialization_and_metadata(tmp_path):
    auditor = LLMIndependenceAuditor(workspace_dir=str(tmp_path))
    report = auditor.audit_all_layers()
    d = report.to_dict()

    assert isinstance(d, dict)
    assert d["total_layers"] == 6
    assert d["compliance_score"] == 1.0
    assert len(d["layers"]) == 6

    gen_result = auditor.execute_zero_llm_generation()
    gd = gen_result.to_dict()
    assert isinstance(gd, dict)
    assert gd["llm_invocations_count"] == 0
    assert gd["calculation_checks_passed"] is True
