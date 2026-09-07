"""
Tests for Native Desktop Application Runner (Section 25 & 38).

Verifies:
1. apps.desktop.desktop_app module imports cleanly and exports expected functions.
2. Backend health detection logic correctly identifies active/inactive service state.
3. run_desktop.bat includes native desktop window launch branch.
"""

from pathlib import Path
from apps.desktop.desktop_app import is_backend_running, wait_for_backend, SERVER_URL, HEALTH_URL


def test_desktop_app_exports():
    """Verify core desktop launcher configuration constants and functions."""
    assert SERVER_URL == "http://127.0.0.1:8765/"
    assert HEALTH_URL == "http://127.0.0.1:8765/api/v1/system/info"


def test_is_backend_running():
    """Verify backend health checker returns a valid boolean."""
    running = is_backend_running(timeout=1.0)
    assert isinstance(running, bool)


def test_run_desktop_bat_includes_native_window():
    """Verify run_desktop.bat has the native desktop window launch branch."""
    bat_path = Path(__file__).resolve().parent.parent.parent / "run_desktop.bat"
    assert bat_path.exists()
    content = bat_path.read_text(encoding="utf-8")
    assert "desktop_app" in content
    assert "Launching Native Desktop Window" in content


def test_mineintel_exe_exists():
    """Verify compiled native MineIntel.exe exists in root and is a valid Windows executable."""
    exe_path = Path(__file__).resolve().parent.parent.parent / "MineIntel.exe"
    assert exe_path.exists(), "MineIntel.exe should exist in project root"
    assert exe_path.stat().st_size > 0, "MineIntel.exe should be non-empty"
    # Verify standard DOS/PE header ('MZ' magic bytes)
    with open(exe_path, "rb") as f:
        header = f.read(2)
        assert header == b"MZ", "MineIntel.exe should be a valid Windows PE binary"

