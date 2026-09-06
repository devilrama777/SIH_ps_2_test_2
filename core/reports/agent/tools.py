"""
Controlled Agent Tools — Section 23 of Master Implementation Specification.

Exposes authorized, strictly-gated application tools for the local editing agent.
The LLM never receives unrestricted filesystem or network access.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from core.assets.catalog import ImageAssetCatalog
from core.retrieval.search import HybridSearchEngine, SearchQuery


class ToolExecutionResult(BaseModel):
    tool_name: str
    success: bool
    data: Any = None
    error: Optional[str] = None


class ControlledAgentTools:
    """
    Security-hardened tool execution layer for agentic report editing.
    """

    def __init__(
        self,
        search_engine: Optional[HybridSearchEngine] = None,
        asset_catalog: Optional[ImageAssetCatalog] = None,
        workspace_dir: str = "data/workspace",
    ):
        self.search_engine = search_engine or HybridSearchEngine()
        self.asset_catalog = asset_catalog or ImageAssetCatalog()
        self.workspace_dir = Path(workspace_dir)

    def search_documents(self, query: str, limit: int = 10) -> ToolExecutionResult:
        """Search canonical text elements across all indexed documents."""
        try:
            results = self.search_engine.search(SearchQuery(query_text=query, limit=min(limit, 25)))
            data = [
                {
                    "document_id": r.document_id,
                    "source_reference": r.source_reference,
                    "page_number": r.page_number,
                    "text": r.text,
                    "score": r.score,
                }
                for r in results
            ]
            return ToolExecutionResult(tool_name="search_documents", success=True, data=data)
        except Exception as exc:
            return ToolExecutionResult(tool_name="search_documents", success=False, error=str(exc))

    def get_source(self, document_id: str) -> ToolExecutionResult:
        """Retrieve metadata for a specific document."""
        p = self.workspace_dir / "canonical_documents" / f"{document_id}.json"
        if not p.exists():
            return ToolExecutionResult(tool_name="get_source", success=False, error=f"Document {document_id} not found")

        try:
            with open(p, "r", encoding="utf-8") as f:
                doc = json.load(f)
            return ToolExecutionResult(
                tool_name="get_source",
                success=True,
                data={
                    "document_id": doc.get("document_id"),
                    "metadata": doc.get("metadata"),
                    "total_pages": doc.get("total_pages"),
                },
            )
        except Exception as exc:
            return ToolExecutionResult(tool_name="get_source", success=False, error=str(exc))

    def get_page(self, document_id: str, page_number: int) -> ToolExecutionResult:
        """Retrieve extracted elements from a specific page of a document."""
        p = self.workspace_dir / "canonical_documents" / f"{document_id}.json"
        if not p.exists():
            return ToolExecutionResult(tool_name="get_page", success=False, error=f"Document {document_id} not found")

        try:
            with open(p, "r", encoding="utf-8") as f:
                doc = json.load(f)

            for page in doc.get("pages", []):
                if page.get("page_number") == page_number:
                    return ToolExecutionResult(tool_name="get_page", success=True, data=page)

            return ToolExecutionResult(tool_name="get_page", success=False, error=f"Page {page_number} not found")
        except Exception as exc:
            return ToolExecutionResult(tool_name="get_page", success=False, error=str(exc))

    def get_image(self, asset_id: str) -> ToolExecutionResult:
        """Retrieve technical and provenance metadata for an image asset."""
        asset = self.asset_catalog.get_asset(asset_id)
        if not asset:
            return ToolExecutionResult(tool_name="get_image", success=False, error=f"Image asset {asset_id} not found")
        return ToolExecutionResult(tool_name="get_image", success=True, data=asset.model_dump())
