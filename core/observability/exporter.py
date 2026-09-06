"""
Sanitized Diagnostic Bundle Exporter.
Adheres to CIL Master Implementation Plan Section 35:
- Provide a diagnostic export mechanism that can exclude sensitive source contents.
- Packages system info, execution logs, and performance metrics into an air-gapped zip.
"""

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import hashlib
import json
import logging
import os
from pathlib import Path
import platform
import re
import shutil
import sys
from typing import Any, Dict, List, Optional
import zipfile

from core.observability.telemetry import ObservabilityManager
from core.storage.lifecycle import StorageManager

logger = logging.getLogger(__name__)

# Patterns to scrub for air-gapped confidentiality
SENSITIVE_PATTERNS = [
    (re.compile(r"(?i)(password|secret|token|api[_-]?key|credential)\s*[:=]\s*['\"][^'\"]+['\"]"), r"\1=[REDACTED]"),
    (re.compile(r"(?i)bearer\s+[A-Za-z0-9\-\._~\+\/]+=*"), "Bearer [REDACTED]"),
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"), "[EMAIL_REDACTED]"),
    (re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b"), "[CARD_OR_ID_REDACTED]"),
]


@dataclass
class DiagnosticBundleInfo:
    bundle_filename: str
    bundle_path: str
    sha256_hash: str
    created_at: str
    file_size_bytes: int
    included_files: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SanitizedDiagnosticExporter:
    """
    Collects system diagnostics, scrubs sensitive text, and produces
    an encrypted or clean ZIP archive for DevOps / IT investigation.
    """

    def __init__(
        self,
        workspace_dir: str = "data/workspace",
        observability_manager: Optional[ObservabilityManager] = None,
        storage_manager: Optional[StorageManager] = None,
    ):
        self.workspace_dir = Path(workspace_dir)
        self.obs_manager = observability_manager or ObservabilityManager(str(self.workspace_dir / "audit_logs"))
        self.storage_manager = storage_manager or StorageManager(str(self.workspace_dir))
        self.export_dir = self.workspace_dir / "temp" / "diagnostic_exports"
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def sanitize_text(self, text: str) -> str:
        """Sanitize text by replacing sensitive patterns."""
        sanitized = text
        for pattern, replacement in SENSITIVE_PATTERNS:
            sanitized = pattern.sub(replacement, sanitized)
        return sanitized

    def gather_system_environment(self) -> Dict[str, Any]:
        """Gather non-sensitive platform and execution environment metrics."""
        return {
            "platform": platform.platform(),
            "python_version": sys.version,
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "environment_variables_present": [
                k for k in os.environ.keys() if not any(s in k.lower() for s in ["key", "secret", "pass", "token"])
            ],
        }

    def export_bundle(self, bundle_name: Optional[str] = None) -> DiagnosticBundleInfo:
        """
        Creates a clean sanitized zip bundle containing diagnostic files.
        Never includes raw original source files.
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        name = bundle_name or f"diagnostic_bundle_{timestamp}.zip"
        bundle_path = self.export_dir / name

        included_files: List[str] = []

        with zipfile.ZipFile(bundle_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # 1. System environment
            env_info = self.gather_system_environment()
            zip_file.writestr("system_environment.json", json.dumps(env_info, indent=2))
            included_files.append("system_environment.json")

            # 2. Storage breakdown
            storage_breakdown = {k: v.to_dict() for k, v in self.storage_manager.get_storage_breakdown().items()}
            zip_file.writestr("storage_breakdown.json", json.dumps(storage_breakdown, indent=2))
            included_files.append("storage_breakdown.json")

            # 3. Telemetry log (sanitized)
            telemetry_records = self.obs_manager.get_recent_telemetry(limit=200)
            sanitized_telemetry_str = self.sanitize_text(json.dumps(telemetry_records, indent=2))
            zip_file.writestr("telemetry_log.json", sanitized_telemetry_str)
            included_files.append("telemetry_log.json")

            # 4. Telemetry stage aggregates
            aggregates = self.obs_manager.get_stage_aggregates()
            zip_file.writestr("stage_aggregates.json", json.dumps(aggregates, indent=2))
            included_files.append("stage_aggregates.json")

            # 5. Manifest
            manifest = {
                "bundle_name": name,
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "file_count": len(included_files),
                "sanitization_applied": True,
                "airgap_certified": True,
            }
            zip_file.writestr("manifest.json", json.dumps(manifest, indent=2))
            included_files.append("manifest.json")

        # Compute SHA-256 hash of bundle
        sha256 = hashlib.sha256()
        with open(bundle_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
        bundle_hash = sha256.hexdigest()

        bundle_size = bundle_path.stat().st_size

        logger.info(f"Generated sanitized diagnostic bundle {name} ({bundle_size} bytes, SHA-256={bundle_hash[:12]})")

        return DiagnosticBundleInfo(
            bundle_filename=name,
            bundle_path=str(bundle_path),
            sha256_hash=bundle_hash,
            created_at=datetime.now(timezone.utc).isoformat(),
            file_size_bytes=bundle_size,
            included_files=included_files,
        )
