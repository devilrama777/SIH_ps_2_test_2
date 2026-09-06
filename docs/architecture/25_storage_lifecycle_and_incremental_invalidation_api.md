# Architectural Record 25: Storage Lifecycle Management & Incremental Invalidation REST Endpoints

## Overview & Scope
Implements Section 37 (Storage Management & Retention Policies) and Section 28 (Section Dependency Graph & Incremental Invalidation Engine) REST APIs in `apps/processing/server.py`, harmonizing the frontend `DiagnosticsView.tsx` with backend operations on canonical port `8765`.

---

## Architecture & Invariants

```
                                      +---------------------------------------------+
                                      | DiagnosticsView.tsx (Port 8765)             |
                                      +---------------------------------------------+
                                                |                             |
                       GET /api/v1/storage/breakdown                          |
                       POST /api/v1/storage/cleanup                           |
                       POST /api/v1/storage/purge-category                    |
                                                |                             |
                                                v                             |
                         +-----------------------------+                      |
                         | StorageManager              |                      |
                         | (core/storage/lifecycle.py) |                      |
                         +-----------------------------+                      |
                         | - Track 7 categories:       |                      |
                         |   original_source [IMMUTABLE|                      |
                         |   canonical_cache           |                      |
                         |   search_index              |                      |
                         |   asset_catalog             |                      |
                         |   render_temp [CLEANABLE]   |                      |
                         |   logs                      |                      |
                         |   reports                   |                      |
                         +-----------------------------+                      |
                                                                              v
                                                   POST /api/v1/reports/incremental/invalidate
                                                                              |
                                                                              v
                                                         +------------------------------------------+
                                                         | SectionDependencyGraph                   |
                                                         | (core/reports/incremental_engine.py)     |
                                                         +------------------------------------------+
                                                         | - Computes dirty transitive closure      |
                                                         | - Preserves intact cached sections       |
                                                         +------------------------------------------+
```

### 1. Section 37 Storage Invariants
- **Original Source Protection**: `ORIGINAL_SOURCE` (`data/workspace/sources`) is marked with `is_safe_to_clean = False`. Any call to `POST /api/v1/storage/purge-category` specifying `original_source` is unconditionally rejected with **HTTP 403 Forbidden**.
- **Ephemeral Temp Cleanup**: Only `RENDER_TEMP` files are purged during routine automated or on-demand cleanup via `POST /api/v1/storage/cleanup`.
- **Confirmation Token Protection**: Purging non-source categories requires passing an explicit token matching `PURGE_<CATEGORY_NAME>`.
- **Audit Trail Logging**: Every cleanup or category purge triggers an immutable audit log entry via `AuditLogger` with event type `CONFIG_CHANGE`.

### 2. Section 28 Incremental Invalidation Endpoint
- `POST /api/v1/reports/incremental/invalidate`:
  - Accepts `report_data` (or `report_id`) and a list of `changed_sources`.
  - Parses direct citations and transitive dependency hierarchies (e.g., Executive Summary synthesizing operational and financial metrics).
  - Returns `total_sections`, `dirty_sections` (requiring surgical regeneration), `clean_sections` (retained from cache), and the serialized dependency graph.

---

## Verification Evidence
- **Automated Tests**:
  - `tests/storage/test_storage_api.py` (4 tests: breakdown reporting, dry-run cleanup, original source protection, invalid token rejection).
  - `tests/reports/test_incremental_invalidation_api.py` (2 tests: surgical dirty/clean section partitioning, unreferenced source handling).
- **Full Pytest Suite**: 179/179 tests passing (100% pass rate in 77.75s).
- **Frontend Build**: `apps/desktop` compiles cleanly with 0 TypeScript/bundler warnings (`npm.cmd run build` in 5.80s).
