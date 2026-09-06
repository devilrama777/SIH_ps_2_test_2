"""
Security Domain Models — Section 24 of Master Implementation Specification.
"""
from __future__ import annotations

from enum import Enum
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class AuditEventType(str, Enum):
    INGESTION = "ingestion"
    REPORT_CREATED = "report_created"
    AGENT_EDIT_PROPOSED = "agent_edit_proposed"
    AGENT_EDIT_ACCEPTED = "agent_edit_accepted"
    AGENT_EDIT_REJECTED = "agent_edit_rejected"
    AGENT_ACTION = "agent_action"
    TOOL_INVOCATION = "tool_invocation"
    EXPORT_PDF = "export_pdf"
    EXPORT_HTML = "export_html"
    CONFIG_CHANGE = "config_change"
    AUTHENTICATION = "authentication"
    NETWORK_VIOLATION = "network_violation"


class AuditLogEntry(BaseModel):
    """
    Immutable, cryptographically-chained security audit record.
    """
    log_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: AuditEventType
    user: str = "local_operator"
    action: str
    resource_id: Optional[str] = None
    status: str = "success"  # 'success', 'failure', 'blocked'
    ip_address: str = "127.0.0.1"
    details: Dict[str, Any] = Field(default_factory=dict)
    prev_hash: Optional[str] = None
    entry_hash: str = ""


class SecurityStatus(BaseModel):
    """System-wide security posture and compliance status."""
    air_gap_enforced: bool = True
    no_cloud_ai_calls: bool = True
    vault_status: str = "secure_encrypted_vault"
    audit_chain_valid: bool = True
    total_audit_logs: int = 0
    workspace_directory: str
    active_controls: list[str] = Field(default_factory=list)
