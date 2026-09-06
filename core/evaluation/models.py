"""
Evaluation & Regression Quality Domain Models — Section 30 & Section 32 of Master Plan.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ReportQualityMetrics(BaseModel):
    """
    Measurable quality checks defined in Section 32 of the Master Implementation Plan.
    """
    source_coverage: float = Field(..., description="Proportion of citations resolving to valid primary sources (0.0 to 1.0)")
    provenance_coverage: float = Field(..., description="Proportion of substantive sections/paragraphs with valid provenance (0.0 to 1.0)")
    unsupported_claim_rate: float = Field(..., description="Rate of numerical claims lacking ground-truth backing (0.0 to 1.0)")
    numerical_error_rate: float = Field(..., description="Rate of arithmetic or balance anomalies (0.0 to 1.0)")
    total_claims_evaluated: int = 0
    total_citations_resolved: int = 0
    missing_evidence_count: int = 0
    passed_quality_threshold: bool = True
    details: Dict[str, Any] = Field(default_factory=dict)


class GoldenRegressionResult(BaseModel):
    """
    End-to-end regression evaluation result across golden reference dataset.
    """
    run_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    total_golden_fixtures: int
    ingested_documents: int
    generated_sections: int
    metrics: ReportQualityMetrics
    validation_passed: bool
    audit_chain_verified: bool
    pdf_generated: bool
    pdf_path: Optional[str] = None
    execution_duration_sec: float
