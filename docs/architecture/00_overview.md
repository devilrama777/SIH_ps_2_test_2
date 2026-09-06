# CIL Local AI Report Generator — Architecture Overview

## 1. System Vision & Purpose

The **CIL Local AI Report Generator** is an air-gapped, local-first document intelligence and report-generation platform designed to assemble comprehensive subsidiary reports (300–400 pages) for Coal India Limited (CIL) subsidiaries from local confidential files.

### Architectural Tenets

1. **Air-Gapped Local Operation**:
   - Confidential source files never exit the local PC environment.
   - External cloud AI APIs (OpenAI, Anthropic, Gemini), cloud OCR, and cloud embeddings are strictly disallowed.
2. **Deterministic Calculations & Truth Grounding**:
   - The LLM is **never** used for raw PDF parsing, coordinate math, spreadsheet extraction, or deterministic arithmetic.
   - LLMs are reserved for semantic comprehension, topic structuring, narrative synthesis, and agentic revisions.
3. **End-to-End Traceability (Provenance)**:
   - Every fact, table cell, image, and narrative assertion links directly to an immutable `ProvenanceRecord` pointing to the exact document path, page number, bounding box, or spreadsheet coordinate (e.g. `Sheet: March, Cell: G27`).
4. **Dynamic Report Architecture**:
   - Rather than force-fitting evidence into a static template, reports evolve dynamically based on current-period evidence, discovering new top-level chapters and subsections as needed.

---

## 2. Monorepo Structure

```text
├── apps/
│   ├── desktop/                 # Tauri 2 + React + TypeScript desktop shell
│   └── processing/              # Local Python processing service (FastAPI / Uvicorn)
├── core/
│   ├── domain/                  # Canonical Document, Evidence, Job, and Report models
│   ├── connectors/              # DataConnector interface & LocalFolderConnector
│   ├── ingestion/               # File discovery, hashing, and format parsing
│   ├── extraction/              # Layout, OCR, and tabular extraction
│   ├── retrieval/               # SQLite FTS5 & hybrid search
│   ├── ai/                      # Local AI Gateway (llama.cpp / Gemma / Llama)
│   ├── validation/              # Deterministic rule & fact validation engine
│   ├── provenance/              # Source evidence tracking & ID generators
│   └── reports/                 # Dynamic planner, templates & PDF composition
├── data/                        # Local workspace, indexes, and cache directories
├── docs/                        # Architecture and development documentation
└── tests/                       # Comprehensive unit & integration test suites
```

---

## 3. Component Interactions & Data Flow

```text
                  ┌──────────────────┐
                  │    Desktop UI    │ (Tauri 2 / React)
                  └────────┬─────────┘
                           │ HTTP / IPC (Port 8765)
                    Application Core
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        v                  v                  v
 Data Connectors     Document Engine     Report Engine
 (LocalFolder)        (Docling/OCR)      (Planner & Templates)
        │                  │                  │
        │                  v                  │
        │          Canonical Model            │
        │                  │                  │
        └──────────────────┼──────────────────┘
                           v
                    Retrieval Engine (SQLite FTS5)
                           │
                           v
                     Local AI Gateway (llama.cpp)
                           │
                           v
                  Report Planner & Generation
                           │
                           v
                     Validation Engine
                           │
                           v
                    Report Composition
                           │
                 ┌─────────┴─────────┐
                 v                   v
          Classic Template     Modern Template
                 │                   │
                 └─────────┬─────────┘
                           v
                      Chromium / PDF
```

---

## 4. Phased Roadmap

| Phase | Title | Focus Area | Status |
|---|---|---|---|
| **0** | **Architecture & Workspace** | **Monorepo, domain models, FastAPI backend, Tauri shell, health checks** | **Done** |
| 1 | Local Data Connector | Folder selection, recursive file discovery, hashing, temporal indexing | Upcoming |
| 2 | Document Extraction & OCR | Scanned/digital PDF parsing, openpyxl, canonical population | Upcoming |
| 3 | Search & SQLite FTS5 | Hybrid lexical + temporal evidence retrieval | Upcoming |
| 4 | Local AI Gateway | llama.cpp runtime, Gemma/Llama inference, benchmark harness | Upcoming |
| 5 | Report Planner | Reference report analysis, dynamic hierarchy, section planning | Upcoming |
| 6 | Report Generation | Section generation, deterministic tables, charts, links | Upcoming |
| 7 | Image Intelligence | Asset database, duplicate detection, layout placement | Upcoming |
| 8 | PDF Renderer | Chromium/Playwright, Classic & Modern templates, TOC | Upcoming |
| 9 | Agentic Editing | Source-aware revisions, diff viewer, human approval loop | Upcoming |
| 10 | Security Hardening | Encrypted SQLite, OS credential storage, audit log | Ongoing |
| 11 | Full Regression | Reference report validation on test corpus | Upcoming |
| 12 | Packaging | Standalone installers for Windows, macOS, Linux | Upcoming |
