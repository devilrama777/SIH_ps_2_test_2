"""
Extraction Subsystem — Section 6, 7, 8, 9 of Master Implementation Specification.
"""
from core.extraction.base import BaseExtractor
from core.extraction.docx_extractor import DOCXExtractor
from core.extraction.image_extractor import ImageExtractor
from core.extraction.pdf_extractor import PDFExtractor
from core.extraction.text_csv_extractor import CSVExtractor, TextExtractor
from core.extraction.unified import UnifiedDocumentExtractor, extract_document
from core.extraction.xlsx_extractor import XLSXExtractor

__all__ = [
    "BaseExtractor",
    "CSVExtractor",
    "DOCXExtractor",
    "ImageExtractor",
    "PDFExtractor",
    "TextExtractor",
    "UnifiedDocumentExtractor",
    "XLSXExtractor",
    "extract_document",
]
