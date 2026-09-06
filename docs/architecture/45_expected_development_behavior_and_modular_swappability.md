# Section 45: Expected Development Behavior & Modular Swappability

## 1. Executive Summary
Section 45 of the **CIL Local AI Report Generator Master Implementation Specification** formalizes the engineering philosophy, component design standards, and decoupling contracts required for an enterprise-grade, air-gapped document intelligence and synthesis platform.

It explicitly mandates three foundational tenets:
1. **The 7-Point Architectural Inquiries** that must be answered and verified for every component prior to integration.
2. **The 5 Core Modular Swappability Contracts** ensuring critical subsystems (LLM, Connector, Template, Database, OCR) can be replaced or upgraded without rewriting unrelated parts.
3. **The Non-Negotiable Priority Hierarchy**:
   $$\mathbf{correctness > traceability > security > maintainability > performance > visual\ polish}$$

---

## 2. The 7-Point Component Architectural Inquiries
Before any software component is accepted into the CIL Report Engine, it must satisfy the 7 foundational inquiries:

| Inquiry | Requirement | Verification Standard in Engine |
|---|---|---|
| **1. Responsibility** | Single Responsibility Principle (SRP); well-bounded domain scope. | Strict domain model encapsulation with zero feature creep. |
| **2. Inputs** | Well-typed schemas, runtime validation, bounded parameters. | Pydantic `BaseModel`, Python 3.10+ type annotations, strict range validation. |
| **3. Outputs** | Canonical, deterministic data models with zero hallucination potential. | Canonical Document Element AST, IEEE floats, ISO timestamps. |
| **4. Dependencies** | Minimal, explicit, inverted dependencies via abstract base classes. | `ABC` interfaces, zero circular imports, zero cloud API SDKs. |
| **5. Failure Modes** | Documented failure modes, graceful degradation, and error isolation. | Multi-tier fallback (e.g., local server $\rightarrow$ direct in-process $\rightarrow$ rule-based fallback). |
| **6. Security** | 100% offline, air-gapped execution, input sanitization, safe file I/O. | Path traversal prevention, zero external egress sockets, sanitized JSON export. |
| **7. Test Strategy** | Automated unit, contract, integration, and regression verification. | High pytest coverage, interface contract assertions, regression benchmarks. |

---

## 3. The 5 Core Modular Swappability Contracts
The architecture achieves complete modular swappability through polymorphic interfaces:

```text
┌────────────────────────────────────────────────────────────────────────┐
│               5 Mission-Critical Decoupled Subsystems                  │
├────────────────────────────┬─────────────────────────────┬─────────────┤
│ Subsystem                  │ Default Implementation      │ Swap Target │
├────────────────────────────┼─────────────────────────────┼─────────────┤
│ 1. Local AI Inference      │ Gemma 2 9B (Local Server)   │ Fallback/   │
│                            │                             │ In-Process  │
│ 2. Data Ingestion          │ LocalFolderConnector        │ CIL Server  │
│                            │                             │ Connector   │
│ 3. Report Template         │ Classic Template (TemplateA)│ Modern (B)  │
│ 4. Metadata/Evidence DB    │ SQLite + FTS5               │ Analytical  │
│                            │ (ReportDatabase)            │ Database    │
│ 5. Layout & OCR Engine     │ PaddleOCR Engine            │ PyMuPDF /   │
│                            │                             │ Docling     │
└────────────────────────────┴─────────────────────────────┴─────────────┘
```

### 3.1 Inference Swappability (`LocalInferenceBackend`)
- **Abstract Base**: `core.ai.backends.base.LocalInferenceBackend`
- **Method Contract**: `generate(prompt, system_prompt, max_tokens, temperature) -> InferenceResult`
- **Decoupling Guarantee**: The report planner, section generator, and UI interact exclusively with `LocalInferenceBackend` or `LocalAIGateway`. Switching models (Gemma 2, Qwen 2.5, Llama 3, or deterministic heuristic fallback) requires zero changes to the citation provenance or report composition layers.

