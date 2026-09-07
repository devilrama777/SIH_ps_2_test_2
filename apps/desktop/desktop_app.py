"""
MineIntel Native Desktop Application Runner.
Powered by Microsoft Edge WebView2 via pywebview.

Launches a dedicated, standalone Windows desktop application window with:
- Zero browser address bar / chrome
- Native window management (1360x860, resizable, dark theme)
- Automatic background server orchestration & clean lifecycle termination
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [desktop_app] %(message)s"
)
logger = logging.getLogger("desktop_app")

BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8765
SERVER_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}/"
HEALTH_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}/api/v1/system/info"


def is_backend_running(timeout: float = 1.0) -> bool:
    """Checks whether the local processing backend is already active."""
    try:
        req = urllib.request.Request(HEALTH_URL, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


def wait_for_backend(timeout_seconds: int = 15) -> bool:
    """Polls the backend until it responds or times out."""
    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        if is_backend_running(timeout=1.0):
            return True
        time.sleep(0.5)
    return False


def main() -> None:
    # Ensure workspace root is in sys.path
    repo_root = Path(__file__).resolve().parent.parent.parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    os.chdir(str(repo_root))

    server_process: subprocess.Popen | None = None

    # 1. Start backend if not already active
    if not is_backend_running(timeout=1.0):
        logger.info("Starting local processing backend service on %s...", SERVER_URL)
        server_cmd = [sys.executable, "-m", "apps.processing.server"]
        
        # On Windows, launch without popping an unwanted extra console
        creationflags = 0
        if sys.platform == "win32":
            creationflags = subprocess.CREATE_NO_WINDOW

        server_process = subprocess.Popen(
            server_cmd,
            cwd=str(repo_root),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags,
        )

        logger.info("Waiting for backend service to bind port %d...", BACKEND_PORT)
        if not wait_for_backend(timeout_seconds=15):
            logger.error("Failed to connect to backend processing server at %s", SERVER_URL)
            if server_process:
                server_process.terminate()
            sys.exit(1)
        logger.info("Backend service is online and healthy.")
    else:
        logger.info("Existing backend service detected on %s.", SERVER_URL)

    # 2. Configure Windows AppUserModelID for taskbar grouping & icon
    ico_path = repo_root / "icon" / "MineIntel.ico"
    if not ico_path.exists():
        ico_path = repo_root / "MineIntel.ico"
    if sys.platform == "win32":
        try:
            import ctypes
            # Must be set before any window is created so Windows Taskbar pins and identifies MineIntel
            app_id = "MineIntel.Corporate.Desktop.1.0"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
            logger.info("Windows AppUserModelID registered: %s", app_id)
        except Exception as ex:
            logger.warning("Could not set AppUserModelID: %s", ex)

    # 3. Import and configure native WebView2 window
    try:
        import webview
    except ImportError:
        logger.error("pywebview is not installed. Please run: pip install pywebview")
        if server_process:
            server_process.terminate()
        sys.exit(1)

    # Set dark theme background matching MineIntel theme (#090d16)
    window = webview.create_window(
        title="MineIntel — CIL Local AI Report Generator",
        url=SERVER_URL,
        width=1360,
        height=860,
        min_size=(1024, 700),
        resizable=True,
        text_select=True,
        background_color="#090d16",
        confirm_close=False,
    )

    def on_shown():
        try:
            if sys.platform == "win32" and ico_path.exists():
                import ctypes
                WM_SETICON = 0x0080
                ICON_SMALL = 0
                ICON_BIG = 1
                IMAGE_ICON = 1
                LR_LOADFROMFILE = 0x00000010

                ico_str = str(ico_path.resolve())
                h_icon_big = ctypes.windll.user32.LoadImageW(
                    None, ico_str, IMAGE_ICON, 32, 32, LR_LOADFROMFILE
                )
                h_icon_small = ctypes.windll.user32.LoadImageW(
                    None, ico_str, IMAGE_ICON, 16, 16, LR_LOADFROMFILE
                )

                hwnd = None
                if hasattr(window, "native") and window.native:
                    if hasattr(window.native, "Handle"):
                        hwnd = int(window.native.Handle.ToInt64())

                if not hwnd:
                    hwnd = ctypes.windll.user32.FindWindowW(None, "MineIntel — CIL Local AI Report Generator")

                if hwnd:
                    if h_icon_big:
                        ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, h_icon_big)
                    if h_icon_small:
                        ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, h_icon_small)
                    logger.info("Attached native taskbar and titlebar icon to HWND %s", hex(hwnd))
        except Exception as ex:
            logger.warning("Could not attach HWND icon: %s", ex)

    window.events.shown += on_shown

    def on_closed():
        logger.info("Desktop window closed by user. Initiating clean termination.")
        if server_process and server_process.poll() is None:
            logger.info("Stopping background processing server process [PID %d]...", server_process.pid)
            server_process.terminate()
            try:
                server_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                server_process.kill()

    window.events.closed += on_closed

    # 4. Start native GUI window with custom taskbar icon
    try:
        logger.info("Launching native desktop window (Microsoft Edge WebView2)...")
        icon_arg = str(ico_path.resolve()) if ico_path.exists() else None
        # On Windows, pywebview automatically utilizes the installed Edge Chromium WebView2 runtime
        webview.start(icon=icon_arg, private_mode=False)
    finally:
        if server_process and server_process.poll() is None:
            logger.info("Ensuring server termination on exit.")
            server_process.terminate()


if __name__ == "__main__":
    main()
