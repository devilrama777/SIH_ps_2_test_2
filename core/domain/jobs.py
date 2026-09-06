"""
Processing Job System Model — Section 27 of Master Implementation Specification.

Large report operations execute via asynchronous, resumable, and observable background jobs.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class JobStage(str, Enum):
    DISCOVERY = "DISCOVERY"
    INGESTION = "INGESTION"
    OCR = "OCR"
    EXTRACTION = "EXTRACTION"
    NORMALIZATION = "NORMALIZATION"
    INDEXING = "INDEXING"
    PLANNING = "PLANNING"
    GENERATION = "GENERATION"
    VALIDATION = "VALIDATION"
    COMPOSITION = "COMPOSITION"
    RENDERING = "RENDERING"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"


class JobStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"


class JobError(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    stage: JobStage
    message: str
    item_id: Optional[str] = None
    recoverable: bool = True
    traceback: Optional[str] = None


class ProcessingJob(BaseModel):
    """Observable background processing job."""
    job_id: str
    job_type: str = Field(..., description="e.g., 'ingest_folder', 'generate_report', 'revalidate_section'")
    status: JobStatus = JobStatus.PENDING
    progress: float = Field(default=0.0, ge=0.0, le=100.0, description="Completion percentage 0.0-100.0")
    current_stage: JobStage = JobStage.DISCOVERY
    total_items: int = 0
    processed_items: int = 0
    failed_items: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    errors: List[JobError] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
