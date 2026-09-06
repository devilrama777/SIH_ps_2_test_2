# Phase 15 Architecture: Unified Settings, Section 40 Vertical Slice & Document Normalization

## 1. Overview & Architectural Vision

Phase 15 completes three core operational mandates defined in the **CIL Local AI Report Generator Master Implementation Specification**:
1. **Unified Application Settings & Subsidiary Configuration Management (Sections 24 & 33)**:
   A thread-safe, atomic configuration system (`core.settings.manager.SettingsManager`) and interactive desktop UI (`SettingsView.tsx`) allowing runtime governance over:
   - Subsidiary corporate profiles (CCL, BCCL, ECL, SECL, WCL, NCL, MCL, CMPDIL, CIL Apex HQ).
   - Local AI inference engine parameters (context windows, thread counts, temperature, llama.cpp GGUF paths, and GPU layer offload).
   - Air-gapped security baselines (strict local loopback 127.0.0.1, default-deny network enforcement, and cryptographic audit retention).
   - Storage lifecycle policies (cache lifespan, scratch pruning intervals, and deletion protection invariants).
   - Report styling and typography defaults (Classic CIL vs Modern Corporate).
2. **Section 40: Autonomous First Vertical Slice Orchestration**:
   An end-to-end pipeline runner (`core.orchestrator.vertical_slice.VerticalSliceRunner`) executing the complete autonomous workflow across 10–20 representative multi-format files (scanned/digital PDF, DOCX, XLSX, TXT, CSV, PNG):
   $$\text{Files} \longrightarrow \text{Extraction} \longrightarrow \text{Normalization} \longrightarrow \text{FTS5 Index} \longrightarrow \text{Planning} \longrightarrow \text{5–10 Page Report} \longrightarrow \text{Provenance} \longrightarrow \text{Agentic Review} \longrightarrow \text{Validation} \longrightarrow \text{Dual PDF}$$
3. **Section 8: Document Normalization & LLM Markdown Layer**:
   A dedicated normalization component (`core.extraction.normalizer.DocumentNormalizer`) that transforms `CanonicalDocument` structures into LLM-optimized Markdown with embedded HTML provenance anchors (`<!-- provenance: doc=... page=... el=... -->`).

---

## 2. Component Architecture

```
                               ┌──────────────────────────────────────────────┐
                               │           Desktop UI (SettingsView)          │
                               └──────────────────────┬───────────────────────┘
                                                      │ REST API
                                                      v
                               ┌──────────────────────────────────────────────┐
                               │            FastAPI Local Server              │
                               └───────┬──────────────────────────────┬───────┘
                                       │                              │
                    ┌──────────────────┴───────────────┐              │
                    v                                  v              v
       ┌─────────────────────────┐        ┌─────────────────────────┐  ┌─────────────────────────┐
       │     SettingsManager     │        │   VerticalSliceRunner   │  │   DocumentNormalizer    │
       │     (Section 24/33)     │        │       (Section 40)      │  │       (Section 8)       │
       ├─────────────────────────┤        ├─────────────────────────┤  ├─────────────────────────┤
       │ • Atomic JSON storage   │        │ • 10-20 file corpus     │  │ • Canonical -> Markdown │
       │ • 9 CIL Subsidiaries    │        │ • End-to-end 9 stages   │  │ • Provenance comments   │
       │ • AI thread/GPU bounds  │        │ • Simulated human review│  │ • GFM table grids       │
       │ • Loopback airgap guard │        │ • Dual-template PDFs    │  │ • Disk caching          │
       │ • Audit log integration │        │ • Section 32 metrics    │  │ • LLM context feeding   │
       └─────────────────────────┘        └─────────────────────────┘  └─────────────────────────┘
```

---

## 3. Configuration & Subsidiary Profile Subsystem (Section 24 & 33)

### 3.1 Domain Model Structure (`core.domain.settings`)
The configuration schema is strictly typed via Pydantic:
- **`SubsidiaryProfile`**:
  - `code`: Subsidiary acronym (e.g. `CCL`, `NCL`, `BCCL`).
  - `full_name`: Official enterprise entity name.
  - `headquarters`: Registered headquarters address.
  - `default_financial_year`: Primary target accounting period.
  - `currency_unit`: Financial reporting denomination (`INR Crores`).
  - `statutory_mandate_csr_percent`: Statutory CSR mandate percentage (2.0%).
- **`AISettings`**:
  - `active_backend`: `rule_based`, `llama_cpp`, or `local_server`.
  - `model_name`: Active model identifier (e.g. `Gemma-2-9B-It-Q4_K_M`, `Llama-3.1-8B-Instruct`).
  - `context_window_tokens`: 2,048 to 32,768 tokens.
  - `max_output_tokens`: 256 to 4,096 tokens.
  - `temperature`: 0.0 to 1.0 (defaults to 0.2 for deterministic precision).
  - `cpu_threads`: 1 to 32 cores.
  - `gpu_offload_layers`: 0 to 99 layers (0 for CPU-first operation).
- **`SecuritySettings`**:
  - `strict_local_loopback`: Enforces binding solely to 127.0.0.1.
  - `allow_external_network`: Default-deny outbound internet access.
  - `audit_log_retention_days`: Cryptographic audit trail lifespan (365 days).
  - `require_dual_authorization_export`: Enforces formal executive sign-off.
