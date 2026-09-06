"""
Unified Extraction Dispatcher — Section 6 of Master Implementation Specification.

Routes incoming documents to the appropriate format extractor and returns
a validated CanonicalDocument instance with coordinate-level provenance.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Type

from core.domain.documents import CanonicalDocument
from core.extraction.base import BaseExtractor
from core.extraction.docx_extractor import DOCXExtractor
from core.extraction.image_extractor import ImageExtractor
from core.extraction.pdf_extractor import PDFExtractor
from core.extraction.text_csv_extractor import CSVExtractor, TextExtractor
from core.extraction.xlsx_extractor import XLSXExtractor
from core.ingestion.discovery import DiscoveredFile
from core.ingestion.formats import DocumentFormat, detect_format


class UnifiedDocumentExtractor:
    """
    Central dispatcher coordinating format-specific extractors.
    """

    def __init__(self):
        self._extractors: Dict[DocumentFormat, BaseExtractor] = {
            DocumentFormat.PDF: PDFExtractor(),
            DocumentFormat.XLSX: XLSXExtractor(),
            DocumentFormat.DOCX: DOCXExtractor(),
            DocumentFormat.CSV: CSVExtractor(),
            DocumentFormat.TXT: TextExtractor(),
            DocumentFormat.IMAGE: ImageExtractor(),
        }

    def extract(self, file_path: Path | str, discovered: Optional[DiscoveredFile] = None) -> CanonicalDocument:
        path = Path(file_path).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"File to extract not found: {path}")

        fmt = discovered.format if discovered else detect_format(path)
        extractor = self._extractors.get(fmt)

        if not extractor:
            raise ValueError(f"No extractor registered for format: {fmt} (file: {path.name})")

        return extractor.extract(path, discovered=discovered)


_default_extractor = UnifiedDocumentExtractor()


def extract_document(file_path: Path | str, discovered: Optional[DiscoveredFile] = None) -> CanonicalDocument:
    """Convenience helper to extract any supported document into a CanonicalDocument."""
    return _default_extractor.extract(file_path, discovered=discovered)
