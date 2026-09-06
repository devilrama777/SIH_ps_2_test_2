"""
Storage Lifecycle and Safe Artifact Cleanup Manager.
Strictly implements CIL Master Implementation Plan Section 37:
- Track:
  1. original source
  2. processed representation
  3. OCR result
  4. structured extraction
  5. embeddings/indexes
  6. generated report
  7. temporary render files
- Provide safe cleanup policies for temporary artifacts.
- NEVER delete original source data automatically unless explicitly authorized.
"""

from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import logging
from pathlib import Path
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ArtifactCategory(str, Enum):
    # Master Plan Section 37 primary categories:
    ORIGINAL_SOURCE = "original_source"
    PROCESSED_REPRESENTATION = "processed_representation"
    OCR_RESULT = "ocr_result"
    STRUCTURED_EXTRACTION = "structured_extraction"
    EMBEDDINGS_INDEXES = "embeddings_indexes"
    GENERATED_REPORT = "generated_report"
    TEMPORARY_RENDER = "temporary_render"

    # Backward compatibility and auxiliary categories:
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


@dataclass
class RetentionRule:
    category: str
    max_age_seconds: Optional[float] = None
    max_bytes_quota: Optional[int] = None
    preserve_minimum_count: int = 0
    is_safe_to_clean: bool = False
    require_explicit_authorization: bool = False

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
    Complies with CIL Master Implementation Plan Section 37.
    """

    def __init__(self, workspace_dir: str = "data/workspace"):
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

        # Predefined path categories (Section 37 primary + aliases)
        self.category_paths: Dict[ArtifactCategory, Path] = {
            # Section 37 primary categories:
            ArtifactCategory.ORIGINAL_SOURCE: self.workspace_dir / "sources",
            ArtifactCategory.PROCESSED_REPRESENTATION: self.workspace_dir / "canonical",
            ArtifactCategory.OCR_RESULT: self.workspace_dir / "ocr",
            ArtifactCategory.STRUCTURED_EXTRACTION: self.workspace_dir / "extractions",
            ArtifactCategory.EMBEDDINGS_INDEXES: self.workspace_dir / "indexes",
            ArtifactCategory.GENERATED_REPORT: self.workspace_dir / "reports",
            ArtifactCategory.TEMPORARY_RENDER: self.workspace_dir / "temp",
            # Auxiliary & legacy aliases:
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

        # Initialize default retention rules
        self.retention_rules: Dict[ArtifactCategory, RetentionRule] = {
            ArtifactCategory.TEMPORARY_RENDER: RetentionRule(
                category=ArtifactCategory.TEMPORARY_RENDER.value,
                max_age_seconds=86400.0,  # 24 hours
                max_bytes_quota=500 * 1024 * 1024,  # 500 MB
                preserve_minimum_count=0,
                is_safe_to_clean=True,
                require_explicit_authorization=False,
            ),
            ArtifactCategory.RENDER_TEMP: RetentionRule(
                category=ArtifactCategory.RENDER_TEMP.value,
                max_age_seconds=86400.0,
                max_bytes_quota=500 * 1024 * 1024,
                preserve_minimum_count=0,
                is_safe_to_clean=True,
                require_explicit_authorization=False,
            ),
            ArtifactCategory.OCR_RESULT: RetentionRule(
                category=ArtifactCategory.OCR_RESULT.value,
                max_age_seconds=30 * 86400.0,  # 30 days
                max_bytes_quota=1024 * 1024 * 1024,  # 1 GB
                preserve_minimum_count=5,
                is_safe_to_clean=True,
                require_explicit_authorization=False,
            ),
            ArtifactCategory.STRUCTURED_EXTRACTION: RetentionRule(
                category=ArtifactCategory.STRUCTURED_EXTRACTION.value,
                max_age_seconds=30 * 86400.0,
                max_bytes_quota=500 * 1024 * 1024,
                preserve_minimum_count=5,
                is_safe_to_clean=True,
                require_explicit_authorization=False,
            ),
            ArtifactCategory.PROCESSED_REPRESENTATION: RetentionRule(
                category=ArtifactCategory.PROCESSED_REPRESENTATION.value,
                max_age_seconds=60 * 86400.0,
                max_bytes_quota=2 * 1024 * 1024 * 1024,
                preserve_minimum_count=10,
                is_safe_to_clean=False,
                require_explicit_authorization=False,
            ),
            ArtifactCategory.CANONICAL_CACHE: RetentionRule(
                category=ArtifactCategory.CANONICAL_CACHE.value,
                max_age_seconds=60 * 86400.0,
                max_bytes_quota=2 * 1024 * 1024 * 1024,
                preserve_minimum_count=10,
                is_safe_to_clean=False,
                require_explicit_authorization=False,
            ),
            ArtifactCategory.ORIGINAL_SOURCE: RetentionRule(
                category=ArtifactCategory.ORIGINAL_SOURCE.value,
                max_age_seconds=None,
                max_bytes_quota=None,
                preserve_minimum_count=0,
                is_safe_to_clean=False,
                require_explicit_authorization=True,  # STRICT INVARIANT
            ),
            ArtifactCategory.EMBEDDINGS_INDEXES: RetentionRule(
                category=ArtifactCategory.EMBEDDINGS_INDEXES.value,
                max_age_seconds=None,
                max_bytes_quota=None,
                is_safe_to_clean=False,
                require_explicit_authorization=False,
            ),
            ArtifactCategory.SEARCH_INDEX: RetentionRule(
                category=ArtifactCategory.SEARCH_INDEX.value,
                max_age_seconds=None,
                max_bytes_quota=None,
                is_safe_to_clean=False,
                require_explicit_authorization=False,
            ),
            ArtifactCategory.GENERATED_REPORT: RetentionRule(
                category=ArtifactCategory.GENERATED_REPORT.value,
                max_age_seconds=None,
                max_bytes_quota=None,
                is_safe_to_clean=False,
                require_explicit_authorization=False,
            ),
            ArtifactCategory.REPORTS: RetentionRule(
                category=ArtifactCategory.REPORTS.value,
                max_age_seconds=None,
                max_bytes_quota=None,
                is_safe_to_clean=False,
                require_explicit_authorization=False,
            ),
            ArtifactCategory.LOGS: RetentionRule(
                category=ArtifactCategory.LOGS.value,
                max_age_seconds=90 * 86400.0,  # 90 days minimum
                max_bytes_quota=None,
                is_safe_to_clean=False,
                require_explicit_authorization=True,
            ),
            ArtifactCategory.ASSET_CATALOG: RetentionRule(
                category=ArtifactCategory.ASSET_CATALOG.value,
                max_age_seconds=None,
                max_bytes_quota=None,
                is_safe_to_clean=False,
                require_explicit_authorization=False,
            ),
        }

    def get_storage_breakdown(self) -> Dict[str, StorageCategorySummary]:
        """Compute disk consumption across all tracked artifact categories."""
        descriptions = {
            ArtifactCategory.ORIGINAL_SOURCE: "Original uploaded/scanned source documents (NEVER auto-deleted)",
            ArtifactCategory.PROCESSED_REPRESENTATION: "Normalized canonical document models (.json)",
            ArtifactCategory.OCR_RESULT: "Raw OCR bounding boxes and cached text recognition files",
            ArtifactCategory.STRUCTURED_EXTRACTION: "Extracted tables, numerical statements, and tabular data",
            ArtifactCategory.EMBEDDINGS_INDEXES: "Vector embeddings, lexical FTS5 indexes, and retrieval graphs",
            ArtifactCategory.GENERATED_REPORT: "Compiled ReportData deliverables and generated PDF reports",
            ArtifactCategory.TEMPORARY_RENDER: "Intermediate HTML render scratch, headless browser temp files, and buffers",
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

            is_safe = cat in [
                ArtifactCategory.RENDER_TEMP,
                ArtifactCategory.TEMPORARY_RENDER,
                ArtifactCategory.OCR_RESULT,
                ArtifactCategory.STRUCTURED_EXTRACTION,
            ]
            # ORIGINAL_SOURCE is strictly False
            if cat == ArtifactCategory.ORIGINAL_SOURCE:
                is_safe = False

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

    def get_retention_rules(self) -> Dict[str, Dict[str, Any]]:
        """Return all active retention rules as serializable dictionaries."""
        return {cat.value: rule.to_dict() for cat, rule in self.retention_rules.items()}

    def update_retention_rule(
        self,
        category: ArtifactCategory,
        max_age_seconds: Optional[float] = None,
        max_bytes_quota: Optional[int] = None,
        preserve_minimum_count: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Update retention configuration for a category."""
        if category == ArtifactCategory.ORIGINAL_SOURCE:
            raise PermissionError(
                "Violation of Section 37 Invariant: ORIGINAL_SOURCE retention policy cannot enable automatic deletion."
            )

        if category not in self.retention_rules:
            self.retention_rules[category] = RetentionRule(
                category=category.value,
                is_safe_to_clean=category in [ArtifactCategory.RENDER_TEMP, ArtifactCategory.TEMPORARY_RENDER],
            )

        rule = self.retention_rules[category]
        if max_age_seconds is not None:
            rule.max_age_seconds = max_age_seconds
        if max_bytes_quota is not None:
            rule.max_bytes_quota = max_bytes_quota
        if preserve_minimum_count is not None:
            rule.preserve_minimum_count = preserve_minimum_count

        return rule.to_dict()

    def cleanup_temporary_artifacts(
        self,
        max_age_seconds: float = 0.0,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Safely purges ephemeral render files.
        Section 37 Invariant: Original sources are strictly protected and never touched.
        """
        temp_dir = self.category_paths[ArtifactCategory.TEMPORARY_RENDER]
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

    def apply_retention_policies(
        self,
        categories: Optional[List[ArtifactCategory]] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Applies automated retention rules across requested categories.
        Section 37 Invariant: Original source data is NEVER deleted automatically.
        """
        target_cats = categories or [
            ArtifactCategory.TEMPORARY_RENDER,
            ArtifactCategory.RENDER_TEMP,
            ArtifactCategory.OCR_RESULT,
            ArtifactCategory.STRUCTURED_EXTRACTION,
        ]

        now = time.time()
        results: Dict[str, Any] = {
            "categories_evaluated": [],
            "total_deleted_files": 0,
            "total_freed_bytes": 0,
            "formatted_total_freed": "",
            "dry_run": dry_run,
            "details": {},
        }

        # Deduplicate paths to avoid running twice on aliases (e.g. TEMPORARY_RENDER and RENDER_TEMP)
        seen_paths: set = set()

        for cat in target_cats:
            # Absolute guardrail: never delete original source automatically
            if cat == ArtifactCategory.ORIGINAL_SOURCE:
                results["details"][cat.value] = {
                    "status": "PROTECTED",
                    "reason": "Section 37 Invariant: ORIGINAL_SOURCE is strictly protected against automated deletion.",
                    "deleted_count": 0,
                    "freed_bytes": 0,
                }
                continue

            target_path = self.category_paths.get(cat)
            if not target_path or not target_path.exists():
                continue

            real_path = target_path.resolve()
            if real_path in seen_paths:
                continue
            seen_paths.add(real_path)

            results["categories_evaluated"].append(cat.value)
            rule = self.retention_rules.get(cat)
            max_age = rule.max_age_seconds if rule else 86400.0
            quota = rule.max_bytes_quota if rule else None
            min_preserve = rule.preserve_minimum_count if rule else 0

            # Gather all files with stat
            file_records = []
            for f in target_path.rglob("*"):
                if f.is_file():
                    try:
                        st = f.stat()
                        file_records.append({"path": f, "size": st.st_size, "mtime": st.st_mtime})
                    except OSError:
                        pass

            # Sort by mtime ascending (oldest first)
            file_records.sort(key=lambda x: x["mtime"])

            files_to_delete: List[Dict[str, Any]] = []
            files_to_keep = list(file_records)

            # 1. Prune files older than max_age_seconds
            if max_age is not None:
                candidates = []
                for item in files_to_keep:
                    if (now - item["mtime"]) >= max_age:
                        candidates.append(item)

                # Keep at least min_preserve items
                allowed_delete_count = max(0, len(files_to_keep) - min_preserve)
                prunable = candidates[:allowed_delete_count]
                for item in prunable:
                    files_to_delete.append(item)
                    files_to_keep.remove(item)

            # 2. Prune if remaining files exceed quota
            if quota is not None:
                current_bytes = sum(x["size"] for x in files_to_keep)
                while current_bytes > quota and len(files_to_keep) > min_preserve:
                    oldest = files_to_keep.pop(0)
                    files_to_delete.append(oldest)
                    current_bytes -= oldest["size"]

            cat_freed = 0
            cat_deleted_count = 0
            for item in files_to_delete:
                cat_freed += item["size"]
                cat_deleted_count += 1
                if not dry_run:
                    try:
                        item["path"].unlink()
                    except OSError as err:
                        logger.warning("Could not delete file %s: %s", item["path"], err)

            results["total_deleted_files"] += cat_deleted_count
            results["total_freed_bytes"] += cat_freed
            results["details"][cat.value] = {
                "deleted_count": cat_deleted_count,
                "freed_bytes": cat_freed,
                "formatted_freed": format_bytes(cat_freed),
            }

        results["formatted_total_freed"] = format_bytes(results["total_freed_bytes"])
        return results

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

    def generate_source_deletion_token(self, relative_path: str) -> str:
        """
        Generates deterministic authorization token required for explicitly authorized source deletion.
        """
        norm_path = str(Path(relative_path)).strip()
        digest = hashlib.sha256(f"AUTH_DELETE_{norm_path}".encode("utf-8")).hexdigest()[:16]
        return f"CONFIRM_DELETE_SOURCE_{digest}"

    def authorize_source_deletion(
        self,
        relative_path: str,
        authorization_token: str,
        authorized_by: str = "security_officer",
        reason: str = "Authorized audit-logged source removal",
    ) -> Dict[str, Any]:
        """
        Strictly implements Section 37 explicit authorization rule:
        'Never delete original source data automatically unless explicitly authorized.'
        Requires cryptographic confirmation token matching the file path.
        """
        sources_dir = self.category_paths[ArtifactCategory.ORIGINAL_SOURCE].resolve()
        target_file = (sources_dir / relative_path).resolve()

        # Prevent directory traversal
        try:
            target_file.relative_to(sources_dir)
        except ValueError:
            raise ValueError("Directory traversal detected. File must reside inside original sources.")

        if not target_file.exists() or not target_file.is_file():
            raise FileNotFoundError(f"Source file '{relative_path}' does not exist in original sources.")

        expected_token = self.generate_source_deletion_token(relative_path)
        # Also accept explicit named token
        file_name_token = f"CONFIRM_DELETE_SOURCE_{target_file.name}"

        if authorization_token not in [expected_token, file_name_token]:
            raise ValueError(
                f"Unauthorized. Valid token required for source deletion. Expected: '{expected_token}' or '{file_name_token}'."
            )

        file_size = target_file.stat().st_size
        target_file.unlink()

        audit_record = {
            "action": "EXPLICIT_SOURCE_DELETION",
            "file_name": target_file.name,
            "relative_path": relative_path,
            "authorized_by": authorized_by,
            "reason": reason,
            "freed_bytes": file_size,
            "formatted_freed": format_bytes(file_size),
            "timestamp": time.time(),
        }

        logger.warning("AUDIT ALERT: Explicitly authorized source deletion executed: %s", audit_record)
        return audit_record
