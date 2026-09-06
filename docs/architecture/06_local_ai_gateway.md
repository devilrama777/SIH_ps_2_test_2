# Local AI Gateway & Model Evaluation Specification

## 1. Architectural Purpose

The **Local AI Gateway** (`core/ai/`) provides an air-gapped, model-independent reasoning and narrative generation layer for the CIL Report Generator, strictly implementing **Section 1.2, 1.3, 12, and 31** of the *CIL Local AI Report Generator Master Implementation Specification*.

The gateway decouples CIL business components (Report Planner, Section Generator, Validation Engine, Agentic Editor) from specific model weights (e.g. Gemma, Llama 3.1, Qwen) and execution engines.

```
+------------------------------------------------------------------------------------+
|               CIL Business Layer (Report Planner, Generator, Editor)              |
+------------------------------------------------------------------------------------+
                                       |
                   AIGateway (Model-Independent Interface)
     +------------------------------------------------------------------+
     |  generate()        chat()             summarize()   classify()   |
     |  plan_report()     edit_section()     extract_semantics()        |
     +------------------------------------------------------------------+
                                       |
                         LocalAIGateway Orchestration
                                       |
    +----------------------------------+----------------------------------+
    |                                  |                                  |
[RuleBasedLocalBackend]      [LocalHttpInferenceBackend]     [LlamaCppDirectBackend]
- Zero external dependencies - 127.0.0.1 / localhost only   - In-process GGUF engine
- Deterministic citations    - llama.cpp server / Ollama    - llama-cpp-python C++
- CI/CD & test validation    - CPU / GPU port offload       - CPU-first / n_gpu_layers
```

---

## 2. Strict Air-Gap & Security Invariants

1. **Zero External Cloud AI API Calls (Rule 1.2)**:
   - External endpoints (OpenAI, Anthropic, Gemini, cloud OCR, or third-party AI SaaS) are strictly prohibited.
   - Any attempt to pass non-loopback URLs (e.g., `https://api.openai.com` or LAN IPs) to `LocalHttpInferenceBackend` raises a blocking `ValueError` with an *Air-gapped security violation* error.
2. **LLM is Not the Source of Truth (Rule 1.3)**:
   - Numerical totals, spreadsheet cell ranges, and PDF bounding boxes are computed deterministically by document extraction extractors (`core/extraction/`).
   - The LLM is restricted to semantic understanding, narrative summarization, and report planning.
3. **Mandatory Provenance Citations (Rule 1.4)**:
   - Every generated factual statement must cite its source document and page/cell using bracketed notation: `[DOC:filename:P{page}]` or `[COORD:workbook:sheet:cell]`.
   - The gateway automatically scans responses, extracts cited references, and populates `AIResponse.grounding_metadata`.

---

## 3. Pluggable Backends

| Backend Class | Engine Type | Use Case & Hardware Fit |
|---|---|---|
| `RuleBasedLocalBackend` | Deterministic Python / regex engine | Offline testing, unit test suites, fast CI/CD validation, zero weight downloads. |
| `LocalHttpInferenceBackend` | Local HTTP REST (`127.0.0.1:[port]/v1`) | Connects to an air-gapped local `llama.cpp` server or `Ollama` running on the host machine. |
| `LlamaCppDirectBackend` | In-process C-bindings (`llama_cpp.Llama`) | In-process GGUF loading with CPU thread tuning (`n_threads`) and GPU layer offload (`n_gpu_layers`). |

---

## 4. Standardized Model Benchmark Harness (Section 31)

To ensure model selection is empirical and benchmark-driven rather than based on subjective writing style, the platform provides `ModelBenchmarkHarness` (`core/ai/benchmark/`):

### 4.1 The 8 Evaluation Tasks

1. **Task 1: Summarize Evidence** — Evaluates retention of exact raw coal production metrics (e.g. 773.60 MT) and document page citations.
2. **Task 2: Identify Relevant Evidence** — Evaluates corpus discrimination and citation selection for specific operational topics (e.g., washery beneficiation yield at Patherdih).
3. **Task 3: Generate Section** — Evaluates narrative synthesis for Capex summaries citing audited ledgers and FMC reports.
4. **Task 4: Interpret Tables** — Evaluates tabular reading and dispatch mode share comparisons (Rail 62.1%, Road, MGR).
5. **Task 5: Identify Contradictions** — Evaluates detection of numerical discrepancies between draft press releases and audited statutory balance sheets.
6. **Task 6: Edit Section** — Evaluates evidence-grounded revisions incorporating environmental audit metrics (saplings planted, mine water discharge).
7. **Task 7: Follow Provenance** — Evaluates citation compliance under DGMS safety audit queries.
8. **Task 8: Generate Report Plan** — Evaluates dynamic corporate chapter structuring combining mandatory sections and discovered topics.

### 4.2 Metrics Recorded

- **Accuracy**: Proportion of ground truth facts correctly present.
- **Grounding Score**: Proportion of required provenance citations correctly cited.
- **Hallucination Rate**: $1.0 - (0.5 \times \text{Accuracy} + 0.5 \times \text{Grounding})$.
- **Latency & Throughput**: Seconds elapsed per task and generated tokens per second.
- **Hardware Footprint**: Peak RAM (MB) and CPU utilization (%) via `psutil`.

Evaluation runs are persisted as JSON and Markdown reports in `data/workspace/benchmarks/`.

---

## 5. API Endpoints

- `GET /api/v1/ai/models`: Query active model and candidate backends.
- `POST /api/v1/ai/backend/select`: Switch inference backend.
- `POST /api/v1/ai/generate`: Execute raw completion with citation extraction.
- `POST /api/v1/ai/summarize`: Grounded evidence summarization.
- `POST /api/v1/ai/benchmark`: Run the 8-task benchmark harness on the active backend.
- `GET /api/v1/ai/benchmarks`: List historical benchmark evaluation runs.
