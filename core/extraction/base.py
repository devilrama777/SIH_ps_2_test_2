"""
Base Document Extractor Interface — Section 6 & 9 of Master Implementation Plan.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional
from core.domain.documents import CanonicalDocument
from core.ingestion.discovery import DiscoveredFile


class BaseExtractor(ABC):
    """Abstract interface for format-specific document extractors."""

    @abstractmethod
    def extract(self, file_path: Path, discovered: Optional[DiscoveredFile] = None) -> CanonicalDocument:
        """
        Extract structured elements from a file and return a CanonicalDocument
        with coordinate-level provenance.
        """
        pass
