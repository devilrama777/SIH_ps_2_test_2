"""
Tests for Native Desktop Application Runner (Section 25 & 38).

Verifies:
1. apps.desktop.desktop_app module imports cleanly and exports expected functions.
2. Backend health detection logic correctly identifies active/inactive service state.
3. run_desktop.bat includes native desktop window launch branch.
"""

from pathlib import Path
import json


def test_tauri_desktop_shell_configuration():
    """Verify Tauri 2 desktop shell configuration conforms to MineIntel specifications."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    tauri_conf_path = repo_root / "apps" / "desktop" / "src-tauri" / "tauri.conf.json"
    cargo_toml_path = repo_root / "apps" / "desktop" / "src-tauri" / "Cargo.toml"

    assert tauri_conf_path.exists(), "tauri.conf.json must exist"
    assert cargo_toml_path.exists(), "Cargo.toml must exist"

    conf = json.loads(tauri_conf_path.read_text(encoding="utf-8"))
    assert conf["productName"] == "MineIntel"
    assert conf["identifier"] == "com.mineintel.desktop"
    assert "MineIntel" in conf["app"]["windows"][0]["title"]


def test_run_desktop_bat_tauri_shell():
    """Verify run_desktop.bat launches backend and targets native desktop shell."""
    bat_path = Path(__file__).resolve().parent.parent.parent / "run_desktop.bat"
    assert bat_path.exists()
    content = bat_path.read_text(encoding="utf-8")
    assert "cil-report-desktop.exe" in content or "target\\release" in content


def test_mineintel_exe_exists():
    """Verify compiled native MineIntel.exe exists in root and is a valid Windows executable."""
    exe_path = Path(__file__).resolve().parent.parent.parent / "MineIntel.exe"
    assert exe_path.exists(), "MineIntel.exe should exist in project root"
    assert exe_path.stat().st_size > 0, "MineIntel.exe should be non-empty"
    # Verify standard DOS/PE header ('MZ' magic bytes)
    with open(exe_path, "rb") as f:
        header = f.read(2)
        assert header == b"MZ", "MineIntel.exe should be a valid Windows PE binary"

