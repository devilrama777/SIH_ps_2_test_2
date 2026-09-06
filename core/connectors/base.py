"""
DataConnector Abstraction — Section 4 of Master Implementation Specification.

Provides an extensible contract for discovering and fetching source documents.
In Phase 0/1, LocalFolderConnector will be the primary implementation.
Future CIL connectors (API, SQL, Network Share, SharePoint, SFTP) will plug into this interface.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class SourceItem(BaseModel):
    """Metadata of an individual source document discovered by a connector."""
    source_id: str
    source_uri: str
    filename: str
    file_extension: str
    file_size_bytes: int
    modified_timestamp: Optional[float] = None
    metadata: Dict[str, Any] = {}


class ConnectorHealth(BaseModel):
    """Health status and diagnostic details of a data source connector."""
    healthy: bool
    connector_type: str
    details: Dict[str, Any] = {}
    error: Optional[str] = None


class DataConnector(ABC):
    """
    Abstract interface for all data ingestion connectors.
    Decouples document processing from physical data source topology.
    """

    @abstractmethod
    def discover(self, query: Optional[Dict[str, Any]] = None) -> List[SourceItem]:
        """Discover available source documents matching an optional query or filter."""
        pass

    @abstractmethod
    def list_sources(self) -> List[SourceItem]:
        """Enumerate all accessible source items currently available."""
        pass

    @abstractmethod
    def fetch_document(self, source_id: str) -> bytes:
        """Fetch raw binary content of a specific source document."""
        pass

    @abstractmethod
    def fetch_metadata(self, source_id: str) -> Dict[str, Any]:
        """Fetch metadata for a specific source document without retrieving full content."""
        pass

    @abstractmethod
    def health_check(self) -> ConnectorHealth:
        """Perform a liveness and access check on the connector."""
        pass
