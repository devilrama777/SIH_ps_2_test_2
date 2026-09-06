# Phase 15 Architecture: Enterprise Report Orchestrator, One-Click Wizard & Organizational Connectors

## 1. Overview & Architectural Vision

The **CIL Local AI Report Generator** culminates in a unified, one-click enterprise report generation pipeline as specified in Sections 4.2, 33, 40, and 46 of the Master Implementation Specification.

Phase 13 integrates all 12 prior subsystems into a seamless corporate workflow:
```
+----------------------------------------------------------------------------------------------------+
|                         ENTERPRISE MASTER REPORT GENERATION PIPELINE                               |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|    [ 1. Discovery ]                                                                                |
|       Discovers confidential PDF, XLSX, DOCX, CSV, TXT, and PNG/JPG files via DataConnector        |
|                                       │                                                            |
|                                       ▼                                                            |
|    [ 2. Extraction ]                                                                               |
|       Extracts structured text, tables, and exact cell/page coordinates into CanonicalDocument     |
|                                       │                                                            |
|                                       ▼                                                            |
|    [ 3. Indexing ]                                                                                 |
|       Builds local SQLite FTS5 full-text & temporal search index with BM25 ranking                 |
|                                       │                                                            |
|                                       ▼                                                            |
|    [ 4. Planning ]                                                                                 |
|       Analyzes reference structures, discovers emergent operational topics, maps section evidence  |
|                                       │                                                            |
|                                       ▼                                                            |
|    [ 5. Generation ]                                                                               |
|       Synthesizes narratives, financial tables, and chart specs using Local AI Gateway & templates  |
|                                       │                                                            |
|                                       ▼                                                            |
|    [ 6. Validation ]                                                                               |
|       Executes 6D deterministic validation (numerical, temporal, provenance, structural, etc.)     |
|                                       │                                                            |
|                                       ▼                                                            |
|    [ 7. Asset Placement & PDF Rendering ]                                                          |
|       Perceptual hash deduplication, layout selection, headless Chromium/Playwright rendering      |
|                                       │                                                            |
|                                       ▼                                                            |
|    [ 8. Audit Logging & Authorized Upload ]                                                        |
|       SHA-256 hash chaining, formal human sign-off, and secure transmission to organizational DMS   |
|                                                                                                    |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Architectural Components

### 2.1 Enterprise Report Pipeline (`core.orchestrator.pipeline.EnterpriseReportPipeline`)
The master orchestrator coordinates the end-to-end autonomous lifecycle:
- Session management: persists session state to `data/workspace/pipeline_sessions/{session_id}.json`.
- Non-blocking execution: supports asynchronous background tasks via FastAPI `BackgroundTasks` with real-time polling.
- Stage-by-stage event logging: records detailed progress logs across all 8 pipeline phases.
- Quality metrics calculation: automatically invokes `QualityMetricCalculator` to evaluate Section 32 metrics (`source_coverage`, `provenance_coverage`, `unsupported_claim_rate`, `numerical_error_rate`).

### 2.2 Future Production Connectors (`core.connectors.future`)
Adhering strictly to Section 4.2 of the Master Plan, future production data sources plug into the unified `DataConnector` contract without modifying downstream processing:
1. **`NetworkShareConnector`**:
   Mounts corporate SMB / UNC paths (e.g. `\\cil-fileserver\reports\FY25`) using domain authentication and credential vault integration.
2. **`SharePointConnector`**:
   Connects to Microsoft SharePoint document libraries for corporate document synchronization.
3. **`CILApiConnector`**:
   Interfaces with internal CIL SAP/ERP microservices for direct quantitative data retrieval.

### 2.3 Dual-Authorization & Secure Corporate Upload (`core.connectors.upload.AuthorizedReportUploader`)
In strict adherence to Section 0 and Section 46:
- **Mandatory Human Sign-Off**: Prevents unauthorized automated transmission; requires explicit approval by a designated corporate authority (`approver_name`, `approval_notes`, timestamp).
- **Cryptographic Packaging**: Computes the SHA-256 digest of the final PDF report and outputs an immutable submission manifest (`.manifest.json`).
- **Audit Ledger Chaining**: Logs the `EXPORT_PDF` transmission event into the tamper-evident SHA-256 audit ledger.

---

## 3. Desktop UI: Interactive "New Report Wizard" (`NewReportWizardView.tsx`)

The Desktop UI introduces a modern 4-step wizard implementing Section 33's "New Report Flow":
- **Step 1: Setup & Configuration**: Subsidiary selector (CCL, NCL, SECL, MCL, etc.), financial year input, data source/connector selector, and corporate template style choice (Classic CIL vs Modern Corporate).
- **Step 2: Live Pipeline Execution**: Real-time progress bar (0% to 100%), stage badges, and an integrated terminal event stream display.
- **Step 3: Quality Audit & Document Review**: Score cards displaying Section 32 metrics, validation findings counter, and direct PDF artifact preview link.
- **Step 4: Formal Sign-Off & Corporate Upload**: Executive sign-off form, approval stamp, and one-click transmission to the authorized corporate repository.

---

## 4. REST API Surface

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/pipeline/start` | Initiates the unified 8-stage enterprise report generation session |
| `GET` | `/api/v1/pipeline/status/{session_id}` | Returns live session progress, stage logs, and quality metrics |
| `POST` | `/api/v1/pipeline/approve` | Formally signs and approves the generated report |
| `POST` | `/api/v1/pipeline/upload` | Transmits approved report to authorized corporate destination |
| `GET` | `/api/v1/connectors/available` | Lists available local and enterprise connector configurations |

---

## 5. Verification & Test Coverage

- `tests/orchestrator/test_enterprise_pipeline.py`: Validates end-to-end execution across all 8 stages from raw files to final PDF.
- `tests/orchestrator/test_pipeline_api.py`: Tests the REST API lifecycle including startup, status polling, unapproved upload rejection, approval, and authorized transmission.
- `tests/connectors/test_future_connectors.py`: Tests `NetworkShareConnector`, `SharePointConnector`, `CILApiConnector`, and `AuthorizedReportUploader`.
- Full project test suite: **114 passed out of 114 tests**.
