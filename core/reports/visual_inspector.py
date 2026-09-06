"""
Interactive Source Inspector & Coordinate Preview Engine.
Section 1.4, Section 11 & Section 15 of Master Implementation Specification.

Renders interactive SVG/HTML coordinate overlays for spatial bounding box
verification and spreadsheet cell provenance inspection on local desktop client.
"""
from __future__ import annotations

import html
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from core.domain.documents import BoundingBox
from core.domain.evidence import ProvenanceRecord, SpreadsheetCoordinate


class VisualHighlight(BaseModel):
    """Visual highlight region on a document page or sheet."""
    highlight_id: str
    label: str
    bbox: Optional[BoundingBox] = None
    spreadsheet_coord: Optional[SpreadsheetCoordinate] = None
    snippet: str = ""
    color: str = "#FF4500"  # Orange-red highlight standard
    confidence: Optional[float] = None


class VisualInspectorReport(BaseModel):
    """Rendered visual coordinate inspection package."""
    source_reference: str
    page_number: Optional[int] = None
    width: float = 800.0
    height: float = 1100.0
    highlights: List[VisualHighlight] = Field(default_factory=list)
    svg_overlay: str = ""
    html_preview: str = ""


class VisualSourceInspector:
    """
    Generates deterministic, zero-dependency SVG overlays and interactive
    HTML inspection widgets for desktop audit views.
    """

    def generate_svg_overlay(
        self,
        width: float,
        height: float,
        highlights: List[VisualHighlight],
    ) -> str:
        """
        Generates an SVG layer matching document page dimensions
        with semi-transparent bounding boxes and hover tooltips.
        """
        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {float(width)} {float(height)}" '
            f'width="100%" height="100%" style="position: absolute; top: 0; left: 0; pointer-events: none;">',
            '  <defs>',
            '    <style>',
            '      .prov-box { fill-opacity: 0.22; stroke-width: 2; pointer-events: auto; cursor: pointer; transition: all 0.2s ease; }',
            '      .prov-box:hover { fill-opacity: 0.45; stroke-width: 3.5; }',
            '      .prov-text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace; font-size: 11px; font-weight: 700; fill: #111; }',
            '    </style>',
            '  </defs>',
        ]

        for h in highlights:
            if not h.bbox:
                continue
            b = h.bbox
            x = b.x0
            y = b.y0
            w = max(1.0, b.x1 - b.x0)
            ht = max(1.0, b.y1 - b.y0)
            esc_label = html.escape(h.label)
            esc_snip = html.escape(h.snippet)
            conf_str = f" ({round(h.confidence * 100)}%)" if h.confidence is not None else ""

            svg_parts.append(
                f'  <g id="{html.escape(h.highlight_id)}">'
                f'    <rect class="prov-box" x="{x}" y="{y}" width="{w}" height="{ht}" '
                f'stroke="{h.color}" fill="{h.color}">'
                f'      <title>{esc_label}{conf_str}&#10;{esc_snip}</title>'
                f'    </rect>'
                f'    <rect x="{x}" y="{max(0.0, y - 16)}" width="{min(w, 180.0)}" height="16" fill="{h.color}" rx="3"/>'
                f'    <text class="prov-text" x="{x + 4}" y="{max(12.0, y - 4)}" fill="#ffffff">{esc_label}</text>'
                f'  </g>'
            )

        svg_parts.append('</svg>')
        return "\n".join(svg_parts)

    def render_spreadsheet_grid(self, coord: SpreadsheetCoordinate) -> str:
        """
        Renders a lightweight HTML table preview demonstrating cell coordinate
        positioning for spreadsheet evidence.
        """
        sheet = html.escape(coord.sheet_name)
        cell = html.escape(coord.cell or "Unknown Cell")
        val = html.escape(str(coord.formatted_value or coord.raw_value or ""))
        row_idx = coord.row or 1
        col_idx = coord.column or 1

        rows_html = []
        for r in range(max(1, row_idx - 2), row_idx + 3):
            cols_html = [f'<td style="background: #f0f0f0; font-weight: bold; padding: 4px 8px; border: 1px solid #ccc;">{r}</td>']
            for c in range(max(1, col_idx - 2), col_idx + 3):
                is_target = (r == row_idx and c == col_idx)
                bg = "#FFE4B5" if is_target else "#ffffff"
                border = "2px solid #FF4500" if is_target else "1px solid #e0e0e0"
                content = val if is_target else ""
                cols_html.append(
                    f'<td style="background: {bg}; border: {border}; padding: 4px 8px; min-width: 70px; font-family: monospace;">{content}</td>'
                )
            rows_html.append(f'<tr>{"".join(cols_html)}</tr>')

        return (
            f'<div class="spreadsheet-inspector" style="border: 1px solid #ccc; padding: 8px; border-radius: 4px; background: #fafafa;">'
            f'  <div style="font-weight: 600; margin-bottom: 6px;">Workbook: {html.escape(coord.workbook_name)} | Sheet: {sheet} | Target Cell: <span style="color: #FF4500;">{cell}</span></div>'
            f'  <table style="border-collapse: collapse; font-size: 12px;">'
            f'    {"".join(rows_html)}'
            f'  </table>'
            f'</div>'
        )

    def create_inspector_from_provenance(
        self,
        record: ProvenanceRecord,
        excerpt: Optional[str] = None,
        page_width: float = 800.0,
        page_height: float = 1100.0,
    ) -> VisualInspectorReport:
        """
        Builds a complete inspection package from a provenance record.
        """
        highlights: List[VisualHighlight] = []

        if record.bbox:
            highlights.append(
                VisualHighlight(
                    highlight_id=f"hl_{record.provenance_id}",
                    label=record.element_id or "Evidence Region",
                    bbox=record.bbox,
                    snippet=excerpt or record.metadata.get("text_snippet", ""),
                    confidence=record.confidence,
                )
            )

        svg = ""
        html_preview = ""
        if highlights:
            svg = self.generate_svg_overlay(page_width, page_height, highlights)
            html_preview = (
                f'<div class="inspector-container" style="position: relative; width: {page_width}px; height: {page_height}px; border: 1px solid #ddd; background: #fdfdfd;">'
                f'  <div style="padding: 12px; color: #555;">Document: {html.escape(record.source_reference)} (Page {record.page_number or 1})</div>'
                f'  {svg}'
                f'</div>'
            )
        elif record.spreadsheet_coord:
            html_preview = self.render_spreadsheet_grid(record.spreadsheet_coord)

        return VisualInspectorReport(
            source_reference=record.source_reference,
            page_number=record.page_number,
            width=page_width,
            height=page_height,
            highlights=highlights,
            svg_overlay=svg,
            html_preview=html_preview,
        )
