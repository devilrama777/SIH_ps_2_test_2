"""
Sanitized Audit & Diagnostic Exporter.
Section 1.4, Section 24 & Section 25 of Master Implementation Specification.

Provides zero-leakage diagnostic and audit log exporting for air-gapped environments.
Masks credentials, private user filesystem paths, and sensitive tokens while
preserving cryptographic chain integrity proofs.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from core.security.audit_logger import AuditLogger
from core.security.models import AuditEventType, AuditLogEntry


class AuditVerificationResult(BaseModel):
    """Result of cryptographic Merkle/hash-chain audit ledger verification."""
    is_valid: bool
    total_entries: int
    genesis_hash: str
    latest_hash: Optional[str] = None
    tampered_entry_id: Optional[str] = None
    tampered_index: Optional[int] = None
    error_reason: Optional[str] = None


class SanitizedAuditExport(BaseModel):
    """Sanitized diagnostic bundle with cryptographic verification manifest."""
    export_id: str
    generated_at: str
    chain_valid: bool
    total_records: int
    manifest_sha256: str
    records: List[Dict[str, Any]] = Field(default_factory=list)


class SanitizedAuditExporter:
    """
    Sanitizes and exports audit trails for external diagnostic submission
    without exposing confidential CIL operational data or local filesystem paths.
    """

    PATH_PATTERN = re.compile(r"(?i)[a-z]:\\users\\[^\s\\/]+|/home/[^\s/]+", re.IGNORECASE)
    SECRET_PATTERN = re.compile(
        r"(?i)\b(bearer\s+token|bearer|api[_-]?key|password|secret|token|auth|key)\b[\s:=]+([^\s,;]+)"
    )

    def __init__(self, audit_logger: Optional[AuditLogger] = None) -> None:
        self.audit_logger = audit_logger or AuditLogger()

    def sanitize_text(self, text: str) -> str:
        """Masks private user paths and credentials from text strings."""
        if not text:
            return text
        # Redact private paths
        cleaned = self.PATH_PATTERN.sub("[REDACTED_USER_PATH]", text)
        # Redact secrets
        cleaned = self.SECRET_PATTERN.sub(r"\1: [REDACTED_SECRET]", cleaned)
        return cleaned

    def sanitize_dict(self, data: Any) -> Any:
        """Recursively sanitizes dictionary and list data structures."""
        if isinstance(data, dict):
            return {k: self.sanitize_dict(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.sanitize_dict(item) for item in data]
        elif isinstance(data, str):
            return self.sanitize_text(data)
        return data

    def verify_ledger(self) -> AuditVerificationResult:
        """
        Executes granular cryptographic audit chain verification, identifying
        any modified, injected, or removed log entries.
        """
        entries = self.audit_logger.list_logs(limit=100000)
        # list_logs returns reverse order (DESC), sort ASC for chain verification
        entries_asc = sorted(entries, key=lambda e: e.timestamp)

        expected_prev = AuditLogger.GENESIS_HASH
        latest_hash = None

        for idx, entry in enumerate(entries_asc):
            if entry.prev_hash != expected_prev:
                return AuditVerificationResult(
                    is_valid=False,
                    total_entries=len(entries_asc),
                    genesis_hash=AuditLogger.GENESIS_HASH,
                    tampered_entry_id=entry.log_id,
                    tampered_index=idx,
                    error_reason=f"Broken prev_hash link at entry {entry.log_id}",
                )

            # Recompute entry hash
            payload = f"{entry.log_id}|{entry.timestamp.isoformat()}|{entry.event_type.value}|{entry.user}|{entry.action}|{entry.resource_id or ''}|{entry.status}|{entry.prev_hash}"
            expected_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()

            if entry.entry_hash != expected_hash:
                return AuditVerificationResult(
                    is_valid=False,
                    total_entries=len(entries_asc),
                    genesis_hash=AuditLogger.GENESIS_HASH,
                    tampered_entry_id=entry.log_id,
                    tampered_index=idx,
                    error_reason=f"Content hash mismatch at entry {entry.log_id}",
                )

            expected_prev = entry.entry_hash
            latest_hash = entry.entry_hash

        return AuditVerificationResult(
            is_valid=True,
            total_entries=len(entries_asc),
            genesis_hash=AuditLogger.GENESIS_HASH,
            latest_hash=latest_hash,
        )

    def export_sanitized_logs(self, limit: int = 1000) -> SanitizedAuditExport:
        """
        Generates a sanitized audit export with SHA-256 integrity manifest.
        """
        verification = self.verify_ledger()
        raw_logs = self.audit_logger.list_logs(limit=limit)

        sanitized_records = []
        for r in raw_logs:
            record_dict = r.model_dump()
            record_dict["timestamp"] = r.timestamp.isoformat()
            record_dict["resource_id"] = self.sanitize_text(r.resource_id or "")
            record_dict["action"] = self.sanitize_text(r.action)
            record_dict["details"] = self.sanitize_dict(r.details)
            sanitized_records.append(record_dict)

        # Compute deterministic bundle manifest hash
        payload_bytes = json.dumps(sanitized_records, sort_keys=True).encode("utf-8")
        manifest_hash = hashlib.sha256(payload_bytes).hexdigest()
        export_id = f"aud_exp_{hashlib.sha256(str(datetime.utcnow()).encode()).hexdigest()[:10]}"

        return SanitizedAuditExport(
            export_id=export_id,
            generated_at=datetime.utcnow().isoformat(),
            chain_valid=verification.is_valid,
            total_records=len(sanitized_records),
            manifest_sha256=manifest_hash,
            records=sanitized_records,
        )
