"""
Image Intelligence Integration Layer — Section 18 of Master Implementation Specification.

Bridges the core asset catalog, analyzer, and models with section planning
and deterministic layout selection.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from core.assets.models import (
    ImageAsset,
    ImageAssetAssignment,
    ImageLayoutType,
    ImageQualityGrade,
)
from core.assets.analyzer import ImageAssetAnalyzer
from core.assets.catalog import ImageAssetCatalog

from enum import Enum

# Aliases for Section 18 specifications
LayoutType = ImageLayoutType


class ImageTopic(str, Enum):
    MINING_OPERATIONS = "mining"
    SAFETY_FIRST = "safety"
    ENVIRONMENTAL_RECLAMATION = "sustainability"
    CSR_COMMUNITY = "csr"
    EXECUTIVE_LEADERSHIP = "governance"
    MACHINERY = "machinery"
    DISPATCH = "dispatch"
    GENERAL = "general"


class ImageSlotSpec(BaseModel):
    slot_id: str
    asset_id: str
    caption: Optional[str] = None
    width_percent: float
    alignment: str  # 'left', 'right', 'center'


class SectionImagePresentation(BaseModel):
    """Deterministic styling and positioning specification for section visuals."""
    layout_type: ImageLayoutType
    recommended_css_class: str
    slots: List[ImageSlotSpec]
    container_style: Dict[str, str] = Field(default_factory=dict)


class DeterministicLayoutEngine:
    """
    Decides actual visual layout geometry without exposing raw coordinates to the LLM.
    Enforces Section 18 rule:
    'The AI may recommend which image is relevant to a section.
     The deterministic layout engine decides actual placement.'
    """

    @classmethod
    def resolve_layout(
        cls,
        section_type: str,
        available_assets: List[ImageAsset],
        preferred_layout: Optional[ImageLayoutType] = None,
    ) -> SectionImagePresentation:
        if not available_assets:
            return SectionImagePresentation(
                layout_type=ImageLayoutType.SINGLE_HERO,
                recommended_css_class="layout-empty",
                slots=[],
            )

        # 1. Explicit preference if satisfies count
        if preferred_layout == ImageLayoutType.GRID_2X2 and len(available_assets) >= 4:
            return cls._build_grid_2x2(available_assets[:4])

        if preferred_layout == ImageLayoutType.TWO_COLUMN_TEXT_IMAGE:
            return cls._build_two_column(available_assets[0])

        if preferred_layout == ImageLayoutType.SINGLE_HERO:
            return cls._build_hero(available_assets[0])

        # 2. Heuristic selection based on section type
        st_lower = section_type.lower()
        if ("director" in st_lower or "leadership" in st_lower or "board" in st_lower) and len(available_assets) >= 4:
            return cls._build_grid_2x2(available_assets[:4])
        elif ("operational" in st_lower or "mining" in st_lower) and available_assets:
            return cls._build_two_column(available_assets[0])
        elif ("csr" in st_lower or "environment" in st_lower) and len(available_assets) >= 2:
            return cls._build_controlled_spacing(available_assets[:2])
        else:
            return cls._build_hero(available_assets[0])

    @staticmethod
    def _build_hero(asset: ImageAsset) -> SectionImagePresentation:
        return SectionImagePresentation(
            layout_type=ImageLayoutType.SINGLE_HERO,
            recommended_css_class="layout-hero-banner",
            slots=[
                ImageSlotSpec(
                    slot_id="hero_main",
                    asset_id=asset.asset_id,
                    caption=asset.caption or f"Site photograph: {asset.filename}",
                    width_percent=100.0,
                    alignment="center",
                )
            ],
            container_style={"margin": "16px 0", "borderRadius": "8px", "overflow": "hidden"},
        )

    @staticmethod
    def _build_two_column(asset: ImageAsset) -> SectionImagePresentation:
        return SectionImagePresentation(
            layout_type=ImageLayoutType.TWO_COLUMN_TEXT_IMAGE,
            recommended_css_class="layout-two-column",
            slots=[
                ImageSlotSpec(
                    slot_id="col_visual",
                    asset_id=asset.asset_id,
                    caption=asset.caption or asset.filename,
                    width_percent=45.0,
                    alignment="right",
                )
            ],
            container_style={"display": "flex", "gap": "20px", "alignItems": "flex-start"},
        )

    @staticmethod
    def _build_grid_2x2(assets: List[ImageAsset]) -> SectionImagePresentation:
        slots = [
            ImageSlotSpec(
                slot_id=f"grid_slot_{idx+1}",
                asset_id=a.asset_id,
                caption=a.caption or a.filename,
                width_percent=48.0,
                alignment="center",
            )
            for idx, a in enumerate(assets[:4])
        ]
        return SectionImagePresentation(
            layout_type=ImageLayoutType.GRID_2X2,
            recommended_css_class="layout-grid-2x2",
            slots=slots,
            container_style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "14px"},
        )

    @staticmethod
    def _build_controlled_spacing(assets: List[ImageAsset]) -> SectionImagePresentation:
        slots = [
            ImageSlotSpec(
                slot_id=f"spaced_slot_{idx+1}",
                asset_id=a.asset_id,
                caption=a.caption or a.filename,
                width_percent=48.0,
                alignment="center",
            )
            for idx, a in enumerate(assets[:2])
        ]
        return SectionImagePresentation(
            layout_type=ImageLayoutType.CONTROLLED_SPACING,
            recommended_css_class="layout-controlled-spacing",
            slots=slots,
            container_style={"display": "flex", "gap": "16px", "justifyContent": "space-between"},
        )


__all__ = [
    "ImageAsset",
    "ImageAssetAssignment",
    "ImageLayoutType",
    "ImageQualityGrade",
    "ImageAssetAnalyzer",
    "ImageAssetCatalog",
    "LayoutType",
    "ImageSlotSpec",
    "SectionImagePresentation",
    "DeterministicLayoutEngine",
    "ImageTopic",
]
