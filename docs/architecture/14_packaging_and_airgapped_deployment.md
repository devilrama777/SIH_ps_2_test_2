# Phase 14 Architecture: Packaging, Air-Gapped Deployment & Production Topology

## 1. Executive Overview

The **CIL Local AI Report Generator** is built to operate in strictly air-gapped, confidential organizational environments (e.g. Coal India Limited subsidiaries and regional headquarters) where zero internet connectivity is accessible or permitted.

Phase 12 completes the platform by delivering self-contained packaging, pre-flight environment diagnostics, cryptographic bundle verification, cross-platform launchers, and production deployment automation.

```
+----------------------------------------------------------------------------------------------------+
|                             AIR-GAPPED DISTRIBUTION & RUNTIME TOPOLOGY                             |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|    [ Offline Distribution Archive ]                                                                |
|       cil-report-ai-v0.1.0-airgapped.zip (Source + Dist Assets + bundle_manifest.json)              |
|                                                                                                    |
|                                       │ Unpack & Verify                                            |
|                                       ▼                                                            |
|    [ Cryptographic Integrity Verifier: installer.setup_offline ]                                    |
|       - Validates SHA-256 checksums of 100% of packaged files                                      |
|       - Initializes data/workspace/, data/indexes/, data/cache/, models/cache/                     |
|                                                                                                    |
|                                       │ Pre-flight Check                                           |
|                                       ▼                                                            |
|    [ Diagnostic Verifier: installer.verify_environment ]                                           |
|       - Python >= 3.11                                                                             |
|       - RAM >= 8 GB (16 GB recommended)                                                            |
|       - Free Disk >= 5 GB                                                                          |
|       - SQLite FTS5 extension functional                                                           |
|       - Document extraction dependencies present                                                   |
|       - Loopback binding check: 127.0.0.1 (Strict zero-cloud isolation)                            |
|                                                                                                    |
|                                       │ Launch                                                     |
|                                       ▼                                                            |
|    [ Local Runtime: run_desktop.bat / run_desktop.sh ]                                             |
|       ┌────────────────────────────────────────────────────────┐                                   |
|       │ Desktop UI: Tauri 2 / Vite React (Port 5173 / Native)  │                                   |
|       └───────────────────────────┬────────────────────────────┘                                   |
|                                   │ Local Loopback REST IPC                                        |
|       ┌───────────────────────────▼────────────────────────────┐                                   |
|       │ Python Processing Engine (FastAPI on 127.0.0.1:8000)   │                                   |
|       │ - SQLite FTS5 Indexer                                  │                                   |
|       │ - Canonical Document Extraction                        │                                   |
|       │ - Deterministic Validation Engine                      │                                   |
|       │ - Local AI Gateway (Llama.cpp / Gemma GGUF)            │                                   |
|       │ - Headless PDF Chromium Renderer                       │                                   |
|       │ - SHA-256 Hash Chained Audit Logger                    │                                   |
|       └────────────────────────────────────────────────────────┘                                   |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Packaging Architecture

### 2.1 Distribution Bundle Packager (`installer.package_offline_bundle`)
The bundle packager aggregates all required runtime assets without development caches:
- **Core Domain Logic**: `core/` (ingestion, extraction, retrieval, AI gateway, report planner, generation, deterministic validation, image catalog, rendering, security).
- **Processing Service**: `apps/processing/` (FastAPI local server and lifecycle managers).
- **Compiled Frontend Assets**: `apps/desktop/dist/` (pre-compiled HTML, CSS, JavaScript chunks ready for immediate offline execution).
- **Environment & Setup Scripts**: `installer/` (`verify_environment.py`, `setup_offline.py`).
- **One-Click Launchers**: `run_desktop.bat`, `run_server.bat`, `run_desktop.sh`, `run_server.sh`.

### 2.2 Cryptographic Bundle Manifest (`bundle_manifest.json`)
Every file in the distribution archive is indexed with its size and cryptographic SHA-256 checksum:
```json
{
  "bundle_name": "cil-report-ai-airgapped-distribution",
  "version": "0.1.0",
  "created_at": "2026-09-06T15:20:00.000000",
  "air_gapped": true,
  "external_network_prohibited": true,
  "total_files": 142,
  "files": [
    {
      "path": "core/security/audit_logger.py",
      "size_bytes": 4820,
      "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    }
  ]
}
```

---

## 3. Pre-Flight Diagnostics (`installer.verify_environment`)

Before booting or processing reports, the platform performs automated pre-flight diagnostics:

| Diagnostic Check | Requirement | Purpose |
|---|---|---|
| **Python Version** | `>= 3.11` | Ensures modern typing, performance enhancements, and pattern matching support |
| **System RAM** | `>= 8.0 GB` (16 GB rec) | Prevents OOM when parsing 400-page subsidiary annual reports and running local GGUF models |
| **Free Disk Space** | `>= 5.0 GB` (10 GB rec) | Allocates workspace for SQLite indexes, converted PDF page caches, and rendered artifacts |
| **SQLite FTS5** | Functional | Verifies full-text search virtual tables compile and match query tokens accurately |
| **Workspace Paths** | Verified / Created | Assures `data/workspace/`, `data/indexes/`, `data/cache/`, and `models/cache/` exist |
| **Doc Libraries** | Available | Checks `pymupdf` (fitz), `openpyxl`, `python-docx`, `pillow`, `fastapi`, `pydantic` |
| **Model Weight Cache** | Accessible | Confirms `models/cache/` path; falls back to deterministic local mock if weights unmounted |
| **Loopback Security** | Strictly Enforced | Verifies host is `127.0.0.1` and `allow_external_network=false` |

---

## 4. Hardware Sizing & Specifications

In strict adherence to Section 0 and Section 36 of the Master Implementation Plan:

| Resource | Minimum Specification | Recommended Specification |
|---|---|---|
| **Processor** | Intel Core i5 / AMD Ryzen 5 (4+ cores) | Intel Core i7 / AMD Ryzen 7 (8+ cores) |
| **Memory** | 8 GB DDR4 | 16 GB or 32 GB DDR4/DDR5 |
| **Storage** | 512 GB SSD (50 GB available) | 1 TB NVMe SSD (200 GB available) |
| **GPU (Optional)** | None (CPU-first llama.cpp quantized) | NVIDIA RTX 3050 / 4060 (4 GB - 8 GB VRAM) |
| **Operating System** | Windows 10/11 64-bit | Windows 11 64-bit / RHEL 8+ / Ubuntu 22.04+ |

---

## 5. Offline Installation Runbook (Air-Gapped Systems)

### Step 1: Transfer Distribution Archive
Copy `cil-report-ai-v0.1.0-airgapped.zip` to the target air-gapped machine via approved secure media (e.g. encrypted organizational USB).

### Step 2: Extract Archive
Extract the archive into the designated application folder:
```powershell
Expand-Archive -Path cil-report-ai-v0.1.0-airgapped.zip -DestinationPath C:\CIL_Report_AI
cd C:\CIL_Report_AI
```

### Step 3: Run Integrity & Setup Tool
Execute the offline setup utility:
```powershell
python setup_offline.py
```
This automatically:
1. Verifies SHA-256 checksums of all bundled files.
2. Initializes workspace folders (`data/workspace/`, `data/indexes/`, `data/cache/`, `models/cache/`).
3. Runs all pre-flight diagnostic checks.

### Step 4: Launch Platform
- **Windows**: Double-click `run_desktop.bat`
- **Linux/macOS**: Run `./run_desktop.sh`

The launcher starts the local processing service on `127.0.0.1:8000` and displays the desktop interface.

---

## 6. Security Sign-Off & Air-Gap Compliance

| Security Requirement | Implementation | Status |
|---|---|---|
| **Zero Cloud AI Leakage** | Local AI Gateway only; cloud endpoints permanently disabled | **COMPLIANT** |
| **Loopback Binding** | Service explicitly binds to `127.0.0.1` (no `0.0.0.0`) | **COMPLIANT** |
| **Credential Encryption** | Windows DPAPI with machine-salted AES-256 fallback | **COMPLIANT** |
| **Tamper-Evident Audit** | SHA-256 cryptographic hash-chained audit database | **COMPLIANT** |
| **Evidence Provenance** | Zero orphan claims; 100% coordinate-level citations verified | **COMPLIANT** |
