"""
Turnkey Production Release & Offline Packaging Pipeline.
Compiles desktop assets, exports signed production certificate, packages air-gapped distribution artifacts,
and computes cryptographic SHA-256 manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("release_builder")


def compute_sha256(file_path: Path) -> str:
    """Computes hexadecimal SHA-256 digest of a file in 64 KB chunks."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


class ProductionReleaseBuilder:
    """Orchestrates turnkey offline release bundling for Coal India Limited."""

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root.resolve()
        self.dist_release_dir = self.repo_root / "dist" / "production_release"

    def prepare_release(self) -> Dict[str, Any]:
        """Packages all release components into dist/production_release/."""
        logger.info("Initializing production release bundle at %s", self.dist_release_dir)
        self.dist_release_dir.mkdir(parents=True, exist_ok=True)

        # 1. Export production certificate
        sys.path.insert(0, str(self.repo_root))
        from core.orchestrator.production_readiness_audit import ProductionReadinessAuditor

        auditor = ProductionReadinessAuditor(workspace_root=self.repo_root)
        cert_path = self.dist_release_dir / "PRODUCTION_CERTIFICATE.json"
        auditor.export_certificate(output_path=cert_path)
        logger.info("Generated and verified Production Certificate at %s", cert_path)

        # 2. Package desktop UI build
        desktop_dist = self.repo_root / "apps" / "desktop" / "dist"
        target_ui = self.dist_release_dir / "desktop_ui"
        if desktop_dist.exists():
            if target_ui.exists():
                shutil.rmtree(target_ui)
            shutil.copytree(desktop_dist, target_ui)
            logger.info("Packaged Desktop UI bundle (%d files)", sum(1 for _ in target_ui.rglob("*.*")))
        else:
            logger.warning("Desktop build directory %s not found. Proceeding with headless payload.", desktop_dist)

        # 3. Package documentation records
        target_docs = self.dist_release_dir / "docs"
        if target_docs.exists():
            shutil.rmtree(target_docs)
        shutil.copytree(self.repo_root / "docs" / "architecture", target_docs)
        logger.info("Packaged Architecture Specifications (%d documents)", len(list(target_docs.glob("*.md"))))

        # 4. Generate RELEASE_MANIFEST.sha256
        manifest_entries: List[Dict[str, Any]] = []
        manifest_file = self.dist_release_dir / "RELEASE_MANIFEST.sha256"

        with open(manifest_file, "w", encoding="utf-8") as mf:
            for item in sorted(self.dist_release_dir.rglob("*.*")):
                if item == manifest_file or item.name == "release_summary.json":
                    continue
                rel_p = item.relative_to(self.dist_release_dir).as_posix()
                digest = compute_sha256(item)
                size_bytes = item.stat().st_size
                mf.write(f"{digest}  {rel_p}\n")
                manifest_entries.append({
                    "path": rel_p,
                    "sha256": digest,
                    "size_bytes": size_bytes,
                })

        logger.info("Computed SHA-256 checksums for %d release artifacts.", len(manifest_entries))

        summary = {
            "status": "SUCCESS",
            "release_directory": str(self.dist_release_dir),
            "manifest_file": str(manifest_file),
            "total_artifacts": len(manifest_entries),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%SZ", time.gmtime()),
        }

        with open(self.dist_release_dir / "release_summary.json", "w", encoding="utf-8") as sf:
            json.dump(summary, sf, indent=2)

        return summary

    def verify_release(self) -> bool:
        """Validates all artifacts in dist/production_release/ against RELEASE_MANIFEST.sha256."""
        manifest_file = self.dist_release_dir / "RELEASE_MANIFEST.sha256"
        if not manifest_file.exists():
            logger.error("Manifest file %s not found.", manifest_file)
            return False

        all_ok = True
        with open(manifest_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                expected_hash, rel_path = line.split("  ", 1)
                target_file = self.dist_release_dir / rel_path
                if not target_file.exists():
                    logger.error("Missing artifact: %s", rel_path)
                    all_ok = False
                    continue
                actual_hash = compute_sha256(target_file)
                if actual_hash != expected_hash:
                    logger.error("Checksum mismatch for %s: expected %s, got %s", rel_path, expected_hash, actual_hash)
                    all_ok = False

        if all_ok:
            logger.info("Release manifest verification passed with 100% cryptographic integrity.")
        return all_ok


def main() -> None:
    parser = argparse.ArgumentParser(description="Build or verify CIL Production Release Bundle")
    parser.add_argument("--verify", action="store_true", help="Verify release checksum integrity")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    builder = ProductionReleaseBuilder(repo_root=repo_root)

    if args.verify:
        ok = builder.verify_release()
        sys.exit(0 if ok else 1)
    else:
        summary = builder.prepare_release()
        print(json.dumps(summary, indent=2))
        ok = builder.verify_release()
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
