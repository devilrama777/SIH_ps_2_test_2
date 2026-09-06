"""
Unit and Integration Tests for Phase 35: Cryptographic Tamper-Evident Audit & Sanitized Diagnostic Export.
Section 1.4, Section 24 & Section 25 of Master Implementation Specification.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from apps.processing.server import app
from core.security.audit_logger import AuditLogger
from core.security.models import AuditEventType
from core.security.sanitized_export import (
    AuditVerificationResult,
    SanitizedAuditExport,
    SanitizedAuditExporter,
)

client = TestClient(app)


def test_audit_chain_validity(tmp_path: Path):
    db_path = str(tmp_path / "valid_audit.db")
    logger = AuditLogger(db_path=db_path)

    logger.log_event(AuditEventType.INGESTION, "ingest_file", "doc_01")
    logger.log_event(AuditEventType.REPORT_CREATED, "create_report", "rep_01")
    logger.log_event(AuditEventType.EXPORT_PDF, "export_pdf", "rep_01.pdf")

    exporter = SanitizedAuditExporter(audit_logger=logger)
    res = exporter.verify_ledger()
    assert res.is_valid is True
    assert res.total_entries == 3
    assert res.latest_hash is not None


def test_tamper_detection(tmp_path: Path):
    db_path = str(tmp_path / "tampered_audit.db")
    logger = AuditLogger(db_path=db_path)

    e1 = logger.log_event(AuditEventType.INGESTION, "ingest_file", "doc_01")
    e2 = logger.log_event(AuditEventType.REPORT_CREATED, "create_report", "rep_01")
    e3 = logger.log_event(AuditEventType.EXPORT_PDF, "export_pdf", "rep_01.pdf")

    # Maliciously modify the database record in e2 without updating hashes
    conn = sqlite3.connect(db_path)
    conn.execute("UPDATE audit_logs SET action = 'tampered_action' WHERE log_id = ?", (e2.log_id,))
    conn.commit()
    conn.close()

    exporter = SanitizedAuditExporter(audit_logger=logger)
    res = exporter.verify_ledger()
    assert res.is_valid is False
    assert res.tampered_entry_id == e2.log_id
    assert "Content hash mismatch" in res.error_reason


def test_sanitization_redaction():
    exporter = SanitizedAuditExporter()
    raw_text = r"File saved to C:\Users\dt\Confidential\production.xlsx with bearer token: secret_api_key_123"
    sanitized = exporter.sanitize_text(raw_text)

    assert r"C:\Users\dt" not in sanitized
    assert "[REDACTED_USER_PATH]" in sanitized
    assert "secret_api_key_123" not in sanitized
    assert "[REDACTED_SECRET]" in sanitized


def test_sanitized_export_manifest(tmp_path: Path):
    db_path = str(tmp_path / "export_audit.db")
    logger = AuditLogger(db_path=db_path)

    logger.log_event(
        AuditEventType.INGESTION,
        r"Ingested file from C:\Users\dt\Desktop\production.xlsx",
        resource_id=r"C:\Users\dt\report.pdf",
        details={"path": r"C:\Users\dt\data.csv", "api_token": "secret_key_889"},
    )

    exporter = SanitizedAuditExporter(audit_logger=logger)
    bundle: SanitizedAuditExport = exporter.export_sanitized_logs()

    assert bundle.chain_valid is True
    assert bundle.total_records == 1
    assert len(bundle.manifest_sha256) == 64

    rec = bundle.records[0]
    assert r"C:\Users\dt" not in rec["action"]
    assert r"C:\Users\dt" not in rec["resource_id"]
    assert r"C:\Users\dt" not in str(rec["details"])


def test_audit_rest_api():
    verify_resp = client.get("/api/v1/audit/verify")
    assert verify_resp.status_code == 200
    data = verify_resp.json()
    assert "is_valid" in data
    assert "total_entries" in data

    export_resp = client.post("/api/v1/audit/export/sanitized?limit=10")
    assert export_resp.status_code == 200
    exp_data = export_resp.json()
    assert "manifest_sha256" in exp_data
    assert "records" in exp_data
