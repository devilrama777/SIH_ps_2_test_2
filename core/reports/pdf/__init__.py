"""
PDF Generation & Rendering Package — Sections 19 & 20 of Master Plan.
"""
from core.reports.pdf.html_builder import ReportHtmlBuilder
from core.reports.pdf.renderer import PdfRenderer, PdfRenderResult
from core.reports.pdf.templates.classic import CLASSIC_CSS
from core.reports.pdf.templates.modern import MODERN_CSS

__all__ = [
    "ReportHtmlBuilder",
    "PdfRenderer",
    "PdfRenderResult",
    "CLASSIC_CSS",
    "MODERN_CSS",
]
