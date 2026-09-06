# CIL Local AI Report Generator

A **local-first document intelligence and report-generation platform** for generating comprehensive Coal India Limited (CIL) subsidiary reports from confidential local organizational data.

## Key Tenets

1. **Local-First AI**: Confidential source documents never leave the local environment. All indexing, parsing, OCR, and AI inference execute locally without reliance on third-party cloud APIs.
2. **Deterministic Truth & Provenance**: The LLM is used for synthesis, semantic structuring, and drafting. Raw facts, numbers, dates, tables, and coordinates are handled deterministically with full source traceability down to page numbers and spreadsheet cells.
3. **Dynamic Report Architecture**: Supports recurring, mandatory, optional, and newly discovered sections tailored to current-period operational evidence.
4. **Agentic Review with Diff**: Interactive editing where requested corrections trace back to evidence and require explicit human validation.
5. **Security from Day Zero**: Default-deny network policies, secure credential management, and structured audit logs.

## Architecture & Monorepo Structure

```text
├── apps/
│   ├── desktop/                 # Tauri 2 + React + TypeScript desktop shell
│   └── processing/              # Local Python processing service (FastAPI)
├── core/
│   ├── domain/                  # Canonical Document, Evidence, and Report models
│   ├── connectors/              # DataConnector interface & LocalFolderConnector
│   ├── ingestion/               # File discovery, hashing, and format parsing
│   ├── extraction/              # Layout, OCR, and tabular extraction
│   ├── retrieval/               # SQLite FTS5 & hybrid search
│   ├── ai/                      # Local AI Gateway (llama.cpp / Gemma / Llama)
│   ├── validation/              # Deterministic rule & fact validation engine
│   ├── provenance/              # Source evidence tracking
│   └── reports/                 # Dynamic planner, templates & PDF composition
├── data/                        # Local workspace, indexes, and cache directories
├── docs/                        # Architecture and development documentation
└── tests/                       # Comprehensive unit & integration test suites
```

## Getting Started (Phase 0)

### Python Backend Service
```bash
# Set up Python virtual environment
py -3.13 -m venv .venv
.venv\Scripts\activate

# Install dependencies in editable mode
pip install -e ".[dev]"

# Run tests
pytest -v

# Start the processing service
python -m apps.processing.server
```

### Desktop UI Shell
```bash
cd apps/desktop
npm install
npm run dev
```
