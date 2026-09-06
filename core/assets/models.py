"""
Image Intelligence Asset Models — Section 18 of Master Implementation Specification.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class ImageLayoutType(str, Enum):
    """Deterministic visual layout placement modes."""
    SINGLE_HERO = "single_hero"
    TWO_COLUMN_TEXT_IMAGE = "two_column"
    GRID_2X2 = "grid_2x2"
    WITH_CAPTION = "with_caption"
    CONTROLLED_SPACING = "controlled_spacing"


class ImageQualityGrade(str, Enum):
    """Assessment of suitability for publication-grade 300+ page corporate reports."""
    EXCELLENT = "excellent"  # High DPI, high res (e.g. >= 1500px, 300 DPI)
    ACCEPTABLE = "acceptable"  # Good enough for standard page column (>= 600px)
    LOW_RES = "low_res"  # Needs downscaling or thumbnail placement (< 400px)
    UNSUITABLE = "unsuitable"  # Tiny icon, placeholder or corrupt (< 150px)


class ImageAsset(BaseModel):
    """
    Cataloged visual artifact with complete technical, perceptual,
    and provenance metadata.
    """
    asset_id: str
    filename: str
    file_path: str
    format: str  # PNG, JPEG, WEBP, TIFF, etc.
    width: int
    height: int
    aspect_ratio: float
    file_size_bytes: int
    sha256_hash: str
    phash: Optional[str] = None  # 64-bit hexadecimal difference hash
    dpi: Optional[int] = None
    quality_grade: ImageQualityGrade = ImageQualityGrade.ACCEPTABLE
    is_duplicate: bool = False
    duplicate_of: Optional[str] = None  # Reference to original asset_id if duplicate
    caption: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    recommended_layout: ImageLayoutType = ImageLayoutType.TWO_COLUMN_TEXT_IMAGE
    provenance_id: Optional[str] = None
    source_document_id: Optional[str] = None
    page_number: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ImageAssetAssignment(BaseModel):
    """Association of an ImageAsset to a specific ReportSection with layout instructions."""
    section_id: str
    asset_id: str
    layout_type: ImageLayoutType
    caption: Optional[str] = None
    display_order: int = 1
    width_percentage: Optional[int] = Field(default=100, ge=10, le=100)
