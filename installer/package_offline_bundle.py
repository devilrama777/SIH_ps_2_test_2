"""
Air-Gapped Offline Bundle Packager.
Section 38 & Section 39 (Phase 12).

Packages the CIL Local AI Report Generator into a self-contained, air-gapped
distribution bundle with cryptographic SHA-256 manifest verification.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def compute_sha256(filepath: Path) -> str:
    """Computes SHA-256 hex digest for a file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class OfflineBundlePackager:
    """Creates a self-contained air-gapped distribution bundle."""

    INCLUDE_DIRS = [
        "core",
        "apps/processing",
        "installer",
    ]

    INCLUDE_FILES = [
        "pyproject.toml",
        "README.md",
        ".env.example",
        "CIL_Local_AI_Report_Generator_Master_Implementation_Plan.md",
    ]

    LAUNCHER_SCRIPTS = [
        "run_desktop.bat",
        "run_server.bat",
        "run_desktop.sh",
        "run_server.sh",
    ]

    def __init__(self, root_dir: Optional[Path] = None, output_dir: Optional[Path] = None):
        self.root_dir = (root_dir or Path.cwd()).resolve()
        self.output_dir = (output_dir or (self.root_dir / "dist" / "offline_bundle")).resolve()

    def build_bundle(self, create_zip: bool = True) -> Tuple[Path, Dict]:
        """Collects files, builds SHA-256 manifest, and optionally archives to ZIP."""
        staging_dir = self.output_dir / "cil-report-ai-v0.1.0-airgapped"
        if staging_dir.exists():
            shutil.rmtree(staging_dir)
        staging_dir.mkdir(parents=True, exist_ok=True)

        manifest_entries: List[Dict] = []

        # 1. Copy Include Directories
        for rel_dir in self.INCLUDE_DIRS:
            src_dir = self.root_dir / rel_dir
            if not src_dir.exists():
                continue
            dest_dir = staging_dir / rel_dir
            dest_dir.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy tree ignoring cache and temp files
            def ignore_patterns(path, names):
                return {n for n in names if n in ("__pycache__", ".pytest_cache") or n.endswith(".pyc")}

            shutil.copytree(src_dir, dest_dir, ignore=ignore_patterns)

        # 2. Copy Frontend Dist if available
        frontend_dist = self.root_dir / "apps" / "desktop" / "dist"
        if frontend_dist.exists():
            dest_fe = staging_dir / "apps" / "desktop" / "dist"
            dest_fe.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(frontend_dist, dest_fe)

        # 3. Copy Root Configuration Files
        for rel_file in self.INCLUDE_FILES:
            src_file = self.root_dir / rel_file
            if src_file.exists():
                shutil.copy2(src_file, staging_dir / rel_file)

        # 4. Copy Launchers
        for script in self.LAUNCHER_SCRIPTS:
            src_script = self.root_dir / script
            if src_script.exists():
                shutil.copy2(src_script, staging_dir / script)

        # 5. Copy or ensure setup script
        setup_script = self.root_dir / "installer" / "setup_offline.py"
        if setup_script.exists():
            dest_setup = staging_dir / "setup_offline.py"
            shutil.copy2(setup_script, dest_setup)

        # 6. Ensure data and models directory placeholders exist
        for placeholder in ("data/workspace", "data/indexes", "data/cache", "models/cache"):
            p = staging_dir / placeholder
            p.mkdir(parents=True, exist_ok=True)
            (p / ".gitkeep").write_text("# CIL Local AI placeholder\n", encoding="utf-8")

        # 7. Compute SHA-256 for all packaged files
        for current_path, _, filenames in os.walk(staging_dir):
            for filename in filenames:
                file_path = Path(current_path) / filename
                rel_path = file_path.relative_to(staging_dir).as_posix()
                size = file_path.stat().st_size
                sha = compute_sha256(file_path)
                manifest_entries.append({
                    "path": rel_path,
                    "size_bytes": size,
                    "sha256": sha,
                })

        manifest = {
            "bundle_name": "cil-report-ai-airgapped-distribution",
            "version": "0.1.0",
            "created_at": datetime.now().isoformat(),
            "air_gapped": True,
            "external_network_prohibited": True,
            "total_files": len(manifest_entries),
            "files": sorted(manifest_entries, key=lambda x: x["path"]),
        }

        manifest_path = staging_dir / "bundle_manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        # 8. Optionally create zip archive
        zip_dest = self.output_dir / "cil-report-ai-v0.1.0-airgapped.zip"
        if create_zip:
            with zipfile.ZipFile(zip_dest, "w", zipfile.ZIP_DEFLATED) as zf:
                for current_path, _, filenames in os.walk(staging_dir):
                    for filename in filenames:
                        fp = Path(current_path) / filename
                        arcname = fp.relative_to(self.output_dir).as_posix()
                        zf.write(fp, arcname)

        return staging_dir, manifest


def main():
    parser = argparse.ArgumentParser(description="Build CIL Local AI Air-Gapped Offline Bundle")
    parser.add_argument("--output-dir", type=Path, default=Path("dist/offline_bundle"), help="Output directory")
    parser.add_argument("--no-zip", action="store_true", help="Skip creating zip archive")
    args = parser.parse_args()

    packager = OfflineBundlePackager(output_dir=args.output_dir)
    print(f"Building air-gapped distribution bundle in: {packager.output_dir}")
    bundle_path, manifest = packager.build_bundle(create_zip=not args.no_zip)
    print(f"Successfully packaged {manifest['total_files']} files into {bundle_path.name}")
    print(f"Manifest written to: {bundle_path / 'bundle_manifest.json'}")


if __name__ == "__main__":
    main()
