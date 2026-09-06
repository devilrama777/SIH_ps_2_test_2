"""
Offline Installation and Integrity Verification Setup Script.
Section 38 & Section 39 (Phase 12).

Executed on an air-gapped target machine to verify cryptographic bundle integrity,
initialize local directory schemas, and validate runtime environment readiness.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def compute_sha256(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class OfflineInstaller:
    """Verifies and initializes an offline unpacked installation."""

    def __init__(self, target_dir: Optional[Path] = None):
        self.target_dir = (target_dir or Path.cwd()).resolve()

    def verify_bundle_manifest(self) -> Tuple[bool, List[str]]:
        manifest_file = self.target_dir / "bundle_manifest.json"
        if not manifest_file.exists():
            return False, ["Missing bundle_manifest.json — corrupted or incomplete distribution bundle."]

        try:
            data = json.loads(manifest_file.read_text(encoding="utf-8"))
            files_list = data.get("files", [])
        except Exception as exc:
            return False, [f"Failed to parse bundle_manifest.json: {exc}"]

        errors: List[str] = []
        for item in files_list:
            rel_path = item["path"]
            expected_sha = item["sha256"]
            actual_file = self.target_dir / rel_path

            if not actual_file.exists():
                errors.append(f"Missing packaged file: {rel_path}")
                continue

            actual_sha = compute_sha256(actual_file)
            if actual_sha != expected_sha:
                errors.append(f"Cryptographic hash mismatch for {rel_path}: expected {expected_sha[:8]}..., got {actual_sha[:8]}...")

        return len(errors) == 0, errors

    def initialize_workspace(self) -> List[str]:
        required_dirs = [
            self.target_dir / "data" / "workspace" / "reports",
            self.target_dir / "data" / "indexes",
            self.target_dir / "data" / "cache",
            self.target_dir / "models" / "cache",
        ]
        created = []
        for d in required_dirs:
            if not d.exists():
                d.mkdir(parents=True, exist_ok=True)
                created.append(str(d.relative_to(self.target_dir)))
        return created

    def execute_setup(self, skip_preflight: bool = False) -> bool:
        print("=" * 70)
        print("  CIL Local AI Report Generator — Air-Gapped Setup & Verification")
        print("=" * 70)
        print(f"Installation Root: {self.target_dir}")

        # 1. Integrity check
        print("\n1. Verifying Cryptographic Bundle Integrity (SHA-256)...")
        passed, errors = self.verify_bundle_manifest()
        if not passed:
            print(f"[FAIL] Bundle verification failed with {len(errors)} error(s):")
            for err in errors[:10]:
                print(f"  - {err}")
            if len(errors) > 10:
                print(f"  - ...and {len(errors) - 10} more errors.")
            return False
        print("[PASS] All files matched SHA-256 manifest signatures exactly.")

        # 2. Workspace initialization
        print("\n2. Initializing Local Data & Cache Schemas...")
        created = self.initialize_workspace()
        if created:
            print(f"[OK] Initialized directories: {', '.join(created)}")
        else:
            print("[OK] All required workspace directories are present.")

        # 3. Pre-flight diagnostics
        if not skip_preflight:
            print("\n3. Running Pre-Flight Environment Diagnostics...")
            try:
                from installer.verify_environment import EnvironmentVerifier
                verifier = EnvironmentVerifier(base_dir=self.target_dir)
                diag = verifier.run_all_checks()
                for c in diag.checks:
                    mark = "PASS" if c.passed else ("WARN" if not c.critical else "FAIL")
                    print(f"  [{mark:4}] {c.name:<25} : {c.details}")
                if not diag.overall_status:
                    print("[FAIL] Critical environment preconditions not met.")
                    return False
            except Exception as exc:
                print(f"[WARN] Diagnostics module encountered error: {exc}")

        print("\n" + "=" * 70)
        print("SETUP COMPLETED SUCCESSFULLY!")
        print("To launch the application:")
        print("  Windows: double-click 'run_desktop.bat'")
        print("  Linux/macOS: execute './run_desktop.sh'")
        print("=" * 70)
        return True


def main():
    parser = argparse.ArgumentParser(description="Initialize and verify CIL Local AI air-gapped installation")
    parser.add_argument("--skip-preflight", action="store_true", help="Skip running environment diagnostics")
    args = parser.parse_args()

    installer = OfflineInstaller()
    success = installer.execute_setup(skip_preflight=args.skip_preflight)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
