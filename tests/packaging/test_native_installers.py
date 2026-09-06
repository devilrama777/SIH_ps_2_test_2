"""
Tests for Phase 29: Cross-Platform Native Installers & Tauri Packaging.
Section 38 and Section 44 (Step 29) of Master Implementation Plan.
"""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from installer.build_installers import InstallerPackager, InstallerManifest


def test_windows_package_generation(tmp_path: Path):
    packager = InstallerPackager(output_dir=str(tmp_path))
    payload = packager.build_windows_package()

    assert payload.target_os == "windows"
    assert payload.file_size_bytes > 0
    assert len(payload.sha256_checksum) == 64
    assert Path(payload.artifact_path).exists()

    # Verify InnoSetup script created
    iss_file = tmp_path / "windows_x64" / "setup_windows.iss"
    assert iss_file.exists()
    assert "CIL Local AI Report Generator" in iss_file.read_text(encoding="utf-8")


def test_linux_deb_package_generation(tmp_path: Path):
    packager = InstallerPackager(output_dir=str(tmp_path))
    payload = packager.build_linux_deb_package()

    assert payload.target_os == "linux"
    assert payload.file_size_bytes > 0
    assert len(payload.sha256_checksum) == 64
    assert Path(payload.artifact_path).exists()

    # Verify control and desktop files
    control_file = tmp_path / "cil-report-ai_0.1.0_amd64" / "DEBIAN" / "control"
    desktop_file = tmp_path / "cil-report-ai_0.1.0_amd64" / "usr" / "share" / "applications" / "cil-report-ai.desktop"
    assert control_file.exists()
    assert desktop_file.exists()
    assert "Package: cil-report-ai" in control_file.read_text(encoding="utf-8")


def test_macos_app_bundle_generation(tmp_path: Path):
    packager = InstallerPackager(output_dir=str(tmp_path))
    payload = packager.build_macos_app_bundle()

    assert payload.target_os == "macos"
    assert payload.file_size_bytes > 0
    assert len(payload.sha256_checksum) == 64
    assert Path(payload.artifact_path).exists()

    # Verify Info.plist
    plist_file = tmp_path / "CIL Report AI.app" / "Contents" / "Info.plist"
    assert plist_file.exists()
    assert "com.cil.reportai" in plist_file.read_text(encoding="utf-8")


def test_build_all_targets_and_manifest(tmp_path: Path):
    packager = InstallerPackager(output_dir=str(tmp_path))
    manifest: InstallerManifest = packager.build_all_targets()

    assert len(manifest.artifacts) == 3
    assert "windows_x64" in manifest.artifacts
    assert "linux_amd64" in manifest.artifacts
    assert "macos_universal" in manifest.artifacts

    manifest_file = tmp_path / "installer_manifest.json"
    assert manifest_file.exists()
    data = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert data["version"] == "0.1.0"
