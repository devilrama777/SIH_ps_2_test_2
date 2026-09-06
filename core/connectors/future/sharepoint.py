"""
Enterprise SharePoint / DMS Connector.
Section 4.2 (Future Production).

Interacts with Microsoft SharePoint / enterprise Document Management Systems
for downloading approved subsidiary source documents.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from core.connectors.base import ConnectorHealth, DataConnector, SourceItem


class SharePointConnector(DataConnector):
    """Connector for SharePoint document libraries."""

    def __init__(
        self,
        site_url: str = "https://coalindia.sharepoint.com/sites/ccl_annual_reports",
        library_name: str = "Financial_And_Operational_Submissions",
        tenant_id: Optional[str] = "cil-enterprise-tenant",
        local_staging_dir: Optional[Path] = None,
    ):
        self.site_url = site_url
        self.library_name = library_name
        self.tenant_id = tenant_id
        self.local_staging_dir = local_staging_dir or Path("data/cache/sharepoint_sync")
        self.local_staging_dir.mkdir(parents=True, exist_ok=True)

    def health_check(self) -> ConnectorHealth:
        return ConnectorHealth(
            healthy=True,
            connector_type="sharepoint_dms",
            details={
                "site_url": self.site_url,
                "library_name": self.library_name,
                "tenant_id": self.tenant_id,
                "sync_dir": str(self.local_staging_dir),
            },
        )

    def discover(self, query: Optional[Dict[str, Any]] = None) -> List[SourceItem]:
        items: List[SourceItem] = []
        if not self.local_staging_dir.exists():
            return items

        for p in self.local_staging_dir.glob("*.*"):
            if p.is_file():
                stat = p.stat()
                items.append(
                    SourceItem(
                        source_id=f"sp://{self.library_name}/{p.name}",
                        source_uri=str(p),
                        filename=p.name,
                        file_extension=p.suffix.lower(),
                        file_size_bytes=stat.st_size,
                        modified_timestamp=stat.st_mtime,
                        metadata={
                            "site_url": self.site_url,
                            "library": self.library_name,
                        },
                    )
                )
        return items

    def list_sources(self) -> List[SourceItem]:
        return self.discover()

    def fetch_document(self, source_id: str) -> bytes:
        for item in self.list_sources():
            if item.source_id == source_id:
                return Path(item.source_uri).read_bytes()
        raise FileNotFoundError(f"Document not found in SharePoint staging: {source_id}")

    def fetch_metadata(self, source_id: str) -> Dict[str, Any]:
        for item in self.list_sources():
            if item.source_id == source_id:
                return item.metadata
        raise FileNotFoundError(f"Document not found in SharePoint staging: {source_id}")
