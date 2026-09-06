import sqlite3
import pytest
from core.security.models import AuditEventType
from core.security.audit_logger import AuditLogger


def test_audit_logger_genesis_and_chaining(tmp_path):
    db_file = str(tmp_path / "test_audit.db")
    logger = AuditLogger(db_path=db_file)

    # Initial chain with 0 logs should be valid
    assert logger.verify_chain_integrity() is True
    assert logger.count_logs() == 0

    # Log 3 distinct events
    e1 = logger.log_event(
        event_type=AuditEventType.INGESTION,
        action="ingest_pdf",
        resource_id="doc_ccl_01",
        details={"pages": 12},
    )
    assert e1.prev_hash == AuditLogger.GENESIS_HASH
    assert len(e1.entry_hash) == 64

    e2 = logger.log_event(
        event_type=AuditEventType.REPORT_CREATED,
        action="generate_report",
        resource_id="rep_2025_01",
        details={"title": "CCL Annual Report"},
    )
    assert e2.prev_hash == e1.entry_hash

    e3 = logger.log_event(
        event_type=AuditEventType.EXPORT_PDF,
        action="export_pdf",
        resource_id="rep_2025_01",
        details={"template": "modern"},
    )
    assert e3.prev_hash == e2.entry_hash

    assert logger.count_logs() == 3
    assert logger.verify_chain_integrity() is True

    # Check listing and filtering
    all_logs = logger.list_logs()
    assert len(all_logs) == 3
    # Most recent first
    assert all_logs[0].log_id == e3.log_id

    pdf_logs = logger.list_logs(event_type=AuditEventType.EXPORT_PDF)
    assert len(pdf_logs) == 1
    assert pdf_logs[0].action == "export_pdf"


def test_tamper_detection(tmp_path):
    db_file = str(tmp_path / "tamper_test.db")
    logger = AuditLogger(db_path=db_file)

    logger.log_event(AuditEventType.INGESTION, "doc_1")
    logger.log_event(AuditEventType.REPORT_CREATED, "rep_1")
    logger.log_event(AuditEventType.EXPORT_PDF, "rep_1")

    assert logger.verify_chain_integrity() is True

    # Tamper with middle row in SQLite directly
    conn = sqlite3.connect(db_file)
    conn.execute("UPDATE audit_logs SET action = 'tampered_action' WHERE event_type = 'report_created'")
    conn.commit()
    conn.close()

    # Integrity verification must catch the tamper
    assert logger.verify_chain_integrity() is False