- **`StorageSettings`**:
  - `cache_retention_days`: Lifespan for parsed canonical models (30 days).
  - `temp_auto_prune_interval_hours`: Auto-cleanup frequency for scratch render files (24 hours).
  - `dry_run_safety_lock`: Simulates pruning without filesystem modifications.
- **`TemplateSettings`**:
  - `default_visual_mode`: `modern` or `classic`.
  - `brand_primary_color`: CIL Navy Blue (`#0B3C5D`).
  - `brand_secondary_color`: CIL Gold (`#D97706`).

### 3.2 Atomic Persistence
`SettingsManager` uses atomic file replacement (`.tmp` $\longrightarrow$ `.replace()`) to eliminate race conditions and partial writes, persisting to `data/workspace/app_settings.json`. All updates generate tamper-evident audit logs via `AuditLogger`.

---

## 4. Section 40: First Vertical Slice Autonomous Pipeline

### 4.1 Objective & Pre-condition
Before initiating massive 400-page subsidiary reports, Section 40 mandates a complete, reproducible vertical slice executing across 10–20 representative source files.

### 4.2 Pipeline Stages
`VerticalSliceRunner.run_vertical_slice()` executes ten orchestrated stages:
1. **Corpus Preparation & Discovery**: Ensures 12 multi-format representative files exist in `vertical_slice_corpus/` (scanned PDF, digital PDF, DOCX, XLSX, TXT, CSV, PNG). Discovers files via `LocalFolderConnector`.
2. **Multi-Format Structured Extraction**: Extracts text, tables, coordinates, and images via `UnifiedDocumentExtractor` into `CanonicalDocument` models.
3. **Markdown Normalization**: Converts canonical documents into clean Markdown with embedded provenance anchors via `DocumentNormalizer`.
4. **SQLite FTS5 Hybrid Indexing**: Indexes text elements and metadata into SQLite FTS5 with BM25 full-text ranking via `DocumentIndexer`.
5. **Dynamic Report Planning**: Maps current-year evidence to standard CIL chapters targeting a 5–10 page report structure via `ReportPlanner` and `EvidenceToSectionMapper`.
6. **Section Content Generation**: Synthesizes narratives, tables, and provenance references via `MasterReportGenerator`.
7. **Initial Validation**: Executes deterministic 6D validation (numerical, temporal, provenance, structural, visual, links).
8. **Human Review & Agentic Correction**: Verifies the human-in-the-loop review workflow via `ReportEditingAgent`, proposing an amendment to an operational section, generating a diff, applying the change upon approval, and re-validating.
9. **Dual-Template PDF Rendering**: Renders both Template A (Classic CIL) and Template B (Modern Corporate) via `PdfRenderer`.
10. **Section 32 Quality Audit**: Evaluates and records key quality metrics:
    - `source_coverage`: $\ge 90\%$
    - `provenance_coverage`: $\ge 80\%$
    - `unsupported_claim_rate`: $\le 5\%$
    - `numerical_error_rate`: $0.0\%$

---

## 5. Document Normalization Subsystem (Section 8)

Section 8 specifies:
$$\text{Raw Documents} \longrightarrow \text{Canonical Structured Model} + \text{Markdown Representation}$$

`DocumentNormalizer` satisfies this by generating structured Markdown files where:
- Headings maintain standard hierarchy (`#`, `##`, `###`).
- Tables are transformed into GitHub Flavored Markdown (GFM) grids with header dividers.
- Image elements embed metadata captions and asset references.
- Provenance anchors are preserved as non-rendered HTML comments:
  ```html
  <!-- provenance: doc=doc_0042 page=3 el=el_009821 type=paragraph -->
  ```
- Cached under `data/workspace/normalized/{doc_id}.md` for rapid LLM context injection without re-parsing raw binaries.

---

## 6. REST API Surface

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/settings` | Retrieves current application configuration |
| `POST` | `/api/v1/settings` | Updates configuration with validation & audit logging |
| `POST` | `/api/v1/settings/reset` | Restores factory CIL defaults |
| `GET` | `/api/v1/settings/subsidiaries` | Enumerates recognized Coal India subsidiaries |
| `POST` | `/api/v1/settings/subsidiaries/select` | Switches active subsidiary profile |
| `POST` | `/api/v1/pipeline/vertical-slice` | Executes Section 40 autonomous first vertical slice |
| `POST` | `/api/v1/documents/normalize` | Generates and caches secondary Markdown for a canonical document |

---

## 7. Verification & Test Coverage

- `tests/settings/test_settings_api.py`: Validates settings initialization, bounds validation, subsidiary switching, default recovery, and REST API endpoints.
- `tests/extraction/test_document_normalizer.py`: Validates conversion from canonical model to GFM markdown with provenance comment tags and disk caching.
- `tests/orchestrator/test_vertical_slice.py`: Validates the end-to-end 10-20 file pipeline slice, human correction loop, dual PDF exports, and Section 32 quality metrics.
- Frontend build: `npm run build` in `apps/desktop` compiles with zero errors into production bundle.
