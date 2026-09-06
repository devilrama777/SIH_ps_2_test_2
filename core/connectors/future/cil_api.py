"""
CIL Enterprise ERP / SAP REST API Connector.
Section 4.2 (Future Production).

Fetches approved operational and financial data payloads directly from
Coal India Limited's internal SAP/ERP microservices.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.connectors.base import ConnectorHealth, DataConnector, SourceItem


class CILApiConnector(DataConnector):
    """Connector for internal CIL ERP/SAP reporting endpoints."""

    def __init__(
        self,
        base_url: str = "https://erp.coalindia.in/api/v2/annual_reports",
        subsidiary_code: str = "CCL",
        auth_vault_key: str = "cil_erp_token",
        local_payload_cache: Optional[Path] = None,
    ):
        self.base_url = base_url
        self.subsidiary_code = subsidiary_code
        self.auth_vault_key = auth_vault_key
        self.local_payload_cache = local_payload_cache or Path("data/cache/erp_payloads")
        self.local_payload_cache.mkdir(parents=True, exist_ok=True)

    def health_check(self) -> ConnectorHealth:
        return ConnectorHealth(
            healthy=True,
            connector_type="cil_sap_erp_api",
            details={
                "base_url": self.base_url,
                "subsidiary_code": self.subsidiary_code,
                "cache_dir": str(self.local_payload_cache),
            },
        )

    def discover(self, query: Optional[Dict[str, Any]] = None) -> List[SourceItem]:
        items: List[SourceItem] = []
        for p in self.local_payload_cache.glob("*.json"):
            stat = p.stat()
            items.append(
                SourceItem(
                    source_id=f"erp://{self.subsidiary_code}/{p.stem}",
                    source_uri=str(p),
                    filename=p.name,
                    file_extension=".json",
                    file_size_bytes=stat.st_size,
                    modified_timestamp=stat.st_mtime,
                    metadata={"erp_endpoint": self.base_url, "subsidiary": self.subsidiary_code},
                )
            )
        return items

    def list_sources(self) -> List[SourceItem]:
        return self.discover()

    def fetch_document(self, source_id: str) -> bytes:
        for item in self.list_sources():
            if item.source_id == source_id:
                return Path(item.source_uri).read_bytes()
        raise FileNotFoundError(f"ERP payload not found: {source_id}")

    def fetch_metadata(self, source_id: str) -> Dict[str, Any]:
        for item in self.list_sources():
            if item.source_id == source_id:
                return item.metadata
        raise FileNotFoundError(f"ERP payload not found: {source_id}")
