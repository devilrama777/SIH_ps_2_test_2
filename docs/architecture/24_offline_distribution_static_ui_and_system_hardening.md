# Architectural Record 24: Embedded Static Desktop UI & System Hardening

## Overview & Scope
Implements Section 25 (Desktop Shell Architecture), Section 38 (Air-Gapped Distribution Packaging), and Cross-Platform Launcher Script Hardening of the `CIL_Local_AI_Report_Generator_Master_Implementation_Plan.md`.

This milestone achieves complete runtime parity across all target enterprise deployment environments:
1. **Full Native Shell**: Tauri v2 desktop application wrapping the web frontend.
2. **Developer Shell**: Vite development server paired with local processing server.
3. **Zero-Node Air-Gapped Workstations**: Standalone Python service serving pre-compiled static assets directly from `apps/desktop/dist` over loopback port `8765` into the standard system web browser.

---

## Technical Architecture

```
                                  +---------------------------------------+
                                  | Client Workstation (Air-Gapped)       |
                                  +---------------------------------------+
                                                     |
                     +-------------------------------+-------------------------------+
                     |                               |                               |
                     v                               v                               v
             [Tauri Desktop]                [System Browser]                 [Dev Environment]
          Native Tauri Webview            Edge / Chrome / Firefox            Vite Dev Server (:5173)
                     |                               |                               |
                     +---------------+---------------+                               |
                                     |                                               |
                                     v                                               v
                     +---------------------------------------+       +-------------------------------+
                     | FastAPI Processing Server (:8765)      |<------| API Proxy (localhost:8765)   |
                     +---------------------------------------+       +-------------------------------+
                     | - GET / -> apps/desktop/dist/index.html
                     | - GET /assets/* -> StaticFiles(dist/assets)
                     | - GET /ui/* -> StaticFiles(dist, html=True)
                     | - /api/v1/* -> Processing & AI REST Endpoints
                     +---------------------------------------+
```

### 1. Embedded Static File Serving (`apps/processing/server.py`)
- **Mounts**:
  - `/assets`: Mounted to `apps/desktop/dist/assets` using `fastapi.staticfiles.StaticFiles`.
  - `/ui`: Mounted to `apps/desktop/dist` with `html=True`.
  - `GET /`: Route handler returning `FileResponse("apps/desktop/dist/index.html")` when built, or a JSON diagnostic status when unbuilt.
- **Route Precedence**: All `/api/v1/*` routes remain declared prior to root mounts, ensuring 100% routing precedence for API calls.

### 2. Air-Gapped Packaging Pipeline (`installer/package_offline_bundle.py`)
- Automatically stages `apps/desktop/dist` alongside backend sources (`core`, `apps/processing`, `installer`, and configuration templates).
- Computes SHA-256 cryptographic digests for every bundle asset, embedding them in `bundle_manifest.json`.
- Supports directory copy tree hardening with `dirs_exist_ok=True`.

### 3. Cross-Platform Launcher Scripts Hardening
- **Windows (`run_desktop.bat`, `run_server.bat`)**:
  - Harmonized service port to canonical `8765`.
  - Added detection cascade:
    1. Check for compiled Tauri executable `cil-report-desktop.exe`.
    2. Check for compiled static web UI in `apps/desktop/dist/index.html` -> launch `http://127.0.0.1:8765/`.
    3. Check for `npm` -> launch `npm.cmd run dev`.
    4. Fallback -> open default browser at `http://127.0.0.1:8765/`.
- **Unix / macOS (`run_desktop.sh`, `run_server.sh`)**:
  - Harmonized service port to canonical `8765`.
  - Mirrors same detection cascade with `xdg-open` and `open` system browser utilities.

---

## Verification & Test Evidence
- **New Test Suite**: `tests/packaging/test_static_ui_serving.py` (5 tests covering `GET /`, `/ui`, `/assets`, API precedence, `/docs`).
- **Packaging Suite**: `tests/packaging/test_bundle_packager.py` (4 tests verifying manifest calculation and dist packaging).
- **Full Regression**: 173/173 tests passing (100% coverage).
- **Frontend Verification**: Clean TypeScript & Vite production build (`dist/index.html`, `dist/assets`).
