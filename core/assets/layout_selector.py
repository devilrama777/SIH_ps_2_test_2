"""
Deterministic Layout Selector — Section 18 of Master Implementation Specification.

Decides exact visual layout structure (single hero, two-column, 2x2 grid,
captioned diagram, or controlled spacing) without LLM guesswork.
"""
from __future__ import annotations

from typing import Any, Dict, List
from core.assets.models import ImageAsset, ImageLayoutType


class DeterministicLayoutSelector:
    """
    Selects presentation layout for section imagery based on count,
    aspect ratios, and image resolutions.
    """

    @staticmethod
    def select_layout(assets: List[ImageAsset]) -> ImageLayoutType:
        if not assets:
            return ImageLayoutType.WITH_CAPTION

        count = len(assets)

        # Case 1: Exactly 4 images -> Candidate for 2x2 grid
        if count == 4:
            return ImageLayoutType.GRID_2X2

        # Case 2: Single image
        if count == 1:
            img = assets[0]
            # Panoramic / widescreen hero banner
            if img.aspect_ratio >= 1.6 and img.width >= 1000:
                return ImageLayoutType.SINGLE_HERO
            # Tall portrait image looks best alongside narrative text
            if img.aspect_ratio <= 0.85:
                return ImageLayoutType.TWO_COLUMN_TEXT_IMAGE
            # Standard presentation
            return ImageLayoutType.WITH_CAPTION

        # Case 3: Two images
        if count == 2:
            # If both are portrait, place side-by-side or two-column
            if all(a.aspect_ratio <= 1.0 for a in assets):
                return ImageLayoutType.TWO_COLUMN_TEXT_IMAGE
            return ImageLayoutType.CONTROLLED_SPACING

        # Case 4: Multiple images (> 2)
        return ImageLayoutType.CONTROLLED_SPACING

    @staticmethod
    def generate_html_container(assets: List[ImageAsset], layout: ImageLayoutType) -> str:
        """
        Generates semantic HTML/CSS markup for the selected visual layout.
        Used by the PDF report renderer in Phase 8.
        """
        if not assets:
            return ""

        if layout == ImageLayoutType.SINGLE_HERO:
            img = assets[0]
            return (
                f'<figure class="report-image-hero">\n'
                f'  <img src="{img.file_path}" alt="{img.caption or ""}" style="width:100%; max-height:420px; object-fit:cover; border-radius:6px;" />\n'
                f'  {f"<figcaption>{img.caption}</figcaption>" if img.caption else ""}\n'
                f'</figure>'
            )

        if layout == ImageLayoutType.GRID_2X2:
            items = []
            for img in assets[:4]:
                items.append(
                    f'  <div class="grid-item">\n'
                    f'    <img src="{img.file_path}" alt="{img.caption or ""}" style="width:100%; height:180px; object-fit:cover; border-radius:4px;" />\n'
                    f'    {f"<p class=\"caption\">{img.caption}</p>" if img.caption else ""}\n'
                    f'  </div>'
                )
            return (
                f'<div class="report-image-grid-2x2" style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin:16px 0;">\n'
                + "\n".join(items)
                + "\n</div>"
            )

        if layout == ImageLayoutType.TWO_COLUMN_TEXT_IMAGE:
            img = assets[0]
            return (
                f'<div class="report-two-col-asset" style="float:right; width:45%; margin:0 0 16px 20px;">\n'
                f'  <img src="{img.file_path}" alt="{img.caption or ""}" style="width:100%; border-radius:4px;" />\n'
                f'  {f"<figcaption style=\"font-size:0.8rem; color:#666; margin-top:4px;\">{img.caption}</figcaption>" if img.caption else ""}\n'
                f'</div>'
            )

        # Default / WITH_CAPTION / CONTROLLED_SPACING
        html_parts = []
        for img in assets:
            html_parts.append(
                f'<figure class="report-image-standard" style="margin:16px auto; max-width:85%; text-align:center;">\n'
                f'  <img src="{img.file_path}" alt="{img.caption or ""}" style="max-width:100%; max-height:360px; border-radius:4px;" />\n'
                f'  {f"<figcaption style=\"font-size:0.82rem; color:#555; margin-top:6px;\">{img.caption}</figcaption>" if img.caption else ""}\n'
                f'</figure>'
            )
        return "\n".join(html_parts)
