"""
DocumentNormalizer: Secondary LLM-friendly Markdown Normalization Layer — Section 8 of Master Plan.

Converts CanonicalDocument structured elements (pages, headings, tables, links, images)
into clean, hierarchical Markdown with embedded provenance anchors for rapid LLM context injection.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.domain.documents import CanonicalDocument, DocumentElement, ElementType

logger = logging.getLogger(__name__)


class DocumentNormalizer:
    """
    Transforms canonical document structures into structured Markdown with provenance comments.
    """

    def __init__(self, output_dir: Optional[Path | str] = None) -> None:
        self.output_dir = Path(output_dir or "data/workspace/normalized")

    def normalize(self, doc: CanonicalDocument) -> str:
        """
        Normalizes a CanonicalDocument into an LLM-friendly Markdown representation.
        Embeds provenance comment anchors that preserve element and page traceability.
        """
        lines: List[str] = []

        # Document Header metadata block
        lines.append(f"# Document: {Path(doc.source_reference).name}")
        lines.append(f"<!-- doc_id: {doc.document_id} | hash: {doc.source_hash[:12]} | type: {doc.document_type.value} -->\n")

        if doc.reporting_year or doc.reporting_period:
            period_str = f"**Reporting Period:** {doc.reporting_year or ''} {doc.reporting_period or ''}".strip()
            lines.append(f"{period_str}\n")

        # Process page by page
        for page in doc.pages:
            lines.append(f"\n--- Page {page.page_number} ---")
            sorted_elements = sorted(
                page.elements,
                key=lambda el: (el.reading_order if el.reading_order is not None else 9999)
            )

            for el in sorted_elements:
                provenance_comment = f"<!-- provenance: doc={doc.document_id} page={page.page_number} el={el.element_id} type={el.type.value} -->"

                if el.type == ElementType.HEADING:
                    level = el.metadata.get("level", 2)
                    prefix = "#" * max(2, min(level + 1, 5))
                    lines.append(f"\n{prefix} {el.text or ''}")
                    lines.append(provenance_comment)

                elif el.type == ElementType.PARAGRAPH:
                    if el.text and el.text.strip():
                        lines.append(f"\n{el.text.strip()}")
                        lines.append(provenance_comment)

                elif el.type == ElementType.TABLE:
                    table_md = self._render_table_markdown(el)
                    if table_md:
                        lines.append(f"\n{table_md}")
                        lines.append(provenance_comment)

                elif el.type == ElementType.IMAGE:
                    caption = el.metadata.get("caption", "Figure / Photograph")
                    lines.append(f"\n![{caption}](asset:{el.element_id})")
                    lines.append(f"*{caption}*")
                    lines.append(provenance_comment)

                elif el.type == ElementType.CAPTION:
                    lines.append(f"\n*{el.text or ''}*")
                    lines.append(provenance_comment)

                elif el.type == ElementType.LINK:
                    url = el.metadata.get("url", "#")
                    text = el.text or url
                    lines.append(f"\n[{text}]({url})")
                    lines.append(provenance_comment)

                elif el.type in (ElementType.SPREADSHEET_CELL, ElementType.TABLE_CELL):
                    # Handled via parent table or standalone cell
                    if el.text:
                        lines.append(f"\n- **{el.metadata.get('cell', 'Cell')}**: {el.text}")
                        lines.append(provenance_comment)

        # Standalone tables if not embedded in pages
        if not doc.pages and doc.tables:
            lines.append("\n## Extracted Tables")
            for idx, tbl in enumerate(doc.tables, 1):
                headers = tbl.get("headers", [])
                rows = tbl.get("rows", [])
                title = tbl.get("title", f"Table {idx}")
                lines.append(f"\n### {title}")
                tbl_md = self._format_markdown_grid(headers, rows)
                lines.append(tbl_md)

        normalized_text = "\n".join(lines).strip()
        doc.markdown_content = normalized_text
        return normalized_text

    def _render_table_markdown(self, el: DocumentElement) -> str:
        """Renders an ElementType.TABLE element into GFM markdown table."""
        headers: List[str] = el.metadata.get("headers", [])
        rows: List[List[str]] = el.metadata.get("rows", [])

        if not headers and not rows:
            return el.text or ""

        return self._format_markdown_grid(headers, rows)

    def _format_markdown_grid(self, headers: List[str], rows: List[List[Any]]) -> str:
        """Helper to construct GFM table grid."""
        if not headers and rows:
            headers = [f"Col {i+1}" for i in range(len(rows[0]))]

        if not headers:
            return ""

        str_headers = [str(h).strip().replace("\n", " ") for h in headers]
        header_line = "| " + " | ".join(str_headers) + " |"
        sep_line = "| " + " | ".join(["---"] * len(str_headers)) + " |"

        row_lines = []
        for r in rows:
            str_cells = []
            for i in range(len(str_headers)):
                cell_val = r[i] if i < len(r) else ""
                clean_val = str(cell_val).strip().replace("\n", " ").replace("|", "\\|")
                str_cells.append(clean_val)
            row_lines.append("| " + " | ".join(str_cells) + " |")

        return "\n".join([header_line, sep_line] + row_lines)

    def normalize_and_save(self, doc: CanonicalDocument) -> Path:
        """Normalizes and saves Markdown representation to disk."""
        text = self.normalize(doc)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        target_path = self.output_dir / f"{doc.document_id}.md"
        target_path.write_text(text, encoding="utf-8")
        logger.info("Saved normalized Markdown for %s to %s", doc.document_id, target_path)
        return target_path
