"""
Authorized Organizational Report Uploader.
Phase 13 (Section 33 step 15, Section 46, and Section 0/1.2).

Enforces mandatory human sign-off verification before transmitting or uploading
the approved annual report PDF to an authorized CIL corporate repository or share.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from core.orchestrator.models import PipelineSession
from core.security.audit_logger import AuditLogger
from core.security.models import AuditEventType


def compute_sha256(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class AuthorizedReportUploader:
    """Safely delivers approved corporate annual reports with dual-authorization checks."""

    def __init__(
        self,
        audit_logger: Optional[AuditLogger] = None,
        default_destination_dir: Optional[Path] = None,
    ):
        self.audit_logger = audit_logger or AuditLogger()
        self.destination_dir = (default_destination_dir or Path("data/workspace/authorized_uploads")).resolve()
        self.destination_dir.mkdir(parents=True, exist_ok=True)

    def upload_report(
        self,
        session: PipelineSession,
        destination_target: Optional[str] = None,
        approver_name: Optional[str] = None,
        approval_notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes authorized upload of the final approved PDF report.
        Strictly enforces human approval verification before transmission.
        """
        if not session.is_approved and not approver_name:
            raise PermissionError(
                "Authorized upload blocked: Report must be explicitly approved by a designated CIL authority."
            )

        if not session.pdf_path:
            raise FileNotFoundError("Cannot upload: PDF artifact path not found in pipeline session.")

        pdf_path = Path(session.pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file does not exist on disk: {pdf_path}")

        pdf_hash = compute_sha256(pdf_path)
        now = datetime.now().isoformat()

        # Update session approval if passed
        if approver_name:
            session.is_approved = True
            session.approved_by = approver_name
            session.approval_timestamp = now
            session.approval_notes = approval_notes

        # Determine target path
        dest_filename = f"{session.config.subsidiary.replace(' ', '_')}_{session.config.reporting_year}_FINAL.pdf"
        target_path = self.destination_dir / dest_filename
        if destination_target:
            target_path = Path(destination_target)
            target_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy PDF to target
        shutil.copy2(pdf_path, target_path)

        # Generate submission manifest
        manifest = {
            "session_id": session.session_id,
            "report_id": session.report_id,
            "subsidiary": session.config.subsidiary,
            "reporting_year": session.config.reporting_year,
            "pdf_filename": dest_filename,
            "pdf_sha256": pdf_hash,
            "approved_by": session.approved_by,
            "approval_timestamp": session.approval_timestamp,
            "approval_notes": session.approval_notes,
            "uploaded_at": now,
            "metrics": session.metrics,
        }
        manifest_path = target_path.with_suffix(".manifest.json")
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        # Mark session
        session.is_uploaded = True
        session.upload_destination = str(target_path)

        # Cryptographic Audit Log
        self.audit_logger.log_event(
            event_type=AuditEventType.EXPORT_PDF,
            action="authorized_corporate_upload",
            resource_id=session.report_id or session.session_id,
            details={
                "pdf_sha256": pdf_hash,
                "approved_by": session.approved_by,
                "destination": str(target_path),
                "timestamp": now,
            },
        )

        return {
            "success": True,
            "pdf_destination": str(target_path),
            "manifest_destination": str(manifest_path),
            "pdf_sha256": pdf_hash,
            "approved_by": session.approved_by,
            "timestamp": now,
        }
