"""
LocalFolderConnector — Section 4 of Master Implementation Specification.

Implements the DataConnector abstraction for local directories, folders, and drives.
Provides file discovery, binary retrieval, and health diagnostics.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.connectors.base import ConnectorHealth, DataConnector, SourceItem
from core.ingestion.discovery import DiscoveredFile, discover_files


class LocalFolderConnector(DataConnector):
    """
    Primary connector for the local-first prototype.
    Reads confidential source documents directly from the local filesystem.
    """

    def __init__(self, root_dir: str | Path):
        self.root_dir = Path(root_dir).resolve()
        self._cache: Dict[str, DiscoveredFile] = {}

    def health_check(self) -> ConnectorHealth:
        """Verify the local directory exists, is readable, and measure disk space."""
        if not self.root_dir.exists():
            return ConnectorHealth(
                healthy=False,
                connector_type="local_folder",
                error=f"Directory does not exist: {self.root_dir}",
            )
        if not self.root_dir.is_dir():
            return ConnectorHealth(
                healthy=False,
                connector_type="local_folder",
                error=f"Path is not a directory: {self.root_dir}",
            )
        if not os.access(self.root_dir, os.R_OK):
            return ConnectorHealth(
                healthy=False,
                connector_type="local_folder",
                error=f"Directory is not readable (Permission Denied): {self.root_dir}",
            )

        try:
            total, used, free = shutil.disk_usage(self.root_dir)
            return ConnectorHealth(
                healthy=True,
                connector_type="local_folder",
                details={
                    "path": str(self.root_dir),
                    "disk_total_gb": round(total / (1024**3), 2),
                    "disk_free_gb": round(free / (1024**3), 2),
                },
            )
        except Exception as exc:
            return ConnectorHealth(
                healthy=True,
                connector_type="local_folder",
                details={"path": str(self.root_dir)},
                error=f"Warning: could not read disk usage: {exc}",
            )

    def discover(self, query: Optional[Dict[str, Any]] = None) -> List[SourceItem]:
        """Discover files and optionally filter by format, financial year, or search substring."""
        discovered = discover_files(self.root_dir, compute_hashes=True)
        self._cache = {f.sha256 or f.absolute_path: f for f in discovered}

        items: List[SourceItem] = []
        for df in discovered:
            # Apply optional filters
            if query:
                if "format" in query and df.format.value != query["format"]:
                    continue
                if "financial_year" in query and df.temporal.financial_year != query["financial_year"]:
                    continue
                if "reporting_month" in query and df.temporal.reporting_month != query["reporting_month"]:
                    continue
                if "search" in query and query["search"].lower() not in df.filename.lower():
                    continue

            source_id = df.sha256 or f"src_{hash(df.absolute_path)}"
            items.append(
                SourceItem(
                    source_id=source_id,
                    source_uri=df.source_uri,
                    filename=df.filename,
                    file_extension=df.extension,
                    file_size_bytes=df.file_size_bytes,
                    modified_timestamp=df.modified_at.timestamp() if df.modified_at else None,
                    metadata={
                        "absolute_path": df.absolute_path,
                        "relative_path": df.relative_path,
                        "document_type": df.document_type.value,
                        "format": df.format.value,
                        "sha256": df.sha256,
                        "temporal": df.temporal.model_dump(),
                    },
                )
            )
        return items

    def list_sources(self) -> List[SourceItem]:
        """List all discovered source documents."""
        return self.discover(query=None)

    def fetch_document(self, source_id: str) -> bytes:
        """Fetch raw binary content of a discovered document by source ID (SHA-256 or cached path)."""
        item = self._cache.get(source_id)
        if not item:
            # Re-discover to refresh cache if needed
            self.discover()
            item = self._cache.get(source_id)

        if not item:
            raise FileNotFoundError(f"Source item not found for source_id: {source_id}")

        file_path = Path(item.absolute_path)
        if not file_path.is_file():
            raise FileNotFoundError(f"File vanished from disk: {file_path}")

        with open(file_path, "rb") as f:
            return f.read()

    def fetch_metadata(self, source_id: str) -> Dict[str, Any]:
        """Fetch metadata for a discovered document without loading full bytes."""
        item = self._cache.get(source_id)
        if not item:
            self.discover()
            item = self._cache.get(source_id)

        if not item:
            raise FileNotFoundError(f"Source item not found for source_id: {source_id}")

        return {
            "source_id": source_id,
            "filename": item.filename,
            "absolute_path": item.absolute_path,
            "relative_path": item.relative_path,
            "file_size_bytes": item.file_size_bytes,
            "sha256": item.sha256,
            "temporal": item.temporal.model_dump(),
        }
