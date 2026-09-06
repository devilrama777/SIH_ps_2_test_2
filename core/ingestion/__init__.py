"""
Ingestion Subsystem — Section 6 of Master Implementation Specification.
"""
from core.ingestion.formats import (
    SUPPORTED_EXTENSIONS,
    DocumentFormat,
    detect_format,
    is_supported_format,
)
from core.ingestion.fingerprint import compute_file_hash, compute_bytes_hash
from core.ingestion.temporal import extract_temporal_metadata, TemporalMetadata
from core.ingestion.discovery import discover_files, DiscoveredFile
from core.ingestion.jobs import IngestionJobManager

__all__ = [
    "SUPPORTED_EXTENSIONS",
    "DiscoveredFile",
    "DocumentFormat",
    "IngestionJobManager",
    "TemporalMetadata",
    "compute_bytes_hash",
    "compute_file_hash",
    "detect_format",
    "discover_files",
    "extract_temporal_metadata",
    "is_supported_format",
]
