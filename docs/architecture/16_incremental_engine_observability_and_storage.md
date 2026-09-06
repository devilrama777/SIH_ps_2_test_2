# Architecture Document 16: Incremental Engine, Failure Resilience, Storage Lifecycle & Observability

## 1. Context and Problem Statement
In large corporate reporting environments (such as compiling 300–400 page annual reports for Coal India Limited subsidiaries), two severe operational bottlenecks commonly emerge:
1. **The "Full Regeneration" Penalty (Section 28)**: If an accountant updates a single cell in an operational spreadsheet or amends a single paragraph of CSR prose, re-extracting the entire document corpus, re-running LLM prompts across 50 sections, and re-rendering a 400-page PDF from scratch incurs catastrophic latency (minutes to hours).
2. **Ephemeral Disk Bloat & Uncontrolled Storage (Section 36 & 37)**: Headless browser rendering, OCR rasterization buffers, scratch image resizing, and intermediate HTML representations rapidly consume disk space. Conversely, naive cleanup scripts risk deleting irreplaceable raw source scans.
3. **Information Leaks in IT Diagnostics (Section 34 & 35)**: When runtime errors occur, DevOps engineers require system diagnostic logs (Python versions, hardware telemetry, parser crashes). Exporting un-sanitized logs risks leaking confidential state enterprise coal data, insider financial metrics, or credential tokens outside the air-gapped security perimeter.

Phase 14 resolves all three challenges through a unified architectural subsystem.

---

## 2. Component Architecture

```
                    ┌──────────────────────────────────────────────┐
                    │            Desktop UI / REST API             │
                    └──────────────────────┬───────────────────────┘
                                           │
         ┌─────────────────────────────────┼─────────────────────────────────┐
         │                                 │                                 │
         v                                 v                                 v
┌───────────────────────────┐ ┌───────────────────────────┐ ┌───────────────────────────┐
│ Section Dependency Graph  │ │     Storage Lifecycle     │ │     Diagnostic Bundle     │
│       (Section 28)        │ │    Manager (Section 37)   │ │   Exporter (Section 35)   │
├───────────────────────────┤ ├───────────────────────────┤ ├───────────────────────────┤
│ • Bidirectional Mapping:  │ │ • Category Tracking:      │ │ • Platform & OS Telemetry │
│   section <-> source_uris │ │   - ORIGINAL_SOURCE (lock)│ │ • Scrubbing Engine:       │
│ • Transitive Invalidation │ │   - CANONICAL_CACHE       │ │   - Redact tokens/secrets │
│   closure calculation     │ │   - RENDER_TEMP (purge)   │ │   - Redact emails/IDs     │
│ • Surgical Regeneration:  │ │ • Safe 1-Click Prune:     │ │ • Standalone Zip Bundle:  │
│   regenerate dirty only   │ │   - Zero source data loss │ │   - SHA-256 Manifest      │
│   preserve clean cache    │ │   - Hardened guard logic  │ │   - Air-gap compliant     │
└───────────────────────────┘ └───────────────────────────┘ └───────────────────────────┘
```

---

## 3. Section-Level Dependency Graph & Incremental Invalidation (Section 28)

### 3.1 Mathematical Formulation
Let $\mathcal{S} = \{s_1, s_2, \dots, s_n\}$ be the set of report sections, and $\mathcal{D} = \{d_1, d_2, \dots, d_m\}$ be the set of source documents.
We construct an adjacency mapping:
$$\text{Dep}(s_i) = \{d \in \mathcal{D} \mid d \text{ cited in } s_i\}$$

Additionally, let $\mathcal{X} \subseteq \mathcal{S} \times \mathcal{S}$ denote inter-section summarizing dependencies (e.g. Executive Summary $s_{exec}$ synthesizes Operational Section $s_{prod}$ and Financial Section $s_{fin}$):
$$(s_{exec}, s_{prod}) \in \mathcal{X}, \quad (s_{exec}, s_{fin}) \in \mathcal{X}$$

When a set of source files $\Delta \mathcal{D} \subseteq \mathcal{D}$ changes, the initial set of directly dirtied sections is:
$$\mathcal{S}_{dirty}^{(0)} = \{s \in \mathcal{S} \mid \text{Dep}(s) \cap \Delta \mathcal{D} \neq \emptyset\}$$

The transitive closure of all dirty sections requiring regeneration is:
$$\mathcal{S}_{dirty}^{(k+1)} = \mathcal{S}_{dirty}^{(k)} \cup \{s \in \mathcal{S} \mid \exists u \in \mathcal{S}_{dirty}^{(k)} \text{ such that } (s, u) \in \mathcal{X}\}$$
Terminating when $\mathcal{S}_{dirty}^{(k+1)} = \mathcal{S}_{dirty}^{(k)}$.

