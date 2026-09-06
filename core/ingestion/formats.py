"""
Format Detection and Filtering — Section 3 of Master Implementation Specification.

Enforces supported input formats:
- PDF (digital and scanned)
- DOCX
- XLSX
- CSV
- TXT
- Images: JPG, JPEG, PNG, TIFF, TIF
Disallows: ZIP/archive and PPTX ingestion per Section 3.
"""
from __future__ import annotations

import os
from enum import Enum
from pathlib import Path
from typing import Optional, Set
from core.domain.documents import DocumentType


class DocumentFormat(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    CSV = "csv"
    TXT = "txt"
    IMAGE = "image"
    UNSUPPORTED = "unsupported"


# Extensions permitted by Section 3 specification
SUPPORTED_EXTENSIONS: Set[str] = {
    ".pdf",
    ".docx",
    ".xlsx",
    ".csv",
    ".txt",
    ".jpg",
    ".jpeg",
    ".png",
    ".tiff",
    ".tif",
}

# Explicitly disallowed formats per Section 3
DISALLOWED_EXTENSIONS: Set[str] = {
    ".zip",
    ".tar",
    ".gz",
    ".7z",
    ".rar",
    ".pptx",
    ".ppt",
}

EXTENSION_TO_FORMAT = {
    ".pdf": DocumentFormat.PDF,
    ".docx": DocumentFormat.DOCX,
    ".xlsx": DocumentFormat.XLSX,
    ".csv": DocumentFormat.CSV,
    ".txt": DocumentFormat.TXT,
    ".jpg": DocumentFormat.IMAGE,
    ".jpeg": DocumentFormat.IMAGE,
    ".png": DocumentFormat.IMAGE,
    ".tiff": DocumentFormat.IMAGE,
    ".tif": DocumentFormat.IMAGE,
}

FORMAT_TO_DOC_TYPE = {
    DocumentFormat.PDF: DocumentType.DIGITAL_PDF,  # specialized in Phase 2 via layout/OCR check
    DocumentFormat.DOCX: DocumentType.DOCX,
    DocumentFormat.XLSX: DocumentType.XLSX,
    DocumentFormat.CSV: DocumentType.CSV,
    DocumentFormat.TXT: DocumentType.TXT,
    DocumentFormat.IMAGE: DocumentType.IMAGE,
}


def is_supported_format(file_path: str | Path) -> bool:
    """Check if the given file extension is supported per specification."""
    ext = Path(file_path).suffix.lower()
    return ext in SUPPORTED_EXTENSIONS


def is_disallowed_format(file_path: str | Path) -> bool:
    """Check if the file belongs to explicitly excluded formats (e.g. ZIP or PPTX)."""
    ext = Path(file_path).suffix.lower()
    return ext in DISALLOWED_EXTENSIONS


def detect_format(file_path: str | Path) -> DocumentFormat:
    """Detect document format from file path."""
    ext = Path(file_path).suffix.lower()
    return EXTENSION_TO_FORMAT.get(ext, DocumentFormat.UNSUPPORTED)


def map_to_document_type(fmt: DocumentFormat) -> DocumentType:
    """Map detected format to core domain DocumentType."""
    return FORMAT_TO_DOC_TYPE.get(fmt, DocumentType.UNKNOWN)
