"""
Unit tests for Future Enterprise Connectors and AuthorizedReportUploader.
Phase 13 (Section 4.2 & Section 46).
"""
import json
import uuid
from pathlib import Path

import pytest

from core.connectors.future.cil_api import CILApiConnector
from core.connectors.future.network_share import NetworkShareConnector
from core.connectors.future.sharepoint import SharePointConnector
from core.connectors.upload import AuthorizedReportUploader
from core.orchestrator.models import PipelineConfig, PipelineSession, PipelineStage
from core.security.audit_logger import AuditLogger


def test_network_share_connector(tmp_path: Path):
    share_dir = tmp_path / "mock_smb_share"
    share_dir.mkdir()
    sample_doc = share_dir / "Production_Record.csv"
    sample_doc.write_text("Date,MT\n2024-03-31,120.5\n", encoding="utf-8")

    connector = NetworkShareConnector(share_path=str(share_dir))
    health = connector.health_check()
    assert health.healthy is True
    assert health.connector_type == "network_share"

    items = connector.discover()
    assert len(items) == 1
    assert items[0].filename == "Production_Record.csv"

    content = connector.fetch_document(items[0].source_id)
    assert b"2024-03-31" in content


def test_sharepoint_connector(tmp_path: Path):
    staging_dir = tmp_path / "sp_staging"
    staging_dir.mkdir()
    doc = staging_dir / "Board_Minutes_Q4.docx"
    doc.write_bytes(b"PK\x03\x04mock_docx_bytes")

    connector = SharePointConnector(local_staging_dir=staging_dir)
    health = connector.health_check()
    assert health.healthy is True
    assert health.connector_type == "sharepoint_dms"

    sources = connector.list_sources()
    assert len(sources) == 1
    assert sources[0].filename == "Board_Minutes_Q4.docx"


def test_cil_api_connector(tmp_path: Path):
    cache_dir = tmp_path / "erp_cache"
    cache_dir.mkdir()
    payload = cache_dir / "FY24_offtake.json"
    payload.write_text(json.dumps({"month": "March", "dispatch_mt": 14.2}), encoding="utf-8")

    connector = CILApiConnector(local_payload_cache=cache_dir)
    health = connector.health_check()
    assert health.healthy is True
    assert health.connector_type == "cil_sap_erp_api"

    sources = connector.discover()
    assert len(sources) == 1
    assert sources[0].filename == "FY24_offtake.json"


def test_authorized_report_uploader(tmp_path: Path):
    audit_db = tmp_path / "audit.db"
    audit_logger = AuditLogger(db_path=str(audit_db))
    uploader = AuthorizedReportUploader(
        audit_logger=audit_logger,
        default_destination_dir=tmp_path / "dest",
    )

    pdf_file = tmp_path / "report_source.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 Mock corporate annual report")

    session = PipelineSession(
        session_id=str(uuid.uuid4()),
        config=PipelineConfig(
            session_id="test_sess",
            source_folder=str(tmp_path),
            subsidiary="Central Coalfields Limited",
            reporting_year="2024-25",
        ),
        current_stage=PipelineStage.COMPLETED,
        progress_percent=100.0,
        created_at="2026-09-06T12:00:00",
        updated_at="2026-09-06T12:05:00",
        report_id="rep_12345",
        pdf_path=str(pdf_file),
        is_approved=False,
    )

    # 1. Blocked when unapproved
    with pytest.raises(PermissionError) as exc_info:
        uploader.upload_report(session)
    assert "Authorized upload blocked" in str(exc_info.value)

    # 2. Succeeds with approver
    res = uploader.upload_report(
        session=session,
        approver_name="Sri Director (Technical)",
        approval_notes="Approved for statutory submission.",
    )
    assert res["success"] is True
    assert Path(res["pdf_destination"]).exists()
    assert Path(res["manifest_destination"]).exists()
    assert session.is_uploaded is True

    # 3. Audit trail verification
    trail = audit_logger.list_logs()
    assert len(trail) == 1
    assert trail[0].action == "authorized_corporate_upload"
    assert audit_logger.verify_chain_integrity() is True
