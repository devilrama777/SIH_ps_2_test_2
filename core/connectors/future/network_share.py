r"""
Enterprise Network Share / SMB / UNC Connector.
Section 4.2 (Future Production).

Connects to enterprise network file shares (UNC paths e.g. \\cil-fileserver\data)
using encrypted credentials stored in the SecureCredentialVault.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.connectors.base import ConnectorHealth, DataConnector, SourceItem
from core.ingestion.formats import is_supported_format


class NetworkShareConnector(DataConnector):
    """Data connector for enterprise SMB / UNC network shares."""

    def __init__(
        self,
        share_path: str,
        domain: Optional[str] = "COALINDIA",
        username: Optional[str] = None,
        auth_credential_key: Optional[str] = "cil_smb_share",
    ):
        self.share_path = Path(share_path)
        self.domain = domain
        self.username = username
        self.auth_credential_key = auth_credential_key

    def health_check(self) -> ConnectorHealth:
        try:
            if not self.share_path.exists():
                return ConnectorHealth(
                    healthy=False,
                    connector_type="network_share",
                    error=f"Network share path not accessible: {self.share_path}",
                )
            return ConnectorHealth(
                healthy=True,
                connector_type="network_share",
                details={
                    "share_path": str(self.share_path),
                    "domain": self.domain,
                    "is_dir": self.share_path.is_dir(),
                },
            )
        except Exception as exc:
            return ConnectorHealth(
                healthy=False,
                connector_type="network_share",
                error=f"Access error: {exc}",
            )

    def discover(self, query: Optional[Dict[str, Any]] = None) -> List[SourceItem]:
        if not self.share_path.exists() or not self.share_path.is_dir():
            return []

        items: List[SourceItem] = []
        for root, _, files in os.walk(self.share_path):
            for f in files:
                if not is_supported_format(f):
                    continue
                ext = Path(f).suffix.lower()
                full_p = Path(root) / f
                try:
                    stat = full_p.stat()
                    items.append(
                        SourceItem(
                            source_id=f"smb://{full_p.relative_to(self.share_path).as_posix()}",
                            source_uri=str(full_p),
                            filename=f,
                            file_extension=ext,
                            file_size_bytes=stat.st_size,
                            modified_timestamp=stat.st_mtime,
                            metadata={"share": str(self.share_path), "domain": self.domain},
                        )
                    )
                except OSError:
                    continue
        return items

    def list_sources(self) -> List[SourceItem]:
        return self.discover()

    def fetch_document(self, source_id: str) -> bytes:
        for item in self.list_sources():
            if item.source_id == source_id:
                return Path(item.source_uri).read_bytes()
        raise FileNotFoundError(f"Source not found on network share: {source_id}")

    def fetch_metadata(self, source_id: str) -> Dict[str, Any]:
        for item in self.list_sources():
            if item.source_id == source_id:
                return item.metadata
        raise FileNotFoundError(f"Source not found on network share: {source_id}")