### 3.2 Selective Re-synthesis
During incremental regeneration (`IncrementalReportEngine.regenerate_sections`):
1. For each $s \in \mathcal{S}_{dirty}$, a `PlannedSection` is constructed and sent to `SectionGenerator.generate_section_content()`.
2. For each $s \notin \mathcal{S}_{dirty}$, the existing `ReportSection` is retained verbatim from cache with zero AI inference cost.
3. The newly assembled `Report` is validated by `ValidationEngine.validate_report()` and timestamped with `last_incremental_update`.

---

## 4. Storage Lifecycle Management & Deletion Protection (Section 37)

The workspace strictly classifies files into non-overlapping categories:

| Category | Typical Directory | Retention Policy | Safe to Auto-Purge? |
| :--- | :--- | :--- | :--- |
| `ORIGINAL_SOURCE` | `data/workspace/sources/` | **Permanent / Immutable** | **NO (Strict Invariant)** |
| `CANONICAL_CACHE` | `data/workspace/canonical/` | Kept until re-extracted | Admin explicit |
| `SEARCH_INDEX` | `data/workspace/indexes/` | Rebuildable on demand | Admin explicit |
| `ASSET_CATALOG` | `data/workspace/assets/` | Preserved with metadata | Admin explicit |
| `RENDER_TEMP` | `data/workspace/temp/` | Ephemeral scratch buffers | **YES (Automated / 1-Click)** |
| `LOGS` | `data/workspace/audit_logs/`| Chained cryptographic trail | Preserved for compliance |
| `REPORTS` | `data/workspace/reports/` | Compiled deliverables | Preserved for records |

### Strict Protection Invariant
`StorageManager.safe_purge_category(ArtifactCategory.ORIGINAL_SOURCE, ...)` unconditionally raises `PermissionError("Violation of Section 37 Invariant: ORIGINAL_SOURCE cannot be purged")`. Original files can never be accidentally erased by cache maintenance routines.

---

## 5. Local Observability & Sanitized Diagnostic Exporter (Section 35)

### 5.1 Telemetry Logger (`ObservabilityManager`)
Records:
- Stage name (`EXTRACTION`, `OCR`, `INDEXING`, `PLANNING`, `GENERATION`, `VALIDATION`, `RENDER`, `INCREMENTAL_REGENERATION`).
- Duration (seconds with millisecond precision).
- Status (`SUCCESS`, `FAILED`, `WARNING`, `FALLBACK`).
- Document IDs and Job IDs.
- Rolling in-memory buffer (default 200 entries) with persistent JSONL append log (`diagnostic_telemetry.jsonl`).

### 5.2 Confidentiality-Preserving Sanitization
Before packing system diagnostics into a ZIP archive, `SanitizedDiagnosticExporter` applies pattern redactions:
1. `password`, `token`, `secret`, `api_key` values $\longrightarrow$ `[REDACTED]`.
2. `Bearer <jwt>` $\longrightarrow$ `Bearer [REDACTED]`.
3. Email addresses $\longrightarrow$ `[EMAIL_REDACTED]`.
4. 16-digit card / identifier patterns $\longrightarrow$ `[CARD_OR_ID_REDACTED]`.
5. Raw text/tabular cells from original documents are **omitted entirely**. Only system hardware, memory, execution stage timings, and sanitized stack traces are exported.

The resulting bundle is sealed with a cryptographic SHA-256 manifest:
```json
{
  "bundle_name": "diagnostic_bundle_20260906_163000.zip",
  "exported_at": "2026-09-06T11:00:00Z",
  "file_count": 5,
  "sanitization_applied": true,
  "airgap_certified": true
}
```

---

## 6. REST API Endpoints

| Method | Route | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/reports/incremental/invalidate` | Computes dirty vs clean sections given modified source paths. |
| `POST` | `/api/v1/reports/incremental/regenerate` | Surgically regenerates dirty sections and stitches back report. |
| `GET` | `/api/v1/storage/breakdown` | Returns disk consumption and file counts per artifact category. |
| `POST` | `/api/v1/storage/cleanup` | Purges expired temporary render files without touching sources. |
| `GET` | `/api/v1/observability/telemetry` | Retrieves recent telemetry events and stage duration averages. |
| `POST` | `/api/v1/observability/export-diagnostics` | Generates a sanitized diagnostic `.zip` archive. |
| `GET` | `/api/v1/observability/download-diagnostics/{file}` | Downloads the generated diagnostic ZIP package. |

---

## 7. Verification and Testing
- `tests/reports/test_incremental_engine.py`: Validates transitive dirty section calculation and surgical regeneration.
- `tests/storage/test_storage_lifecycle.py`: Confirms temporary file pruning and verifies source protection invariant.
- `tests/observability/test_diagnostic_exporter.py`: Confirms regex pattern redaction and ZIP bundle integrity.
- `tests/observability/test_observability_api.py`: Validates end-to-end REST lifecycle across all Phase 14 endpoints.
- Total test coverage: **125 passed out of 125 tests**.