### 3.2 Ingestion Connector Swappability (`DataConnector`)
- **Abstract Base**: `core.connectors.base.DataConnector`
- **Method Contract**: `discover()`, `list_sources()`, `fetch_document()`, `fetch_metadata()`, `health_check()`
- **Decoupling Guarantee**: The extraction and normalization engines consume `SourceItem` models and byte streams. Whether documents come from a local directory or a future CIL corporate server, the downstream pipeline remains identical.

### 3.3 Report Styling Swappability (`ReportTemplate`)
- **Abstract Base**: `core.reports.pdf.html_builder.ReportHtmlBuilder`
- **Method Contract**: `build_html(report: Report, template_name: str) -> str`
- **Decoupling Guarantee**: Report models (`Report`, `ReportSection`, `ReportTable`) are pure domain objects. Templates provide CSS Paged Media stylesheets (`CLASSIC_CSS` vs `MODERN_CSS`). Hot-swapping templates alters only presentation and typography, never factual content or provenance links.

### 3.4 Evidence Database Swappability (`ReportDatabase`)
- **Abstract Base**: Relational & FTS interface in `core.retrieval.db.ReportDatabase`
- **Method Contract**: `get_connection()`, element CRUD, FTS5 lexical indexing, WAL journaling
- **Decoupling Guarantee**: Document extractors write to canonical schemas (`documents`, `pages`, `elements`, `tables`, `provenance`, `fts_elements`). The query and temporal search engines interact via standard SQL queries, allowing SQLite to be swapped for DuckDB, PostgreSQL, or an enterprise warehouse without altering retrieval orchestration.

### 3.5 OCR & Layout Intelligence Swappability (`BaseOCREngine`)
- **Abstract Base**: `core.extraction.ocr.base.BaseOCREngine`
- **Method Contract**: `process_page_image(image_bytes, page_number) -> OCRPageResult`
- **Decoupling Guarantee**: Managed by `MultiEngineOCRManager`. If PaddleOCR is unavailable or fails, execution seamlessly falls back to `PyMuPDFOCREngine` or `DoclingOCREngine` with zero changes to downstream text and table extractors.

---

## 4. The Inviolable Priority Hierarchy

In any architectural, algorithmic, or user experience conflict, decisions are made strictly according to the rank order:
1. **Correctness**: Factual, numerical, and arithmetic precision are absolute. A report with beautiful formatting but incorrect arithmetic or ungrounded claims is unacceptable.
2. **Traceability**: Every fact, metric, and table row must have an unbroken provenance chain (source file, SHA-256 hash, page number, spatial bounding box).
3. **Security**: Absolute offline air-gapped operation, zero cloud telemetry, path traversal defense, and sanitized export.
4. **Maintainability**: Clean, decoupled, modular abstractions with strict type hints and comprehensive test coverage.
5. **Performance**: High throughput and low memory footprint (< 4 GB RAM ceiling, 300–400 page scaling) achieved through deterministic algorithms, not shortcuts that compromise traceability.
6. **Visual Polish**: Professional typography, CIL corporate branding, and clean print layouts. Essential for executive presentation, but never prioritized over truth or security.

---

## 5. Automated Verification & Simulation Harness
The `ExpectedBehaviorVerifier` (`core/orchestrator/expected_behavior_verifier.py`) exposes programmatic and REST API verification:
- `audit_component(info)`: Evaluates the 7 inquiries for any given component.
- `verify_modular_swappability()`: Asserts that all 5 abstract interfaces, source classes, and target classes are decoupled.
- `simulate_swap(subsystem_key)`: Executes a live hot-swap test on `llm`, `connector`, `template`, `database`, or `ocr`, certifying that **0 unrelated modules** are affected.
- `validate_priority_hierarchy()`: Confirms monotonicity and enforcement of the 6-level priority hierarchy.

### REST API Endpoints:
- `GET /api/v1/system/expected-behavior/audit`: Consolidated Section 45 audit report.
- `POST /api/v1/system/expected-behavior/verify-component`: Evaluates individual component compliance.
- `POST /api/v1/system/expected-behavior/simulate-swap`: Executes dynamic swap simulation.
