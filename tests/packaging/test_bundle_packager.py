"""
Unit tests for OfflineBundlePackager and OfflineInstaller.
Phase 12 (Section 38 & 39).
"""
import json
from pathlib import Path

import pytest

from installer.package_offline_bundle import OfflineBundlePackager, compute_sha256
from installer.setup_offline import OfflineInstaller


@pytest.fixture
def mock_repo_root(tmp_path: Path) -> Path:
    """Sets up a minimal mock repo structure for packaging tests."""
    repo = tmp_path / "mock_cil_repo"
    repo.mkdir()

    # Core files
    (repo / "core").mkdir()
    (repo / "core" / "__init__.py").write_text("# core init\n", encoding="utf-8")
    (repo / "core" / "sample.py").write_text("print('sample')\n", encoding="utf-8")

    # Apps
    (repo / "apps" / "processing").mkdir(parents=True)
    (repo / "apps" / "processing" / "__init__.py").write_text("# apps init\n", encoding="utf-8")

    # Installer
    (repo / "installer").mkdir()
    (repo / "installer" / "setup_offline.py").write_text("# setup script\n", encoding="utf-8")

    # Root files
    (repo / "pyproject.toml").write_text('[project]\nname="cil-report-ai"\n', encoding="utf-8")
    (repo / "README.md").write_text("# CIL Local AI\n", encoding="utf-8")
    (repo / "run_desktop.bat").write_text("@echo off\n", encoding="utf-8")
    (repo / "run_server.bat").write_text("@echo off\n", encoding="utf-8")
    (repo / "run_desktop.sh").write_text("#!/bin/bash\n", encoding="utf-8")
    (repo / "run_server.sh").write_text("#!/bin/bash\n", encoding="utf-8")

    return repo


def test_offline_bundle_packaging(mock_repo_root: Path, tmp_path: Path):
    output_dir = tmp_path / "out_bundles"
    packager = OfflineBundlePackager(root_dir=mock_repo_root, output_dir=output_dir)

    staging_dir, manifest = packager.build_bundle(create_zip=True)

    # Verify staging structure
    assert staging_dir.exists()
    assert (staging_dir / "bundle_manifest.json").exists()
    assert (staging_dir / "core" / "sample.py").exists()
    assert (staging_dir / "run_desktop.bat").exists()
    assert (staging_dir / "setup_offline.py").exists()

    # Verify manifest
    assert manifest["bundle_name"] == "cil-report-ai-airgapped-distribution"
    assert manifest["air_gapped"] is True
    assert manifest["total_files"] > 0
    assert any(f["path"] == "core/sample.py" for f in manifest["files"])

    # Verify zip archive
    zip_path = output_dir / "cil-report-ai-v0.1.0-airgapped.zip"
    assert zip_path.exists()
    assert zip_path.stat().st_size > 0


def test_offline_installer_verification_success(mock_repo_root: Path, tmp_path: Path):
    output_dir = tmp_path / "out_bundles"
    packager = OfflineBundlePackager(root_dir=mock_repo_root, output_dir=output_dir)
    staging_dir, _ = packager.build_bundle(create_zip=False)

    installer = OfflineInstaller(target_dir=staging_dir)
    passed, errors = installer.verify_bundle_manifest()

    assert passed is True
    assert len(errors) == 0

    # Test directory initialization
    created = installer.initialize_workspace()
    assert (staging_dir / "data" / "workspace" / "reports").exists()
    assert (staging_dir / "data" / "indexes").exists()
    assert (staging_dir / "data" / "cache").exists()
    assert (staging_dir / "models" / "cache").exists()

    # Test full execution
    success = installer.execute_setup(skip_preflight=True)
    assert success is True


def test_offline_installer_catches_tampering(mock_repo_root: Path, tmp_path: Path):
    output_dir = tmp_path / "out_bundles"
    packager = OfflineBundlePackager(root_dir=mock_repo_root, output_dir=output_dir)
    staging_dir, _ = packager.build_bundle(create_zip=False)

    # Tamper with a packaged file
    target_file = staging_dir / "core" / "sample.py"
    target_file.write_text("MALICIOUS_TAMPERED_CONTENT\n", encoding="utf-8")

    installer = OfflineInstaller(target_dir=staging_dir)
    passed, errors = installer.verify_bundle_manifest()

    assert passed is False
    assert len(errors) == 1
    assert "Cryptographic hash mismatch" in errors[0]
    assert "core/sample.py" in errors[0]


def test_offline_installer_missing_manifest(tmp_path: Path):
    empty_dir = tmp_path / "empty_install"
    empty_dir.mkdir()

    installer = OfflineInstaller(target_dir=empty_dir)
    passed, errors = installer.verify_bundle_manifest()

    assert passed is False
    assert "Missing bundle_manifest.json" in errors[0]
