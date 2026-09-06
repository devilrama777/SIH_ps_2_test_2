"""
Storage Lifecycle and Safe Artifact Cleanup Manager.
Strictly implements CIL Master Implementation Plan Section 37:
- Track original source, processed representation, OCR results, structured extraction,
  embeddings/indexes, generated reports, temporary render files.
- Provide safe cleanup policies for temporary artifacts.
- NEVER delete original source data automatically unless explicitly authorized.
"""

from dataclasses import dataclass, asdict
from enum import Enum
import logging
from pathlib import Path
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ArtifactCategory(str, Enum):
    ORIGINAL_SOURCE = "original_source"
    CANONICAL_CACHE = "canonical_cache"
    SEARCH_INDEX = "search_index"
    ASSET_CATALOG = "asset_catalog"
    RENDER_TEMP = "render_temp"
    LOGS = "logs"
    REPORTS = "reports"


@dataclass
class StorageCategorySummary:
    category: str
    description: str
    path: str
    file_count: int
    total_bytes: int
    formatted_size: str
    is_safe_to_clean: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def format_bytes(num_bytes: int) -> str:
    """Format bytes into human-readable representation."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if num_bytes < 1024.0 or unit == "TB":
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.2f} B"


class StorageManager:
    """
    Manages workspace storage allocations and enforces strict retention/cleanup rules.
    """

    def __init__(self, workspace_dir: str = "data/workspace"):
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

        # Predefined path categories
        self.category_paths: Dict[ArtifactCategory, Path] = {
            ArtifactCategory.ORIGINAL_SOURCE: self.workspace_dir / "sources",
            ArtifactCategory.CANONICAL_CACHE: self.workspace_dir / "canonical",
            ArtifactCategory.SEARCH_INDEX: self.workspace_dir / "indexes",
            ArtifactCategory.ASSET_CATALOG: self.workspace_dir / "assets",
            ArtifactCategory.RENDER_TEMP: self.workspace_dir / "temp",
            ArtifactCategory.LOGS: self.workspace_dir / "audit_logs",
            ArtifactCategory.REPORTS: self.workspace_dir / "reports",
        }

        # Initialize folders
        for p in self.category_paths.values():
            p.mkdir(parents=True, exist_ok=True)

    def get_storage_breakdown(self) -> Dict[str, StorageCategorySummary]:
        """Compute disk consumption across all tracked artifact categories."""
        descriptions = {
            ArtifactCategory.ORIGINAL_SOURCE: "Original uploaded/scanned source documents (NEVER auto-deleted)",
            ArtifactCategory.CANONICAL_CACHE: "Extracted canonical document models and OCR cache (.json)",
            ArtifactCategory.SEARCH_INDEX: "SQLite FTS5 database and lexical search index tables",
            ArtifactCategory.ASSET_CATALOG: "Cataloged images, diagrams, and perceptual hash metadata",
            ArtifactCategory.RENDER_TEMP: "Intermediate HTML render templates, scratch images, and browser buffers",
            ArtifactCategory.LOGS: "Operational telemetry and tamper-evident audit trail logs",
            ArtifactCategory.REPORTS: "Generated ReportData JSON models and compiled PDF deliverables",
        }

        breakdown: Dict[str, StorageCategorySummary] = {}

        for cat, path in self.category_paths.items():
            file_count = 0
            total_bytes = 0
            if path.exists():
                for item in path.rglob("*"):
                    if item.is_file():
                        file_count += 1
                        try:
                            total_bytes += item.stat().st_size
                        except OSError:
                            pass

            is_safe = cat in [ArtifactCategory.RENDER_TEMP]

            breakdown[cat.value] = StorageCategorySummary(
                category=cat.value,
                description=descriptions.get(cat, ""),
                path=str(path),
                file_count=file_count,
                total_bytes=total_bytes,
                formatted_size=format_bytes(total_bytes),
                is_safe_to_clean=is_safe,
            )

        return breakdown

    def cleanup_temporary_artifacts(
        self,
        max_age_seconds: float = 0.0,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Safely purges ephemeral render files.
        Section 37 Invariant: Original sources are strictly protected and never touched.
        """
        temp_dir = self.category_paths[ArtifactCategory.RENDER_TEMP]
        now = time.time()

        deleted_files: List[str] = []
        freed_bytes: int = 0
        skipped_count: int = 0

        if temp_dir.exists():
            for f in temp_dir.rglob("*"):
                if f.is_file():
                    try:
                        mtime = f.stat().st_mtime
                        size = f.stat().st_size
                        age = now - mtime
                        if age >= max_age_seconds:
                            if not dry_run:
                                f.unlink()
                            deleted_files.append(str(f))
                            freed_bytes += size
                        else:
                            skipped_count += 1
                    except OSError as e:
                        logger.warning(f"Error checking/deleting temp file {f}: {e}")

        logger.info(
            f"Storage cleanup: deleted {len(deleted_files)} files, "
            f"freed {format_bytes(freed_bytes)} (dry_run={dry_run})"
        )

        return {
            "deleted_file_count": len(deleted_files),
            "freed_bytes": freed_bytes,
            "formatted_freed": format_bytes(freed_bytes),
            "skipped_recent_files": skipped_count,
            "dry_run": dry_run,
            "deleted_files": deleted_files,
        }

    def safe_purge_category(self, category: ArtifactCategory, confirmation: str) -> Dict[str, Any]:
        """
        Purges non-source categories only if explicit confirmation matches.
        Refuses to delete ORIGINAL_SOURCE under any condition through this method.
        """
        if category == ArtifactCategory.ORIGINAL_SOURCE:
            raise PermissionError(
                "Violation of Section 37 Invariant: ORIGINAL_SOURCE cannot be purged via safe_purge_category."
            )

        expected_confirmation = f"PURGE_{category.value.upper()}"
        if confirmation != expected_confirmation:
            raise ValueError(f"Invalid confirmation token. Expected '{expected_confirmation}'.")

        target_dir = self.category_paths[category]
        deleted = 0
        freed = 0

        if target_dir.exists():
            for f in target_dir.rglob("*"):
                if f.is_file():
                    try:
                        freed += f.stat().st_size
                        f.unlink()
                        deleted += 1
                    except OSError:
                        pass

        return {
            "category": category.value,
            "deleted_count": deleted,
            "freed_bytes": freed,
            "formatted_freed": format_bytes(freed),
        }
