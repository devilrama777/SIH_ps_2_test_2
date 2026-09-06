# Phase 38: Unified Local Installation & Runtime Provisioning Architecture

## 1. Overview
In strict compliance with **Section 38 (INSTALLATION)** of the *CIL Local AI Report Generator Master Implementation Specification*, Phase 38 implements the comprehensive local installation and runtime provisioning architecture.

The platform establishes a zero-assumption deployment model for air-gapped target environments:
```text
Application
+
Python/runtime dependencies
+
document-processing dependencies
+
local model runtime
+
selected model files
```

---

## 2. Five-Tier Runtime Stack

| Tier | Component Identifier | Description & System Scope | Preflight Verification Check |
| :--- | :--- | :--- | :--- |
| **1** | `application` | Desktop UI shell (`apps/desktop/dist`) + FastAPI backend server (`apps/processing/server.py`). | Evaluates bundle existence, distribution build presence, and port availability. |
| **2** | `python_runtime` | Isolated Python 3.11–3.13 runtime with pre-cached wheels, avoiding any host dependency. | Verifies runtime virtual environment, core dependencies (`fastapi`, `pydantic`, `uvicorn`). |
| **3** | `document_processing` | PDF parsers (`pymupdf`), document converters (`docx`, `openpyxl`), and rendering engines (Headless Chromium / PyMuPDF). | Checks import availability and rendering engine capabilities. |
| **4** | `model_runtime` | Local model inference engine (`llama-cpp-python` / `llama.cpp` binary) + deterministic rule-based fallback. | Verifies native library bindings or activates deterministic local fallback engine. |
| **5** | `model_files` | Quantized GGUF model weights stored locally in `models/` directory. | Scans directory for valid `.gguf` files and verifies SHA-256 signatures against catalog. |

---

## 3. Model Provisioning & Licensing Governance

Section 38 explicitly mandates:
> *"The model should be installable/downloadable as part of the application's setup process, subject to the model's licensing/distribution requirements."*

### 3.1 Approved Model Catalog
The system maintains an authoritative catalog of approved models:
1. **Qwen 2.5 1.5B Instruct (Q4_K_M)**:
   - Size: ~1.09 GB GGUF
   - License: Apache-2.0
   - Target: Standard CPU-first execution, 4–8 GB RAM laptops.
2. **Mistral 7B Instruct v0.2 (Q4_K_M)**:
   - Size: ~4.37 GB GGUF
   - License: Apache-2.0
   - Target: Standard balanced report generation, 8–16 GB RAM workstations.
3. **Gemma 2 9B Instruct (Q4_K_M)**:
   - Size: ~5.84 GB GGUF
   - License: Gemma Terms of Use (mandatory acknowledgement)
   - Target: High-throughput narrative generation, 16 GB+ RAM systems.

### 3.2 Provisioning Modes
- **Offline Air-Gapped Import**:
  Operators import GGUF model files directly from local storage, external USB drives, or local network folders via `POST /api/v1/installation/models/import-offline`. The system cryptographically validates the file against the catalog SHA-256 hash before registering it.
- **Setup-Time Download**:
  When internet connectivity is permitted during initial workstation commissioning, operators can trigger model downloads via `POST /api/v1/installation/models/download`. The endpoint strictly enforces `accept_license: true`; requests omitting license acceptance are rejected with `HTTP 403 Forbidden`.

---

## 4. REST API Surface

```
                               ┌───────────────────────────────────────────────┐
                               │     Installation & Model Provisioning API     │
                               └──────────────────────┬────────────────────────┘
                                                      │
         ┌───────────────────┬────────────────────────┼───────────────────────┬────────────────────┐
         │                   │                        │                       │                    │
         ▼                   ▼                        ▼                       ▼                    ▼
GET /installation/status GET /models/catalog    POST /models/import-offline  POST /models/download POST /models/activate
[5-tier readiness state  [Approved GGUF catalog  [Import GGUF from local disk [Download model with  [Switch active model
 & missing requirements]  & license metadata]     with SHA-256 verification]   license acceptance]   for AI Gateway]
```

- **`GET /api/v1/installation/status`**: Complete 5-tier diagnostic status report.
- **`GET /api/v1/installation/models/catalog`**: List of catalog models with license terms, sizes, RAM requirements, and install status.
- **`POST /api/v1/installation/models/import-offline`**: Imports local model weights with SHA-256 verification.
- **`POST /api/v1/installation/models/download`**: Provisions model with mandatory license acceptance check.
- **`POST /api/v1/installation/models/activate`**: Sets active model for the AI Gateway.
- **`POST /api/v1/installation/verify-runtimes`**: Triggers a live preflight check across all 5 tiers.

---

## 5. Verification & Test Suite
Validated by [`tests/installation/test_installation_runtime_provisioning.py`](file:///c:/Rama/SIH_hackathon/SIH_MINE_INTEL/tests/installation/test_installation_runtime_provisioning.py):
- `test_verify_5_installation_tiers`: Verifies readiness inspection across all 5 tiers.
- `test_model_catalog_and_status`: Validates catalog models, licensing URLs, and memory requirements.
- `test_model_download_license_enforcement`: Asserts 403 / PermissionError when license is not accepted, and success when accepted.
- `test_offline_model_import_with_checksum_verification`: Validates successful SHA-256 import and rejection of corrupted model files.
- `test_model_activation`: Verifies active model switching and error handling for uninstalled models.
- `test_installation_rest_api_endpoints`: Validates all REST endpoints via FastAPI `TestClient`.

**Test Results**: 6/6 tests passing (100% pass rate).
