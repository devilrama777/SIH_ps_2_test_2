"""
Cross-Platform Installer Packaging & Distribution CLI — Section 38 and Section 44 (Step 29).

Generates production distribution packages across target operating systems:
1. Windows: Standalone portable runtime bundle and InnoSetup / NSIS installer specification.
2. Linux: Standard Debian package directory structure (.deb) and desktop launcher entry.
3. macOS: Application bundle (.app) layout with Info.plist and DMG creation script.
4. Cryptographic distribution manifest verifying all installer payloads.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import stat
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class InstallerPayload(BaseModel):
    """Metadata for a generated platform installer artifact."""
    target_os: str
    format_type: str
    artifact_path: str
    file_size_bytes: int
    sha256_checksum: str
    created_at: str = Field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))


class InstallerManifest(BaseModel):
    """Cryptographic manifest documenting all built platform packages."""
    bundle_name: str = "cil-local-report-generator-installers"
    version: str = "0.1.0"
    created_at: str = Field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
    artifacts: Dict[str, InstallerPayload] = Field(default_factory=dict)


class InstallerPackager:
    """
    Builds production installer distributions and packages for Windows, Linux, and macOS.
    """

    def __init__(
        self,
        repo_root: Optional[str] = None,
        output_dir: str = "dist/installers",
    ) -> None:
        self.repo_root = Path(repo_root) if repo_root else Path(__file__).resolve().parent.parent
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _compute_sha256(self, file_path: Path) -> str:
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def build_windows_package(self) -> InstallerPayload:
        """
        Builds standalone Windows distribution directory and InnoSetup compilation script.
        """
        win_dir = self.output_dir / "windows_x64"
        win_dir.mkdir(parents=True, exist_ok=True)

        # 1. Generate InnoSetup installer configuration script
        iss_path = win_dir / "setup_windows.iss"
        iss_content = f"""[Setup]
AppName=CIL Local AI Report Generator
AppVersion=0.1.0
DefaultDirName={{autopf}}\\CIL_Report_AI
DefaultGroupName=CIL Report AI
OutputDir=.
OutputBaseFilename=CIL_Report_AI_Setup_v0.1.0
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
DisableWelcomePage=no
PrivilegesRequired=lowest

[Files]
Source: "..\\..\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: ".venv,node_modules,.git,dist"

[Icons]
Name: "{{group}}\\CIL Local AI Report Generator"; Filename: "{{app}}\\run_desktop.bat"; WorkingDir: "{{app}}"
Name: "{{autodesktop}}\\CIL Report AI"; Filename: "{{app}}\\run_desktop.bat"; WorkingDir: "{{app}}"

[Run]
Filename: "{{app}}\\run_desktop.bat"; Description: "Launch CIL Local AI Report Generator"; Flags: nowait postinstall skipifsilent
"""
        iss_path.write_text(iss_content, encoding="utf-8")

        # 2. Windows Portable Launcher batch
        launcher_path = win_dir / "Install_And_Run.bat"
        launcher_content = """@echo off
setlocal
echo ======================================================================
echo   CIL Local AI Report Generator -- Windows Deployment Launcher
echo ======================================================================
cd /d "%~dp0..\\.."
call run_desktop.bat
"""
        launcher_path.write_text(launcher_content, encoding="utf-8")

        # 3. Zip payload
        zip_path = self.output_dir / "cil-report-ai-windows-x64-v0.1.0.zip"
        shutil.make_archive(str(zip_path.with_suffix("")), "zip", str(win_dir))

        return InstallerPayload(
            target_os="windows",
            format_type="inno_setup_and_portable_zip",
            artifact_path=str(zip_path),
            file_size_bytes=zip_path.stat().st_size,
            sha256_checksum=self._compute_sha256(zip_path),
        )

    def build_linux_deb_package(self) -> InstallerPayload:
        """
        Generates standard Debian package layout (.deb) and desktop launcher for Linux workstations.
        """
        deb_dir = self.output_dir / "cil-report-ai_0.1.0_amd64"
        debian_meta = deb_dir / "DEBIAN"
        bin_dir = deb_dir / "usr" / "bin"
        apps_dir = deb_dir / "usr" / "share" / "applications"
        opt_dir = deb_dir / "opt" / "cil-report-ai"

        for d in [debian_meta, bin_dir, apps_dir, opt_dir]:
            d.mkdir(parents=True, exist_ok=True)

        # 1. DEBIAN/control
        control_file = debian_meta / "control"
        control_content = """Package: cil-report-ai
