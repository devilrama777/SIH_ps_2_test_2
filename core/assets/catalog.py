"""
Image Asset Catalog — Section 18 of Master Implementation Specification.

SQLite-backed persistent image repository with duplicate detection,
perceptual similarity matching, and section assignment workflows.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.assets.analyzer import ImageAssetAnalyzer
from core.assets.models import (
    ImageAsset,
    ImageAssetAssignment,
    ImageLayoutType,
    ImageQualityGrade,
)


class ImageAssetCatalog:
    """
    Manages indexing, deduplication, search, and layout assignments of report image assets.
    """

    def __init__(self, db_path: str = "data/workspace/assets.db"):
        self.db_path = db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS image_assets (
                    asset_id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    format TEXT NOT NULL,
                    width INTEGER NOT NULL,
                    height INTEGER NOT NULL,
                    aspect_ratio REAL NOT NULL,
                    file_size_bytes INTEGER NOT NULL,
                    sha256_hash TEXT NOT NULL,
                    phash TEXT,
                    dpi INTEGER,
                    quality_grade TEXT NOT NULL,
                    is_duplicate INTEGER DEFAULT 0,
                    duplicate_of TEXT,
                    caption TEXT,
                    tags TEXT,
                    recommended_layout TEXT NOT NULL,
                    provenance_id TEXT,
                    source_document_id TEXT,
                    page_number INTEGER,
                    metadata TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS section_image_assignments (
                    assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    section_id TEXT NOT NULL,
                    asset_id TEXT NOT NULL,
                    layout_type TEXT NOT NULL,
                    caption TEXT,
                    display_order INTEGER DEFAULT 1,
                    width_percentage INTEGER DEFAULT 100,
                    FOREIGN KEY(asset_id) REFERENCES image_assets(asset_id)
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_assets_sha ON image_assets(sha256_hash)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_assignments_sec ON section_image_assignments(section_id)")
            conn.commit()

    def register_image(
        self,
        file_path: str,
        source_document_id: Optional[str] = None,
        page_number: Optional[int] = None,
        provenance_id: Optional[str] = None,
    ) -> ImageAsset:
        asset = ImageAssetAnalyzer.analyze_image(
            file_path=file_path,
            source_document_id=source_document_id,
            page_number=page_number,
            provenance_id=provenance_id,
        )

        with self._get_conn() as conn:
            # 1. Exact duplicate check (SHA256)
            exact_match = conn.execute(
                "SELECT asset_id FROM image_assets WHERE sha256_hash = ? AND is_duplicate = 0 LIMIT 1",
                (asset.sha256_hash,),
            ).fetchone()

            if exact_match:
                asset.is_duplicate = True
                asset.duplicate_of = exact_match["asset_id"]
            elif asset.phash and asset.phash != "0000000000000000":
                # 2. Perceptual near-duplicate check (dHash Hamming distance <= 4)
                cursor = conn.execute(
                    "SELECT asset_id, phash FROM image_assets WHERE is_duplicate = 0 AND phash IS NOT NULL AND phash != '0000000000000000'"
                )
                for row in cursor.fetchall():
                    dist = ImageAssetAnalyzer.hamming_distance(asset.phash, row["phash"])
                    if dist <= 4:
                        asset.is_duplicate = True
                        asset.duplicate_of = row["asset_id"]
                        break

            # 3. Insert or Replace into Database
            conn.execute(
                """
                INSERT OR REPLACE INTO image_assets (
                    asset_id, filename, file_path, format, width, height, aspect_ratio,
                    file_size_bytes, sha256_hash, phash, dpi, quality_grade, is_duplicate,
                    duplicate_of, caption, tags, recommended_layout, provenance_id,
                    source_document_id, page_number, metadata, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    asset.asset_id,
                    asset.filename,
                    asset.file_path,
                    asset.format,
                    asset.width,
                    asset.height,
                    asset.aspect_ratio,
                    asset.file_size_bytes,
                    asset.sha256_hash,
                    asset.phash,
                    asset.dpi,
                    asset.quality_grade.value,
                    1 if asset.is_duplicate else 0,
                    asset.duplicate_of,
                    asset.caption,
                    json.dumps(asset.tags),
                    asset.recommended_layout.value,
                    asset.provenance_id,
                    asset.source_document_id,
                    asset.page_number,
                    json.dumps(asset.metadata),
                    asset.created_at.isoformat(),
                ),
            )
            conn.commit()

        return asset

    register_asset = register_image

    def get_asset(self, asset_id: str) -> Optional[ImageAsset]:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM image_assets WHERE asset_id = ?", (asset_id,)).fetchone()
            if not row:
                return None
            return self._row_to_asset(row)

    def list_assets(
        self,
        tag: Optional[str] = None,
        min_quality: Optional[ImageQualityGrade] = None,
        include_duplicates: bool = False,
    ) -> List[ImageAsset]:
        with self._get_conn() as conn:
            query = "SELECT * FROM image_assets WHERE 1=1"
            params: List[Any] = []

            if not include_duplicates:
                query += " AND is_duplicate = 0"

            if min_quality:
                # Filter out unsuitable or low_res if requested
                if min_quality == ImageQualityGrade.ACCEPTABLE:
                    query += " AND quality_grade IN ('acceptable', 'excellent')"
                elif min_quality == ImageQualityGrade.EXCELLENT:
                    query += " AND quality_grade = 'excellent'"

            query += " ORDER BY created_at DESC"
            rows = conn.execute(query, params).fetchall()

            assets = [self._row_to_asset(r) for r in rows]
            if tag:
                assets = [a for a in assets if tag.lower() in [t.lower() for t in a.tags]]
            return assets

    def find_duplicates(self, asset: ImageAsset, hamming_threshold: int = 5) -> List[Tuple[ImageAsset, int]]:
        """Finds near-duplicates for a given asset using Hamming distance on phash."""
        duplicates = []
        if not asset.phash:
            return duplicates

        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT * FROM image_assets WHERE asset_id != ? AND phash IS NOT NULL",
                (asset.asset_id,),
            )
            for row in cursor.fetchall():
                cand = self._row_to_asset(row)
                dist = ImageAssetAnalyzer.hamming_distance(asset.phash, cand.phash)
                if dist <= hamming_threshold or cand.duplicate_of == asset.asset_id or asset.duplicate_of == cand.asset_id:
                    duplicates.append((cand, dist))
        return duplicates

    def assign_to_section(
        self,
        section_id: str,
        asset_id: str,
        layout_type: Optional[ImageLayoutType] = None,
        caption: Optional[str] = None,
        display_order: int = 1,
        width_percentage: int = 100,
    ) -> ImageAssetAssignment:
        asset = self.get_asset(asset_id)
        if not asset:
            raise ValueError(f"Asset not found: {asset_id}")

        assigned_layout = layout_type or asset.recommended_layout
        assigned_caption = caption or asset.caption

        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO section_image_assignments (
                    section_id, asset_id, layout_type, caption, display_order, width_percentage
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    section_id,
                    asset_id,
                    assigned_layout.value,
                    assigned_caption,
                    display_order,
                    width_percentage,
                ),
            )
            conn.commit()

        return ImageAssetAssignment(
            section_id=section_id,
            asset_id=asset_id,
            layout_type=assigned_layout,
            caption=assigned_caption,
            display_order=display_order,
            width_percentage=width_percentage,
        )

    def get_section_assignments(self, section_id: str) -> List[ImageAssetAssignment]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM section_image_assignments WHERE section_id = ? ORDER BY display_order ASC",
                (section_id,),
            ).fetchall()
            return [
                ImageAssetAssignment(
                    section_id=r["section_id"],
                    asset_id=r["asset_id"],
                    layout_type=ImageLayoutType(r["layout_type"]),
                    caption=r["caption"],
                    display_order=r["display_order"],
                    width_percentage=r["width_percentage"],
                )
                for r in rows
            ]

    def _row_to_asset(self, row: sqlite3.Row) -> ImageAsset:
        return ImageAsset(
            asset_id=row["asset_id"],
            filename=row["filename"],
            file_path=row["file_path"],
            format=row["format"],
            width=row["width"],
            height=row["height"],
            aspect_ratio=row["aspect_ratio"],
            file_size_bytes=row["file_size_bytes"],
            sha256_hash=row["sha256_hash"],
            phash=row["phash"],
            dpi=row["dpi"],
            quality_grade=ImageQualityGrade(row["quality_grade"]),
            is_duplicate=bool(row["is_duplicate"]),
            duplicate_of=row["duplicate_of"],
            caption=row["caption"],
            tags=json.loads(row["tags"] or "[]"),
            recommended_layout=ImageLayoutType(row["recommended_layout"]),
            provenance_id=row["provenance_id"],
            source_document_id=row["source_document_id"],
            page_number=row["page_number"],
            metadata=json.loads(row["metadata"] or "{}"),
            created_at=datetime.fromisoformat(row["created_at"]),
        )


AssetCatalog = ImageAssetCatalog
