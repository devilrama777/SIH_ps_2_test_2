# Phase 37: Storage Management & Retention Lifecycle Controls

## 1. Overview
In strict compliance with **Section 37 (STORAGE MANAGEMENT)** of the *CIL Local AI Report Generator Master Implementation Specification*, Phase 37 establishes an autonomous, policy-driven storage lifecycle engine for managing local workstation disk resources across long-running report generation pipelines.

The storage subsystem tracks all artifact layers, enforces automated retention and quota pruning for intermediate artifacts, and implements non-negotiable security guardrails protecting confidential source data.

---

## 2. Tracked Artifact Categories
Section 37 specifies that the platform must systematically track and account for disk space across 7 primary categories:

| Category Identifier | Description | Workspace Directory | Cleanup Safety |
| :--- | :--- | :--- | :--- |
| `original_source` | Raw uploaded/scanned source documents (PDFs, spreadsheets, DOCX) | `sources/` | **NEVER AUTO-DELETED** |
| `processed_representation` | Normalized canonical document models (`.json`) | `canonical/` / `processed/` | Controlled retention |
| `ocr_result` | Raw OCR bounding boxes, character coordinates, and cached layouts | `ocr/` | Controlled retention |
| `structured_extraction` | Extracted numerical tables, financial statements, and balance sheets | `extractions/` | Controlled retention |
| `embeddings_indexes` | SQLite FTS5 index tables, lexical inverted indexes, vector graph data | `indexes/` | Controlled retention |
| `generated_report` | Compiled `ReportData` models and rendered PDF deliverables | `reports/` | Preserved deliverables |
| `temporary_render` | Ephemeral HTML templates, browser buffers, scratch render frames | `temp/` | **Safe to auto-clean** |

*Auxiliary and legacy categories (`canonical_cache`, `search_index`, `asset_catalog`, `render_temp`, `logs`, `reports`) remain fully supported for backward compatibility.*

---

## 3. Core Architectural Invariants

### 3.1 Strict Source Protection Invariant
> **Section 37 Invariant**: *Never delete original source data automatically unless explicitly authorized.*
- Any automated retention sweep (`apply_retention_policies`) unconditionally skips the `ORIGINAL_SOURCE` category.
- Calling `safe_purge_category(ArtifactCategory.ORIGINAL_SOURCE, ...)` unconditionally raises `PermissionError` (returning `HTTP 403 Forbidden` over the REST API).
- Calling `update_retention_rule` attempting to enable automated age or quota pruning on `ORIGINAL_SOURCE` raises `PermissionError`.

### 3.2 Explicit Source Deletion Protocol
Original source files may only be removed through explicit, single-file administrative action:
1. Operator requests authorization token: `GET /api/v1/storage/source-token/{file_path}`.
2. System produces a deterministic cryptographic confirmation token: `CONFIRM_DELETE_SOURCE_<SHA256[:16]>`.
3. Operator submits `POST /api/v1/storage/authorize-source-deletion` with the matching token, identity, and audit justification.
4. Action is committed and immutably written to the tamper-evident audit trail (`AuditEventType.CONFIG_CHANGE`).

### 3.3 Ephemeral Render Cleanup & Quota Management
- Ephemeral render files (`temporary_render`, `render_temp`) are eligible for automatic pruning based on configured `max_age_seconds` (default 24 hours).
- Categories with defined `max_bytes_quota` enforce LRU (least recently used) pruning by sorting file timestamps and deleting older artifacts until disk usage falls below quota, while honoring `preserve_minimum_count`.

---

## 4. REST API Surface

```
                               ┌───────────────────────────────────────────────┐
                               │       Storage Lifecycle & Retention API       │
                               └──────────────────────┬────────────────────────┘
                                                      │
         ┌───────────────────┬────────────────────────┼───────────────────────┬────────────────────┐
         │                   │                        │                       │                    │
         ▼                   ▼                        ▼                       ▼                    ▼
GET /storage/breakdown  GET /storage/policies    POST /storage/policies  POST /storage/cleanup/temp POST /storage/apply-policies
[Real-time disk usage   [Active retention rules  [Adjust retention &     [Purge scratch render      [Run automated retention
 per Section 37 layer]   & quota definitions]     quota thresholds]       buffers & HTML frames]     across safe categories]
```

- **`GET /api/v1/storage/breakdown`**: Returns file counts, byte consumption, human-readable sizes, and safety indicators across all 7 Section 37 categories.
- **`GET /api/v1/storage/policies`**: Lists active retention rules for all categories.
- **`POST /api/v1/storage/policies`**: Updates retention rules (`max_age_seconds`, `max_bytes_quota`, `preserve_minimum_count`).
- **`POST /api/v1/storage/cleanup/temp`**: Purges expired temporary render artifacts without touching sources or reports.
- **`POST /api/v1/storage/apply-policies`**: Evaluates and applies retention policies across specified categories (strictly skipping original sources).
- **`GET /api/v1/storage/source-token/{path}`**: Generates required authorization token for single-file source deletion.
- **`POST /api/v1/storage/authorize-source-deletion`**: Executes authorized removal of a source file with audit verification.
- **`POST /api/v1/storage/purge-category`**: Safe category purge requiring explicit `PURGE_<CATEGORY>` token (rejects `original_source` with 403).

---

## 5. Verification & Test Suite
The storage management system is validated by comprehensive tests in `tests/storage/`:
- `tests/storage/test_storage_lifecycle_management.py`:
  - `test_section_37_all_categories_tracked`: confirms all 7 Section 37 categories are tracked with correct disk metrics and safety flags.
  - `test_cleanup_temporary_artifacts_policy`: verifies dry-run and active cleanup of render buffers while source documents remain untouched.
  - `test_retention_policy_enforcement_and_quota_pruning`: verifies quota limits and LRU pruning on intermediate OCR caches.
  - `test_retention_policy_strictly_protects_original_sources`: ensures bulk policy application strictly skips `original_source`.
  - `test_explicit_source_deletion_with_authorization_token`: validates token verification, rejection of unauthorized attempts, and audit logging.
  - `test_storage_api_rest_endpoints`: validates all REST endpoints via FastAPI `TestClient`.
  - `test_api_authorize_source_deletion_flow`: end-to-end test of the authorized deletion workflow.
- `tests/storage/test_storage_api.py`: validates breakdown, temp cleanup, and 403 rejection of source purges.
- `tests/storage/test_storage_lifecycle.py`: validates core storage accounting and invariant enforcement.

**Test Results**: 14/14 tests passing (100% pass rate).
