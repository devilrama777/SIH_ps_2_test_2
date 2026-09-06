"""
File Discovery and Traversal — Section 6 of Master Implementation Specification.

Recursively scans directories, enforces security boundaries against path traversal,
filters supported extensions, and collects filesystem + temporal metadata.
"""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional
from pydantic import BaseModel, Field

from core.ingestion.formats import (
    DocumentFormat,
    detect_format,
    is_disallowed_format,
    is_supported_format,
    map_to_document_type,
)
from core.ingestion.temporal import extract_temporal_metadata, TemporalMetadata
from core.ingestion.fingerprint import compute_file_hash
from core.domain.documents import DocumentType

EXCLUDED_DIR_NAMES = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "dist",
    "build",
    "$recycle.bin",
    "system volume information",
}


class DiscoveredFile(BaseModel):
    """Rich metadata for an individual source document discovered on the filesystem."""
    source_uri: str
    absolute_path: str
    relative_path: str
    filename: str
    extension: str
    file_size_bytes: int
    format: DocumentFormat
    document_type: DocumentType
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    sha256: Optional[str] = None
    temporal: TemporalMetadata = Field(default_factory=TemporalMetadata)


def discover_files(
    root_dir: str | Path,
    compute_hashes: bool = True,
    progress_callback: Optional[Callable[[int, str], None]] = None,
) -> List[DiscoveredFile]:
    """
    Safely discover all supported documents under root_dir.
    Rejects path traversal or symlinks escaping root_dir.
    """
    root = Path(root_dir).resolve()
    if not root.is_dir():
        raise NotADirectoryError(f"Directory not found or inaccessible: {root}")

    discovered: List[DiscoveredFile] = []
    count = 0

    for current_dir, dir_names, filenames in os.walk(root, followlinks=False):
        # In-place filter to avoid traversing ignored / virtual directories
        dir_names[:] = [d for d in dir_names if d.lower() not in EXCLUDED_DIR_NAMES and not d.startswith(".")]

        current_path = Path(current_dir)
        # Ensure path stays within root boundaries (prevents directory traversal)
        try:
            current_path.resolve().relative_to(root)
        except ValueError:
            continue

        for filename in filenames:
            if filename.startswith("~$") or filename.startswith("."):
                continue  # Skip temporary office lockfiles and hidden files

            file_path = current_path / filename
            if not file_path.is_file():
                continue

            # Check supported extensions
            if is_disallowed_format(file_path):
                continue
            if not is_supported_format(file_path):
                continue

            fmt = detect_format(file_path)
            doc_type = map_to_document_type(fmt)

            try:
                stat = file_path.stat()
                size_bytes = stat.st_size
                mtime = datetime.fromtimestamp(stat.st_mtime)
                ctime = datetime.fromtimestamp(stat.st_ctime)
            except (OSError, PermissionError):
                continue

            # Compute SHA-256 fingerprint if requested
            file_hash = None
            if compute_hashes:
                try:
                    file_hash = compute_file_hash(file_path)
                except Exception:
                    continue

            # Extract temporal metadata from folder + filename
            temporal = extract_temporal_metadata(file_path)
            rel_path = str(file_path.relative_to(root)).replace("\\", "/")

            discovered_item = DiscoveredFile(
                source_uri=file_path.as_uri(),
                absolute_path=str(file_path.resolve()),
                relative_path=rel_path,
                filename=filename,
                extension=file_path.suffix.lower(),
                file_size_bytes=size_bytes,
                format=fmt,
                document_type=doc_type,
                created_at=ctime,
                modified_at=mtime,
                sha256=file_hash,
                temporal=temporal,
            )

            discovered.append(discovered_item)
            count += 1
            if progress_callback:
                progress_callback(count, str(file_path))

    return discovered
