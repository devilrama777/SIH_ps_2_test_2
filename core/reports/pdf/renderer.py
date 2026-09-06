"""
PDF Report Renderer — Section 19 of Master Implementation Specification.

Renders HTML/CSS reports to high-quality print PDFs using local headless Chromium
(or PyMuPDF fallback) in a fully air-gapped environment.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field

import fitz  # PyMuPDF for page inspection and fallback

from core.assets.catalog import ImageAssetCatalog
from core.domain.reports import Report
from core.reports.pdf.html_builder import ReportHtmlBuilder


class PdfRenderResult(BaseModel):
    """Execution telemetry and artifacts from PDF rendering."""
    report_id: str
    template_name: str
    pdf_path: str
    html_path: str
    page_count: int
    file_size_bytes: int
    render_time_seconds: float
    renderer_engine: str  # 'chromium' or 'pymupdf'


class PdfRenderer:
    """
    Renders reports to publication-grade PDFs using local browser/PDF engines.
    """

    DEFAULT_CHROMIUM_CANDIDATES = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        "msedge",
        "chrome",
        "chromium",
        "google-chrome",
    ]

    def __init__(
        self,
        asset_catalog: Optional[ImageAssetCatalog] = None,
        output_dir: str = "data/workspace/reports",
        chromium_path: Optional[str] = None,
    ):
        self.html_builder = ReportHtmlBuilder(asset_catalog=asset_catalog)
        self.output_dir = output_dir
        self.chromium_path = chromium_path or self._discover_chromium()
        os.makedirs(self.output_dir, exist_ok=True)

    def _discover_chromium(self) -> Optional[str]:
        for candidate in self.DEFAULT_CHROMIUM_CANDIDATES:
            if os.path.exists(candidate):
                return candidate
            resolved = shutil.which(candidate)
            if resolved:
                return resolved
        return None

    def render_report(self, report: Report, template_name: str = "modern") -> PdfRenderResult:
        start_time = time.time()

        # 1. Build and persist HTML document
        html_content = self.html_builder.build_html(report, template_name=template_name)
        html_file = Path(self.output_dir) / f"{report.report_id}_{template_name}.html"
        pdf_file = Path(self.output_dir) / f"{report.report_id}_{template_name}.pdf"

        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        engine_used = "chromium"

        # 2. Render PDF with Headless Chromium if available
        if self.chromium_path:
            abs_html = Path(html_file).resolve()
            abs_pdf = Path(pdf_file).resolve()

            cmd = [
                self.chromium_path,
                "--headless",
                "--disable-gpu",
                "--run-all-compositor-stages-before-draw",
                "--no-pdf-header-footer",
                f"--print-to-pdf={str(abs_pdf)}",
                f"file:///{str(abs_html).replace(os.sep, '/')}",
            ]

            try:
                subprocess.run(cmd, check=True, capture_output=True, timeout=30)
            except Exception:
                # Fallback if command fails
                self._render_with_pymupdf_fallback(html_content, str(pdf_file))
                engine_used = "pymupdf"
        else:
            self._render_with_pymupdf_fallback(html_content, str(pdf_file))
            engine_used = "pymupdf"

        # 3. Read Page Count and Size using PyMuPDF
        page_count = 1
        file_size = 0
        if pdf_file.exists():
            file_size = os.path.getsize(pdf_file)
            try:
                with fitz.open(str(pdf_file)) as doc:
                    page_count = len(doc)
            except Exception:
                page_count = 1

        elapsed = round(time.time() - start_time, 3)

        return PdfRenderResult(
            report_id=report.report_id,
            template_name=template_name,
            pdf_path=str(pdf_file.resolve()),
            html_path=str(html_file.resolve()),
            page_count=page_count,
            file_size_bytes=file_size,
            render_time_seconds=elapsed,
            renderer_engine=engine_used,
        )

    def _render_with_pymupdf_fallback(self, html_content: str, output_pdf_path: str) -> None:
        """Fallback lightweight text/story PDF generation with PyMuPDF."""
        doc = fitz.open()
        page = doc.new_page(width=595, height=842)  # A4 points
        # Insert minimal structured text
        text_lines = [line.strip() for line in html_content.splitlines() if line.strip().startswith("<p>") or line.strip().startswith("<h")]
        y = 60
        for line in text_lines[:50]:
            clean_text = line.replace("<p>", "").replace("</p>", "").replace("<h1>", "").replace("</h1>", "").replace("<h2>", "").replace("</h2>", "")
            page.insert_text((50, y), clean_text[:80], fontsize=10)
            y += 18
            if y > 780:
                page = doc.new_page(width=595, height=842)
                y = 60
        doc.save(output_pdf_path)
        doc.close()
