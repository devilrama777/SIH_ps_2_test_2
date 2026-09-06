"""
Enterprise Report Pipeline Models.
Phase 13 (Section 33 & 46).
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PipelineStage(str, Enum):
    INITIALIZING = "initializing"
    DISCOVERY = "discovery"
    EXTRACTION = "extraction"
    INDEXING = "indexing"
    PLANNING = "planning"
    GENERATION = "generation"
    VALIDATION = "validation"
    ASSET_INTELLIGENCE = "asset_intelligence"
    PDF_RENDERING = "pdf_rendering"
    COMPLETED = "completed"
    FAILED = "failed"


class PipelineConfig(BaseModel):
    session_id: str
    source_folder: str
    subsidiary: str = "Central Coalfields Limited"
    reporting_year: str = "2024-25"
    reporting_period: str = "Annual"
    template_style: str = "classic"  # "classic" or "modern"
    reference_report_path: Optional[str] = None
    auto_approve: bool = False


class PipelineLogEntry(BaseModel):
    timestamp: str
    stage: PipelineStage
    message: str
    level: str = "INFO"


class PipelineSession(BaseModel):
    session_id: str
    config: PipelineConfig
    current_stage: PipelineStage = PipelineStage.INITIALIZING
    progress_percent: float = 0.0
    created_at: str
    updated_at: str
    report_id: Optional[str] = None
    pdf_path: Optional[str] = None
    is_approved: bool = False
    approved_by: Optional[str] = None
    approval_timestamp: Optional[str] = None
    approval_notes: Optional[str] = None
    is_uploaded: bool = False
    upload_destination: Optional[str] = None
    logs: List[PipelineLogEntry] = Field(default_factory=list)
    metrics: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