Version: 0.1.0
Section: utils
Priority: optional
Architecture: amd64
Maintainer: Coal India Limited Enterprise AI Taskforce <ai-reports@coalindia.in>
Description: CIL Local AI Report Generator
 Cross-platform, air-gapped document intelligence and enterprise report generator
 for confidential Coal India subsidiary records.
"""
        control_file.write_text(control_content, encoding="utf-8")

        # 2. Desktop entry
        desktop_file = apps_dir / "cil-report-ai.desktop"
        desktop_content = """[Desktop Entry]
Name=CIL Local AI Report Generator
Comment=Air-gapped confidential report generator for CIL
Exec=/usr/bin/cil-report-ai
Icon=application-x-executable
Terminal=false
Type=Application
Categories=Office;Development;
"""
        desktop_file.write_text(desktop_content, encoding="utf-8")

        # 3. CLI wrapper in /usr/bin
        wrapper_file = bin_dir / "cil-report-ai"
        wrapper_content = """#!/usr/bin/env bash
set -e
cd /opt/cil-report-ai
exec ./run_desktop.sh "$@"
"""
        wrapper_file.write_text(wrapper_content, encoding="utf-8")

        # 4. Zip the debian directory package structure
        deb_zip = self.output_dir / "cil-report-ai_0.1.0_amd64.deb.zip"
        shutil.make_archive(str(deb_zip.with_suffix("")), "zip", str(deb_dir))

        return InstallerPayload(
            target_os="linux",
            format_type="debian_package_tree",
            artifact_path=str(deb_zip),
            file_size_bytes=deb_zip.stat().st_size,
            sha256_checksum=self._compute_sha256(deb_zip),
        )

    def build_macos_app_bundle(self) -> InstallerPayload:
        """
        Generates macOS Application Bundle (.app) layout and DMG packaging script.
        """
        app_dir = self.output_dir / "CIL Report AI.app"
        contents_dir = app_dir / "Contents"
        macos_bin_dir = contents_dir / "MacOS"
        res_dir = contents_dir / "Resources"

        for d in [contents_dir, macos_bin_dir, res_dir]:
            d.mkdir(parents=True, exist_ok=True)

        # 1. Info.plist
        plist_file = contents_dir / "Info.plist"
        plist_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>launcher.sh</string>
    <key>CFBundleIdentifier</key>
    <string>com.cil.reportai</string>
    <key>CFBundleName</key>
    <string>CIL Report AI</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>0.1.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>12.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
"""
        plist_file.write_text(plist_content, encoding="utf-8")

        # 2. Launcher script
        launcher_file = macos_bin_dir / "launcher.sh"
        launcher_content = """#!/usr/bin/env bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR/../../.."
./run_desktop.sh
"""
        launcher_file.write_text(launcher_content, encoding="utf-8")

        # 3. DMG script
        dmg_script = self.output_dir / "build_macos_dmg.sh"
        dmg_script_content = """#!/usr/bin/env bash
# macOS DMG packaging script
hdiutil create -volname "CIL Report AI" -srcfolder "CIL Report AI.app" -ov -format UDZO "CIL_Report_AI_v0.1.0.dmg"
"""
        dmg_script.write_text(dmg_script_content, encoding="utf-8")

        # 4. Zip app bundle
        app_zip = self.output_dir / "cil-report-ai-macos-v0.1.0.app.zip"
        shutil.make_archive(str(app_zip.with_suffix("")), "zip", str(app_dir))

        return InstallerPayload(
            target_os="macos",
            format_type="macos_app_bundle",
            artifact_path=str(app_zip),
            file_size_bytes=app_zip.stat().st_size,
            sha256_checksum=self._compute_sha256(app_zip),
        )

    def build_all_targets(self) -> InstallerManifest:
        """
        Builds all target platform packages and writes installer_manifest.json.
        """
        manifest = InstallerManifest()

        win_payload = self.build_windows_package()
        manifest.artifacts["windows_x64"] = win_payload

        linux_payload = self.build_linux_deb_package()
        manifest.artifacts["linux_amd64"] = linux_payload

        macos_payload = self.build_macos_app_bundle()
        manifest.artifacts["macos_universal"] = macos_payload

        manifest_path = self.output_dir / "installer_manifest.json"
        manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")

        logger.info(f"[+] All platform installer packages generated under {self.output_dir}")
        return manifest


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Cross-Platform Installer Packager")
    parser.add_argument("--output-dir", default="dist/installers", help="Target directory for installer outputs")
    args = parser.parse_args()

    packager = InstallerPackager(output_dir=args.output_dir)
    m = packager.build_all_targets()
    print(json.dumps(m.model_dump(), indent=2))
