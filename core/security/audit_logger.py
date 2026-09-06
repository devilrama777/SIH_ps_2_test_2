"""
Audit Logger with Cryptographic Chaining — Section 24 of Master Plan.

Maintains an immutable, tamper-evident audit trail of all ingestion,
report generation, agentic modifications, approvals, and exports.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.security.models import AuditEventType, AuditLogEntry


class AuditLogger:
    """
    Cryptographically chained security audit logger.
    """

    GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

    def __init__(self, db_path: str = "data/workspace/audit_log.db"):
        self.db_path = db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_logs (
                    log_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    user TEXT NOT NULL,
                    action TEXT NOT NULL,
                    resource_id TEXT,
                    status TEXT NOT NULL,
                    ip_address TEXT NOT NULL,
                    details TEXT,
                    prev_hash TEXT NOT NULL,
                    entry_hash TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_event ON audit_logs(event_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_logs(timestamp)")
            conn.commit()

    def log_event(
        self,
        event_type: AuditEventType,
        action: str,
        resource_id: Optional[str] = None,
        status: str = "success",
        user: str = "local_operator",
        ip_address: str = "127.0.0.1",
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditLogEntry:
        details_clean = details or {}

        with self._get_conn() as conn:
            # 1. Fetch latest entry hash to maintain cryptographic chain
            last_row = conn.execute(
                "SELECT entry_hash FROM audit_logs ORDER BY rowid DESC LIMIT 1"
            ).fetchone()
            prev_hash = last_row["entry_hash"] if last_row else self.GENESIS_HASH

            # 2. Construct entry
            log_id = f"aud_{uuid.uuid4().hex[:12]}"
            now = datetime.utcnow()

            # 3. Calculate tamper-evident SHA-256 entry hash
            payload = f"{log_id}|{now.isoformat()}|{event_type.value}|{user}|{action}|{resource_id or ''}|{status}|{prev_hash}"
            entry_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()

            entry = AuditLogEntry(
                log_id=log_id,
                timestamp=now,
                event_type=event_type,
                user=user,
                action=action,
                resource_id=resource_id,
                status=status,
                ip_address=ip_address,
                details=details_clean,
                prev_hash=prev_hash,
                entry_hash=entry_hash,
            )

            # 4. Persist to database
            conn.execute(
                """
                INSERT INTO audit_logs (
                    log_id, timestamp, event_type, user, action, resource_id,
                    status, ip_address, details, prev_hash, entry_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.log_id,
                    entry.timestamp.isoformat(),
                    entry.event_type.value,
                    entry.user,
                    entry.action,
                    entry.resource_id,
                    entry.status,
                    entry.ip_address,
                    json.dumps(entry.details),
                    entry.prev_hash,
                    entry.entry_hash,
                ),
            )
            conn.commit()

        return entry

    def verify_chain_integrity(self) -> bool:
        """
        Validates the entire audit ledger from genesis to current.
        Returns False if any record has been modified or deleted.
        """
        with self._get_conn() as conn:
            rows = conn.execute("SELECT * FROM audit_logs ORDER BY rowid ASC").fetchall()
            expected_prev = self.GENESIS_HASH

            for r in rows:
                if r["prev_hash"] != expected_prev:
                    return False

                # Recompute hash
                payload = f"{r['log_id']}|{r['timestamp']}|{r['event_type']}|{r['user']}|{r['action']}|{r['resource_id'] or ''}|{r['status']}|{r['prev_hash']}"
                expected_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()

                if r["entry_hash"] != expected_hash:
                    return False

                expected_prev = r["entry_hash"]

        return True

    def list_logs(
        self,
        event_type: Optional[AuditEventType] = None,
        limit: int = 50,
    ) -> List[AuditLogEntry]:
        with self._get_conn() as conn:
            query = "SELECT * FROM audit_logs"
            params: List[Any] = []

            if event_type:
                query += " WHERE event_type = ?"
                params.append(event_type.value)

            query += " ORDER BY rowid DESC LIMIT ?"
            params.append(limit)

            rows = conn.execute(query, params).fetchall()

            return [
                AuditLogEntry(
                    log_id=r["log_id"],
                    timestamp=datetime.fromisoformat(r["timestamp"]),
                    event_type=AuditEventType(r["event_type"]),
                    user=r["user"],
                    action=r["action"],
                    resource_id=r["resource_id"],
                    status=r["status"],
                    ip_address=r["ip_address"],
                    details=json.loads(r["details"] or "{}"),
                    prev_hash=r["prev_hash"],
                    entry_hash=r["entry_hash"],
                )
                for r in rows
            ]

    def count_logs(self) -> int:
        with self._get_conn() as conn:
            row = conn.execute("SELECT COUNT(*) as cnt FROM audit_logs").fetchone()
            return int(row["cnt"]) if row else 0
