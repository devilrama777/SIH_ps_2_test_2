"""
Test Suite for Phase 42: Master Production Readiness, Live System Watchdog & Final Certification.
Verifies:
- SystemWatchdog real-time telemetry (memory, airgap, database, AI, storage)
- ProductionReadinessAuditor full certification across all 46 specification sections
- Cryptographic SHA-256 and HMAC-SHA256 production certificate signing
- REST API endpoints (/api/v1/system/watchdog/status, /api/v1/system/production-certificate)
- ProductionReleaseBuilder release manifest verification
"""

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from apps.processing.server import app
from core.orchestrator.production_readiness_audit import ProductionReadinessAuditor
from core.orchestrator.system_watchdog import SystemWatchdog
from scripts.build_production_release import ProductionReleaseBuilder


@pytest.fixture
def watchdog():
    return SystemWatchdog()


@pytest.fixture
def auditor():
    return ProductionReadinessAuditor()


@pytest.fixture
def client():
    return TestClient(app)


def test_system_watchdog_snapshot_metrics(watchdog):
    """Verifies that the live watchdog snapshot reports HEALTHY status across all subsystems."""
    snapshot = watchdog.get_watchdog_snapshot()

    assert snapshot.overall_health == "HEALTHY", f"Expected HEALTHY, got {snapshot.overall_health} (warnings: {snapshot.warnings})"
    assert snapshot.is_airgapped is True
    assert snapshot.memory_healthy is True
    assert snapshot.storage_healthy is True
    assert snapshot.database_healthy is True
    assert snapshot.ai_runtime_healthy is True
    assert snapshot.audit_trail_healthy is True
    assert len(snapshot.metrics) == 6

    # Verify individual metric properties
    metric_map = {m.name: m for m in snapshot.metrics}
    assert metric_map["memory_rss"].value < 4000.0
    assert metric_map["airgap_isolation"].value is True
    assert metric_map["database_integrity"].value is True
    assert metric_map["ai_runtime_readiness"].value >= 0.0


def test_production_readiness_all_46_sections(auditor):
    """Verifies that all 46 Master Specification sections are implemented and verified."""
    sections = auditor.audit_all_sections()
    assert len(sections) == 46, f"Expected 46 sections, got {len(sections)}"

    unverified = [s for s in sections if not s.verified]
    assert len(unverified) == 0, f"Unverified sections: {[(s.section_number, s.title, s.target_artifact) for s in unverified]}"


def test_production_certificate_cryptographic_signatures(auditor, tmp_path):
    """Verifies production certificate generation, cryptographic signatures, and export."""
    cert = auditor.generate_production_certificate(authorized_by="CIL Enterprise Audit Commission")

    assert cert.certificate_id.startswith("CIL-CERT-")
    assert cert.total_sections_certified == 46
    assert cert.readiness_percentage == 100.0
    assert cert.airgap_verified is True
    assert cert.modular_swappability_verified is True
    assert cert.watchdog_health == "HEALTHY"

    # Verify cryptographic signature lengths
    assert len(cert.sha256_signature) == 64
    assert len(cert.hmac_integrity_digest) == 64

    # Test file export
    export_file = tmp_path / "TEST_PRODUCTION_CERTIFICATE.json"
    exported_path = auditor.export_certificate(output_path=export_file, cert=cert)
    assert exported_path.exists()

    with open(exported_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["certificate_id"] == cert.certificate_id
    assert len(data["sections"]) == 46


def test_production_release_builder(workspace_root):
    """Verifies that the production release builder compiles and validates the release manifest."""
    builder = ProductionReleaseBuilder(repo_root=workspace_root)
    summary = builder.prepare_release()

    assert summary["status"] == "SUCCESS"
    assert summary["total_artifacts"] >= 40

    is_valid = builder.verify_release()
    assert is_valid is True


def test_rest_api_watchdog_and_certificate_endpoints(client):
    """Verifies the Phase 42 REST endpoints via FastAPI TestClient."""
    # 1. GET /api/v1/system/watchdog/status
    watch_resp = client.get("/api/v1/system/watchdog/status")
    assert watch_resp.status_code == 200
    watch_data = watch_resp.json()
    assert watch_data["overall_health"] == "HEALTHY"
    assert watch_data["is_airgapped"] is True
    assert len(watch_data["metrics"]) == 6

    # 2. POST /api/v1/system/production-certificate
    cert_resp = client.post(
        "/api/v1/system/production-certificate",
        json={"authorized_by": "CIL Executive Director (IT & Telecom)"},
    )
    assert cert_resp.status_code == 200
    cert_data = cert_resp.json()
    assert cert_data["certificate_id"].startswith("CIL-CERT-")
    assert cert_data["readiness_percentage"] == 100.0
    assert cert_data["total_sections_certified"] == 46
    assert cert_data["airgap_verified"] is True
    assert "hmac_integrity_digest" in cert_data
