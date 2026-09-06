"""
Report HTML Builder — Sections 19 & 20 of Master Implementation Specification.

Compiles intermediate Report JSON models into complete, styled HTML documents
supporting Template A (Classic) and Template B (Modern Corporate).
"""
from __future__ import annotations

import html
import re
from typing import Any, Dict, List, Optional

from core.assets.catalog import ImageAssetCatalog
from core.assets.layout_selector import DeterministicLayoutSelector
from core.domain.reports import Report, ReportSection
from core.reports.pdf.templates.classic import CLASSIC_CSS
from core.reports.pdf.templates.modern import MODERN_CSS


class ReportHtmlBuilder:
    """
    Transforms Report domain models into publication-ready HTML documents.
    """

    def __init__(self, asset_catalog: Optional[ImageAssetCatalog] = None):
        self.asset_catalog = asset_catalog

    def build_html(self, report: Report, template_name: str = "modern") -> str:
        css = MODERN_CSS if template_name.lower() == "modern" else CLASSIC_CSS

        # 1. Build Cover Page
        cover_html = self._build_cover_page(report, template_name)

        # 2. Build Table of Contents
        toc_html = self._build_toc(report.sections)

        # 3. Build Sections Content
        sections_html = self._build_sections(report.sections)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{html.escape(report.title)}</title>
  <style>
{css}
  </style>
</head>
<body>
  {cover_html}

  <div class="page-break"></div>

  <div class="toc-container">
    <div class="toc-title">Table of Contents</div>
    {toc_html}
  </div>

  <div class="page-break"></div>

  <div class="report-body">
    {sections_html}
  </div>
</body>
</html>
"""

    def _build_cover_page(self, report: Report, template_name: str) -> str:
        safe_subsidiary = html.escape(report.subsidiary_name)
        safe_title = html.escape(report.title)
        safe_period = html.escape(report.reporting_period)

        return f"""
  <div class="cover-page">
    <div class="cover-header">
      <div class="brand-title">Coal India Limited</div>
      <div class="subsidiary-name">{safe_subsidiary}</div>
    </div>
    <div class="cover-center">
      <div class="report-title">{safe_title}</div>
      <div class="period-badge">{safe_period}</div>
    </div>
    <div class="cover-footer">
      <div>Local-First Document Intelligence Platform &bull; Air-Gapped Verification</div>
      <div>Statutory & Financial Compliance</div>
    </div>
  </div>
"""

    def _build_toc(self, sections: List[ReportSection], prefix: str = "") -> str:
        toc_items = []
        for idx, sec in enumerate(sections, 1):
            num = f"{prefix}{idx}" if prefix else f"{idx}"
            level_cls = f"level-{min(sec.level, 2)}"
            safe_title = html.escape(sec.title)

            toc_items.append(
                f'<div class="toc-item {level_cls}">'
                f'  <a href="#{sec.section_id}" style="color:inherit; text-decoration:none;">'
                f'    <span>{num}. {safe_title}</span>'
                f'  </a>'
                f'</div>'
            )

            if sec.subsections:
                toc_items.append(self._build_toc(sec.subsections, prefix=f"{num}."))

        return "\n".join(toc_items)

    def _build_sections(self, sections: List[ReportSection]) -> str:
        parts = []
        for sec in sections:
            parts.append(self._build_single_section(sec))
        return "\n".join(parts)

    def _build_single_section(self, sec: ReportSection) -> str:
        level_tag = min(sec.level, 3)
        title_cls = f"section-title-l{level_tag}"
        safe_title = html.escape(sec.title)

        out = [f'<div id="{sec.section_id}" class="section-container">']
        out.append(f'  <h{level_tag} class="{title_cls}">{safe_title}</h{level_tag}>')

        # 1. Render Assigned Image Assets if available
        if self.asset_catalog:
            assignments = self.asset_catalog.get_section_assignments(sec.section_id)
            if assignments:
                assets = [self.asset_catalog.get_asset(a.asset_id) for a in assignments]
                valid_assets = [a for a in assets if a is not None]
                if valid_assets:
                    layout = assignments[0].layout_type
                    out.append(DeterministicLayoutSelector.generate_html_container(valid_assets, layout))

        # 2. Render Narrative Blocks
        for nb in sec.narrative_blocks:
            if nb.insufficient_evidence:
                out.append(
                    f'  <div class="warning-callout">'
                    f'    <strong>Note:</strong> {html.escape(nb.text)}'
                    f'  </div>'
                )
            else:
                # Highlight citations in narrative text
                escaped_text = html.escape(nb.text)
                formatted_text = re.sub(
                    r"\[(DOC|COORD|REF):([^\]]+)\]",
                    r'<span class="citation-ref">[\1:\2]</span>',
                    escaped_text,
                )
                out.append(f'  <p>{formatted_text}</p>')

        # 3. Render Tables
        for tbl in sec.tables:
            out.append(self._build_table_html(tbl))

        # 4. Render Subsections
        if sec.subsections:
            out.append(self._build_sections(sec.subsections))

        out.append('</div>')
        return "\n".join(out)

    def _build_table_html(self, tbl: Dict[str, Any]) -> str:
        headers = tbl.get("headers", [])
        rows = tbl.get("rows", [])
        title = tbl.get("title", "")

        th_html = "".join(f"<th>{html.escape(str(h))}</th>" for h in headers)

        tr_html = []
        for row in rows:
            if isinstance(row, list):
                is_total = len(row) > 0 and str(row[0]).strip().lower() == "total"
                cls = ' class="total-row"' if is_total else ""
                tds = "".join(f"<td>{html.escape(str(cell))}</td>" for cell in row)
                tr_html.append(f'<tr{cls}>{tds}</tr>')

        caption_html = f"<caption>{html.escape(title)}</caption>" if title else ""

        return (
            f'<table>\n'
            f'  {caption_html}\n'
            f'  <thead>\n'
            f'    <tr>{th_html}</tr>\n'
            f'  </thead>\n'
            f'  <tbody>\n'
            f'    {"".join(tr_html)}\n'
            f'  </tbody>\n'
            f'</table>'
        )
