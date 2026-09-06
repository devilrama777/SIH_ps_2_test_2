"""
Pre-flight Environment Diagnostics and Verification Tool.
Section 38 & Section 39 (Phase 12).

Verifies system capabilities, air-gapped readiness, SQLite FTS5 support,
memory, disk storage, and document processing prerequisites before launching
or packaging the CIL Local AI Report Generator.
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import sqlite3
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


@dataclass
class CheckResult:
    name: str
    passed: bool
    details: str
    critical: bool = True
    remediation: Optional[str] = None


@dataclass
class EnvironmentDiagnosticReport:
    timestamp: str
    system_os: str
    os_release: str
    architecture: str
    python_version: str
    overall_status: bool
    checks: List[CheckResult] = field(default_factory=list)
    hardware_summary: Dict[str, Any] = field(default_factory=dict)


class EnvironmentVerifier:
    """Verifies all environmental and architectural preconditions for local CIL report generation."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path.cwd()

    def check_python_version(self) -> CheckResult:
        major, minor = sys.version_info.major, sys.version_info.minor
        passed = (major == 3 and minor >= 11)
        details = f"Python {major}.{minor}.{sys.version_info.micro} detected"
        remediation = "Install Python 3.11 or higher (3.11 - 3.13 recommended)." if not passed else None
        return CheckResult("python_version", passed, details, critical=True, remediation=remediation)

    def check_memory(self) -> CheckResult:
        if not HAS_PSUTIL:
            return CheckResult(
                "system_memory",
                True,
                "RAM check skipped (psutil not installed yet; install dependencies to verify)",
                critical=False,
            )
        mem = psutil.virtual_memory()
        total_gb = mem.total / (1024 ** 3)
        avail_gb = mem.available / (1024 ** 3)
        # 8 GB minimum, 16 GB recommended as per Section 0 of Master Plan
        passed = total_gb >= 7.5  # allow minor hardware reservation under 8 GB
        details = f"Total RAM: {total_gb:.1f} GB (Available: {avail_gb:.1f} GB)"
        remediation = "At least 8 GB RAM required (16 GB strongly recommended for 400-page reports)." if not passed else None
        return CheckResult("system_memory", passed, details, critical=True, remediation=remediation)

    def check_disk_space(self) -> CheckResult:
        usage = shutil.disk_usage(self.base_dir)
        free_gb = usage.free / (1024 ** 3)
        # Minimum 5 GB free, 10 GB recommended
        passed = free_gb >= 5.0
        details = f"Free Disk Space: {free_gb:.1f} GB on {self.base_dir.drive or '/'}"
        remediation = "Free up at least 5 GB (10 GB recommended for document cache & indexes)." if not passed else None
        return CheckResult("disk_space", passed, details, critical=True, remediation=remediation)

    def check_sqlite_fts5(self) -> CheckResult:
        try:
            conn = sqlite3.connect(":memory:")
            cursor = conn.cursor()
            cursor.execute("CREATE VIRTUAL TABLE test_fts USING fts5(content);")
            cursor.execute("INSERT INTO test_fts (content) VALUES ('Coal India Limited Annual Report 2024');")
            cursor.execute("SELECT content FROM test_fts WHERE test_fts MATCH 'Coal';")
            row = cursor.fetchone()
            conn.close()
            passed = bool(row and "Coal" in row[0])
            details = "SQLite FTS5 full-text search extension is compiled and functional"
            remediation = None
        except Exception as exc:
            passed = False
            details = f"SQLite FTS5 unavailable: {exc}"
            remediation = "Recompile Python with SQLite3 FTS5 module enabled."
        return CheckResult("sqlite_fts5", passed, details, critical=True, remediation=remediation)

    def check_workspace_directories(self) -> CheckResult:
        required_dirs = [
            self.base_dir / "data" / "workspace",
            self.base_dir / "data" / "indexes",
            self.base_dir / "data" / "cache",
            self.base_dir / "models" / "cache",
        ]
        created = []
        for d in required_dirs:
            if not d.exists():
                d.mkdir(parents=True, exist_ok=True)
                created.append(str(d.relative_to(self.base_dir)))
        details = f"Workspace directories verified ({len(created)} created: {', '.join(created) if created else 'all existed'})"
        return CheckResult("workspace_directories", True, details, critical=True)

    def check_document_libraries(self) -> CheckResult:
        missing = []
        libraries = {
            "pymupdf (fitz)": "fitz",
            "openpyxl": "openpyxl",
            "python-docx": "docx",
            "Pillow": "PIL",
            "fastapi": "fastapi",
            "uvicorn": "uvicorn",
            "pydantic": "pydantic",
        }
        for name, mod in libraries.items():
            try:
                __import__(mod)
            except ImportError:
                missing.append(name)
        
        passed = len(missing) == 0
        details = "All core document intelligence libraries available" if passed else f"Missing: {', '.join(missing)}"
        remediation = f"Run: pip install -e .[document]" if not passed else None
        return CheckResult("document_libraries", passed, details, critical=True, remediation=remediation)

    def check_local_model_cache(self) -> CheckResult:
        models_dir = self.base_dir / "models" / "cache"
        models_dir.mkdir(parents=True, exist_ok=True)
        gguf_files = list(models_dir.glob("*.gguf"))
        bin_files = list(models_dir.glob("*.bin"))
        total_models = len(gguf_files) + len(bin_files)
        
        # In prototype/development, mock fallback is permitted if no GGUF is installed
        details = f"Found {total_models} local model weights ({len(gguf_files)} GGUF) in models/cache/"
        if total_models == 0:
            details += " (Platform running in Local Mock/Deterministic fallback mode)"
        return CheckResult("local_model_cache", True, details, critical=False)

    def check_loopback_binding_security(self) -> CheckResult:
        from apps.processing.config import settings
        passed = settings.host in ("127.0.0.1", "localhost") and not settings.allow_external_network
        details = f"Host binding: {settings.host}, External network allowed: {settings.allow_external_network}"
        remediation = "Set HOST=127.0.0.1 and ALLOW_EXTERNAL_NETWORK=false in .env" if not passed else None
        return CheckResult("loopback_security", passed, details, critical=True, remediation=remediation)

    def run_all_checks(self) -> EnvironmentDiagnosticReport:
        from datetime import datetime
        checks = [
            self.check_python_version(),
            self.check_memory(),
            self.check_disk_space(),
            self.check_sqlite_fts5(),
            self.check_workspace_directories(),
            self.check_document_libraries(),
            self.check_local_model_cache(),
            self.check_loopback_binding_security(),
        ]
        
        critical_passed = all(c.passed for c in checks if c.critical)
        if HAS_PSUTIL:
            mem = psutil.virtual_memory()
            hw_summary = {
                "cpu_count_logical": psutil.cpu_count(logical=True),
                "cpu_count_physical": psutil.cpu_count(logical=False),
                "ram_total_gb": round(mem.total / (1024 ** 3), 2),
                "platform": platform.platform(),
                "processor": platform.processor(),
            }
        else:
            hw_summary = {
                "cpu_count_logical": os.cpu_count(),
                "cpu_count_physical": os.cpu_count(),
                "ram_total_gb": "unknown (psutil required)",
                "platform": platform.platform(),
                "processor": platform.processor(),
            }

        return EnvironmentDiagnosticReport(
            timestamp=datetime.now().isoformat(),
            system_os=platform.system(),
            os_release=platform.release(),
            architecture=platform.machine(),
            python_version=platform.python_version(),
            overall_status=critical_passed,
            checks=checks,
            hardware_summary=hw_summary,
        )


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Verify CIL Local AI Report Generator Environment")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    args = parser.parse_args()

    verifier = EnvironmentVerifier()
    report = verifier.run_all_checks()

    if args.json:
        print(json.dumps(asdict(report), indent=2))
    else:
        print("=" * 70)
        print("  CIL Local AI Report Generator — Pre-Flight Diagnostic Report")
        print("=" * 70)
        print(f"OS:          {report.system_os} {report.os_release} ({report.architecture})")
        print(f"Python:      {report.python_version}")
        print(f"Timestamp:   {report.timestamp}")
        print(f"CPU Cores:   {report.hardware_summary.get('cpu_count_logical', 'N/A')}")
        print(f"Total RAM:   {report.hardware_summary.get('ram_total_gb', 'N/A')} GB")
        print("-" * 70)
        for c in report.checks:
            mark = "PASS" if c.passed else ("FAIL" if c.critical else "WARN")
            print(f"[{mark:4}] {c.name:<25} : {c.details}")
            if not c.passed and c.remediation:
                print(f"       -> Remediation: {c.remediation}")
        print("=" * 70)
        if report.overall_status:
            print("OVERALL STATUS: READY FOR AIR-GAPPED DEPLOYMENT (PASS)")
        else:
            print("OVERALL STATUS: ENVIRONMENT CHECKS FAILED (FAIL)")
        print("=" * 70)

    sys.exit(0 if report.overall_status else 1)


if __name__ == "__main__":
    main()
