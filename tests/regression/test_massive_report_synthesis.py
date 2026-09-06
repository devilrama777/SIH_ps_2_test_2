"""
Regression and Master Showcase Tests for Phase 36: Massive Enterprise Report Synthesis.
Section 0, Section 22, Section 23 & Section 30 of Master Implementation Specification.
"""
from __future__ import annotations

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from apps.processing.server import app
from core.orchestrator.enterprise_synthesis import (
    EnterpriseReportSynthesizer,
    EnterpriseSynthesisConfig,
    EnterpriseSynthesisResult,
    MANDATORY_CIL_CHAPTERS,
)

client = TestClient(app)


def test_enterprise_synthesis_execution(tmp_path: Path):
    synthesizer = EnterpriseReportSynthesizer(workspace_dir=str(tmp_path))
    cfg = EnterpriseSynthesisConfig(
        subsidiary_code="CCL",
        reporting_period="FY 2023-24",
        target_page_scale=25,
        workspace_dir=str(tmp_path),
    )

    res: EnterpriseSynthesisResult = synthesizer.synthesize(cfg)

    assert res.report_id.startswith("rep_")
    assert res.numerical_accuracy_rate == 100.0  # 0.00% numerical error rate
    assert res.total_sections >= 8
    assert len(res.chapters_generated) == 8
    for ch in MANDATORY_CIL_CHAPTERS:
        assert ch in res.chapters_generated

    # Verify generated artifacts
    assert res.pdf_path is not None
    assert Path(res.pdf_path).exists()
    assert res.export_bundle_path is not None
    assert Path(res.export_bundle_path).exists()
    assert res.manifest_sha256 is not None
    assert len(res.manifest_sha256) == 64


def test_enterprise_synthesis_manifest_verification(tmp_path: Path):
    synthesizer = EnterpriseReportSynthesizer(workspace_dir=str(tmp_path))
    cfg = EnterpriseSynthesisConfig(
        subsidiary_code="CCL",
        reporting_period="FY 2023-24",
        workspace_dir=str(tmp_path),
    )
    res = synthesizer.synthesize(cfg)

    manifest_file = Path(res.export_bundle_path) / "manifest.json"
    assert manifest_file.exists()

    data = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert data["manifest_sha256"] == res.manifest_sha256
    assert data["numerical_error_rate"] == 0.00
    assert len(data["chapters"]) == 8


def test_enterprise_synthesis_rest_api(tmp_path: Path):
    payload = {
        "subsidiary_code": "CCL",
        "reporting_period": "FY 2023-24",
        "target_page_scale": 15,
        "workspace_dir": str(tmp_path),
        "enable_dual_rendering": True,
    }

    resp = client.post("/api/v1/reports/synthesize/enterprise", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["numerical_accuracy_rate"] == 100.0
    assert "manifest_sha256" in data
    assert len(data["chapters_generated"]) == 8
