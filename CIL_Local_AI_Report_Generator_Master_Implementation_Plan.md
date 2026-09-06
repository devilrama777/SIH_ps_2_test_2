# CIL Local AI Report Generator — Master Implementation Specification

## 0. Purpose

You are an autonomous senior software architect and implementation agent working inside an IDE workspace.

Build a **cross-platform desktop application** for generating large, high-quality CIL subsidiary reports from confidential local organizational data.

The application is a **local-first document intelligence and report-generation platform**, not a simple "LLM writes a PDF" application.

The target environment is:

- Windows
- macOS
- Linux
- CPU-first operation
- Optional GPU acceleration
- i5-class CPU
- 8 GB or 16 GB RAM
- approximately 4 GB GPU where available
- approximately 512 GB storage

The system must be capable of scaling toward reports of approximately **300–400 pages**, while also handling smaller reports.

The application must process confidential organizational information locally. External cloud LLMs, cloud OCR, and external AI APIs are not allowed.

Internet connectivity is allowed only where explicitly required for:

1. retrieving data from an approved organizational server/source in a future production deployment, and/or
2. uploading an approved final report to an approved organizational website/service.

The prototype must use the **local PC filesystem as its data source** because production server/database access is not currently available.

---

# 1. NON-NEGOTIABLE ENGINEERING RULES

## 1.1 Do not make assumptions

If a requirement is ambiguous, do not silently decide.

Instead:

1. identify the ambiguity,
2. explain the architectural impact,
3. ask for clarification when the decision materially affects implementation.

Do not invent:

- CIL server architecture,
- database technology,
- authentication provider,
- network protocol,
- production deployment topology,
- report business rules,
- financial formulas,
- data definitions,
- organization-specific workflows.

Where a future production detail is unknown, create an abstraction/interface rather than guessing.

## 1.2 Local-first AI

All AI inference must be local.

Do not integrate:

- OpenAI API
- Anthropic API
- Gemini API
- cloud LLM APIs
- cloud OCR
- cloud embeddings
- third-party AI SaaS

unless the user explicitly changes this requirement later.

## 1.3 LLM is not the source of truth

The LLM must NOT be responsible for:

- raw PDF parsing,
- OCR,
- deterministic numerical calculations,
- spreadsheet extraction,
- source-page identification,
- hyperlink extraction,
- image coordinate placement,
- final PDF composition,
- factual verification.

Use deterministic/document-processing components for these jobs.

The LLM is responsible for tasks such as:

- semantic understanding,
- summarization,
- classification,
- report planning,
- narrative generation,
- semantic retrieval assistance,
- identifying relationships between evidence and sections,
- agentic editing.

## 1.4 Preserve provenance

Every important generated fact/statement/table/image must be traceable to source evidence.

The system must preserve:

- source document
- source path/reference
- page number where applicable
- section
- paragraph/block
- spreadsheet workbook
- spreadsheet sheet
- spreadsheet cell/range
- image source
- extraction method
- confidence where available
- document date
- reporting period
- relevant metadata

## 1.5 Security is required from the first prototype

Do not postpone security until production.

Implement real security controls in the prototype.

---

# 2. USER'S REPORT REQUIREMENT

The system is intended to generate large organizational reports.

The provided previous annual report is primarily a **quality/layout/style reference**, not a rigid template that must be copied.

The report generator must support:

- recurring sections,
- mandatory sections,
- optional sections,
- conditionally generated sections,
- newly discovered sections,
- new top-level sections,
- new subsections,
- tables,
- charts,
- photographs/images,
- hyperlinks,
- audit material,
- financial material,
- CSR material,
- narrative content.

The structure must evolve based on current-year/current-period evidence.

The previous report should be analyzed for:

- hierarchy,
- recurring topics,
- visual language,
- layout patterns,
- typography,
- table styles,
- image placement,
- section organization,
- recurring report conventions.

It must NOT force the new report into exactly the same structure.

---

# 3. INPUT FORMATS

The prototype must support:

- scanned PDF
- digital PDF
- DOCX
- XLSX
- JPG
- PNG
- TIFF
- TXT
- CSV
- existing reports

Do NOT implement ZIP/archive ingestion or PPTX ingestion unless explicitly requested later.

The architecture must be extensible so new formats can be added without redesigning the system.

---

# 4. DATA SOURCE ARCHITECTURE

## Prototype

Use a local filesystem connector:

```text
Local PC
  |
  +-- files
  +-- folders
  +-- reports
  +-- spreadsheets
  +-- images
  +-- scanned PDFs
```

Create a connector abstraction:

```python
class DataConnector:
    def discover(self, query):
        ...

    def list_sources(self):
        ...

    def fetch_document(self, source_id):
        ...

    def fetch_metadata(self, source_id):
        ...

    def health_check(self):
        ...
```

Implement:

```text
LocalFolderConnector
```

first.

## Future production

Do not assume the future CIL source technology.

The architecture must permit future implementations such as:

```text
CILApiConnector
SqlConnector
NetworkShareConnector
SharePointConnector
SftpConnector
```

without rewriting the document intelligence/report-generation pipeline.

---

# 5. DATA DISCOVERY AND TIME-BASED ORGANIZATION

The system must work whether source data is organized:

### Case A

```text
2025/
  January/
  February/
  March/
```

or:

### Case B

```text
Documents/
  production.pdf
  report.xlsx
  meeting.docx
  scan.pdf
  image.jpg
```

where dates are embedded inside the documents.

Therefore, ingestion must extract both:

## File metadata

- filename
- filesystem path
- created timestamp
- modified timestamp
- folder information

## Content metadata

- document date
- reporting month
- reporting quarter
- financial year
- reporting period
- event dates
- meeting dates
- effective dates

Create a temporal index so queries such as:

```text
"Show all evidence relevant to March 2025"
```

can work independently of folder organization.

Do not assume that file modification time equals reporting date.

---

# 6. DOCUMENT INGESTION PIPELINE

Build:

```text
Source
  |
  v
File Discovery
  |
  v
File Fingerprinting
  |
  v
Format Detection
  |
  v
Format-Specific Parser
  |
  +--> PDF
  +--> DOCX
  +--> XLSX
  +--> CSV
  +--> TXT
  +--> Image
  |
  v
Layout/OCR/Table Extraction
  |
  v
Canonical Document Model
  |
  +--> Text
  +--> Tables
  +--> Images
  +--> Charts
  +--> Links
  +--> Metadata
  +--> Provenance
```

The pipeline must be incremental and resumable.

If 500 files are ingested and processing fails at file 317, the application must not need to start from zero.

---

# 7. PDF/OCR STRATEGY

Use **Docling and PaddleOCR/PP-StructureV3 as the primary technologies to evaluate and integrate**, rather than relying on a single generic PDF-to-text conversion.

The system should distinguish:

```text
Digital PDF
    |
    +--> structural/text extraction
```

from:

```text
Scanned PDF
    |
    +--> OCR
    +--> layout analysis
    +--> table recognition
    +--> reading order
```

Target workload:

```text
approximately 100 pages x approximately 30 scanned PDFs/month
```

The implementation must benchmark actual performance on the target hardware.

Do not promise a processing speed until it has been measured.

OCR output should preserve, where available:

- page number
- bounding boxes
- text blocks
- headings
- tables
- images
- reading order
- OCR confidence
- source coordinates

---

# 8. MARKITDOWN ROLE

MarkItDown may be used as a **secondary LLM-friendly normalization layer**.

Do NOT make the architecture:

```text
everything -> MarkItDown -> LLM
```

Instead use:

```text
                 +--> Canonical structured model
Raw documents --+
                 +--> Markdown representation
```

Markdown is useful for:

- LLM context
- summarization
- semantic processing
- indexing

The canonical structured model remains authoritative because it preserves:

- pages
- coordinates
- tables
- cells
- images
- links
- metadata
- provenance
- extraction confidence

---

# 9. CANONICAL DOCUMENT MODEL

Create a formal internal document model.

Conceptually:

```text
Document
 |
 +-- document_id
 +-- source_reference
 +-- source_hash
 +-- document_type
 +-- reporting_year
 +-- reporting_period
 +-- dates[]
 +-- metadata
 |
 +-- pages[]
 |    |
 |    +-- page_number
 |    +-- elements[]
 |         |
 |         +-- heading
 |         +-- paragraph
 |         +-- table
 |         +-- image
 |         +-- chart
 |         +-- link
 |         +-- other
 |
 +-- tables[]
 +-- images[]
 +-- links[]
```

Every meaningful element must receive a stable provenance/evidence ID.

Example:

```json
{
  "element_id": "el_009821",
  "type": "table_cell",
  "document_id": "doc_0042",
  "page": 117,
  "bbox": [120, 430, 820, 710],
  "text": "1245.70",
  "confidence": 0.97
}
```

For XLSX:

```json
{
  "element_id": "el_12042",
  "type": "spreadsheet_cell",
  "document_id": "financial_2025",
  "sheet": "March",
  "cell": "G27",
  "value": 1245.70
}
```

The actual schema should be designed cleanly and documented.

---

# 10. DATABASE

Start with **SQLite** for the prototype.

Use it for:

- documents
- pages
- elements
- tables
- table cells
- images
- links
- report definitions
- report sections
- provenance
- corrections
- audit logs
- users/settings where appropriate

Use **SQLite FTS5** for lexical/full-text retrieval.

Add a local vector/semantic retrieval layer after benchmarking the exact workload.

Do not prematurely introduce distributed infrastructure.

The persistence layer must be abstract enough that migration to a server database later is possible.

---

# 11. RETRIEVAL ARCHITECTURE

Use hybrid retrieval:

```text
Query
 |
 +--> lexical search
 |
 +--> semantic search
 |
 +--> metadata filters
 |
 +--> temporal filters
 |
 +--> source/type filters
 |
 v
Result Fusion
 |
 v
Evidence Ranking
 |
 v
LLM Context
```

Example query:

```text
"Find all March 2025 operational performance information."
```

should use:

- semantic relevance
- exact terms
- reporting dates
- document dates
- source metadata
- document type

The retrieval system must return evidence with provenance, not just text chunks.

---

# 12. LOCAL AI GATEWAY

Do not hard-code Gemma or Llama into the business logic.

Create:

```text
AI Gateway
 |
 +--> Gemma
 +--> Llama 3.1
 +--> Future local model
```

The rest of the application should use model-independent operations such as:

```text
generate()
chat()
summarize()
classify()
extract_semantics()
plan_report()
edit_section()
```

Use **llama.cpp as the primary local inference backend candidate**.

Support CPU-first execution and GPU acceleration where available.

Model selection must be benchmark-driven.

Benchmark at minimum:

- RAM usage
- CPU speed
- GPU utilization
- tokens/sec
- context handling
- summarization quality
- factual grounding
- numerical reasoning
- table reasoning
- report-writing quality
- correction quality

Do not assume the largest model is automatically the best model for the target hardware.

---

# 13. REPORT PLANNER

Never ask the LLM to directly write a 400-page report in one prompt.

Use:

```text
Evidence
  |
  v
Report Planner
  |
  v
Report Plan
  |
  v
Section Evidence Sets
  |
  v
Section Generation
  |
  v
Validation
  |
  v
Composition
```

The planner must support:

```text
mandatory section
optional section
conditional section
recurring section
discovered section
new top-level section
new subsection
```

Example:

```json
{
  "title": "Digital Mine Transformation",
  "type": "discovered",
  "level": 1,
  "reason": "Current-period evidence contains substantial material not represented in the previous report structure."
}
```

The system must be capable of adding new top-level sections.

---

# 14. PREVIOUS REPORT ANALYSIS

Treat the provided annual report as a **reference corpus**.

Build a report-structure analyzer that can extract:

- section hierarchy
- heading patterns
- recurring sections
- table patterns
- image patterns
- chart patterns
- layout patterns
- page composition
- typography information where technically recoverable
- hyperlinks
- captions
- visual conventions

Use these observations as guidance for generating a new report.

Do not simply clone page-by-page content.

---

# 15. REPORT DATA MODEL

Create a structured intermediate report representation:

```text
Report
 |
 +-- metadata
 +-- title
 +-- reporting_period
 +-- template
 |
 +-- sections[]
      |
      +-- section_id
      +-- title
      +-- level
      +-- type
      +-- narrative_blocks[]
      +-- tables[]
      +-- charts[]
      +-- images[]
      +-- links[]
      +-- source_refs[]
      +-- validation_status
```

This model must be independent of the final PDF renderer.

That allows:

```text
same content
   |
   +--> classic template
   |
   +--> modern template
```

---

# 16. CONTENT GENERATION

Generate report content section-by-section.

Each generated section must receive an evidence package.

Example:

```text
Section:
Financial Performance

Evidence:
- Annual financial statements
- Monthly XLSX data
- Previous report references
- Relevant audit observations
```

The LLM must be instructed:

1. use only supplied evidence,
2. do not invent figures,
3. do not invent dates,
4. do not invent events,
5. do not fabricate sources,
6. explicitly mark insufficient evidence,
7. preserve numerical precision where required,
8. return structured output,
9. attach provenance references to factual claims where possible.

---

# 17. VALIDATION ENGINE

Build a deterministic validation layer before final PDF generation.

Validate:

## Numerical

- totals
- percentages
- arithmetic
- unit consistency
- year-over-year comparisons
- table values

## Temporal

- reporting periods
- dates
- financial years
- chronological ordering

## Provenance

- every important factual claim has evidence
- source IDs resolve
- page/cell references are valid

## Structural

- mandatory sections exist
- headings are valid
- section hierarchy is valid

## Visual

- image dimensions
- image resolution
- overflow
- broken layouts
- table overflow

## Links

- hyperlink targets exist
- URLs are preserved correctly

If validation fails, flag the issue before final approval.

---

# 18. IMAGE INTELLIGENCE SYSTEM

Images must not simply be pasted into the report.

Create an asset pipeline:

```text
Images
  |
  v
Asset Analyzer
  |
  +--> dimensions
  +--> quality
  +--> duplicate detection
  +--> OCR if useful
  +--> semantic description
  +--> source
  +--> date
  +--> topic
  +--> provenance
  |
  v
Image Asset Database
  |
  v
Report Planner
  |
  v
Layout Engine
```

The AI may recommend which image is relevant to a section.

The deterministic layout engine decides actual placement.

Support layouts such as:

- single hero image
- two-column image/text
- 2x2 image grid
- image with caption
- image + narrative
- multiple images with controlled spacing

Do not expose raw page coordinates as an LLM responsibility.

---

# 19. PDF GENERATION

Use:

```text
Report JSON
   |
   v
HTML/CSS
   |
   v
Chromium / Playwright
   |
   v
PDF
```

The report renderer must support:

- page breaks
- headers
- footers
- page numbering
- tables
- charts
- images
- captions
- hyperlinks
- sections
- TOC
- internal navigation where possible
- external links
- professional typography
- print-friendly layout

---

# 20. TWO REPORT VISUAL MODES

The final PDF must support both:

## Template A — Existing-report-inspired

A style influenced by the provided reference report.

## Template B — Modern corporate

A cleaner contemporary visual design.

The same Report Model must feed both.

The user must be able to select the desired style.

Do not duplicate content-generation logic for different templates.

---

# 21. SOURCE TRACEABILITY UI

The desktop application must allow users to inspect sources.

Example:

```text
Generated statement
        |
        +--> Source: report.pdf
        |       Page 117
        |
        +--> Source: financial.xlsx
                Sheet: March
                Cell: G27
```

The source viewer should support opening/revealing the original evidence where possible.

For PDF sources:

- document
- page
- relevant region where possible

For spreadsheets:

- workbook
- sheet
- cell/range

For images:

- original image
- source metadata

Source traceability must exist in the intermediate report model and not be added as an afterthought.

---

# 22. HUMAN + AGENT REVIEW SYSTEM

The user explicitly wants an agent-based editing experience.

Flow:

```text
Generated Report
      |
      v
Human Review
      |
      v
User instruction
      |
      v
Editing Agent
      |
      +--> locate affected section
      +--> retrieve source evidence
      +--> verify
      +--> regenerate
      +--> validate
      |
      v
Diff / Preview
      |
      v
Accept / Reject
```

Example:

```text
User:
"The production figure in this section is incorrect. Re-check the source and correct it."
```

The agent must:

1. locate the relevant statement,
2. locate provenance,
3. retrieve original evidence,
4. determine the correct value,
5. regenerate only affected content,
6. rerun validation,
7. show the change,
8. require user acceptance.

Do not allow blind string replacement for factual corrections.

---

# 23. AGENT TOOL SECURITY

The LLM must never receive unrestricted filesystem access.

Expose controlled application tools such as:

```text
search_documents()
get_source()
get_page()
get_table()
get_spreadsheet_range()
get_image()
update_section()
validate_section()
render_preview()
export_pdf()
upload_report()
```

Each tool must enforce authorization and input validation.

High-risk operations such as uploading a report must require explicit human approval.

The LLM should request an operation; the application decides whether it is permitted.

---

# 24. SECURITY MODEL

Implement real controls from the prototype.

## Data

Confidential source data remains local during AI/OCR/document processing.

## AI

No external AI API calls.

## Credentials

Do not store credentials in:

- source code
- `.env` files distributed with the application
- plaintext JSON
- plaintext SQLite tables

Use OS-supported secure credential/key storage.

## Database

Evaluate/use encrypted SQLite storage for sensitive metadata where appropriate.

## Files

Use controlled workspace directories and OS permissions.

## Audit logging

Log security-relevant operations:

- login/authentication events where authentication exists
- document ingestion
- report creation
- source access where required
- agent actions
- edits
- approvals
- exports
- uploads
- configuration changes

Do not log sensitive document contents unnecessarily.

## Network

Default-deny network behavior where practical.

Only explicitly configured connectors may communicate externally.

## Telemetry

No hidden analytics or telemetry.

## Secrets

Never commit secrets to Git.

Provide secure configuration handling.

---

# 25. DESKTOP APPLICATION ARCHITECTURE

Use:

```text
Tauri 2
+
React
+
TypeScript
```

for the desktop application.

Use Python for document intelligence and AI orchestration.

Conceptually:

```text
Tauri
 |
 +-- React/TypeScript UI
 |
 +-- Rust desktop layer
 |
 +-- Python processing service
```

The exact IPC mechanism should be chosen based on implementation practicality and documented.

The UI must remain responsive while large documents are processed.

Use background jobs for:

- OCR
- ingestion
- embeddings
- report generation
- rendering
- validation

---

# 26. RECOMMENDED CODEBASE STRUCTURE

Create a maintainable monorepo structure similar to:

```text
cil-report-ai/
|
+-- apps/
|   +-- desktop/
|   |   +-- src/
|   |   +-- src-tauri/
|   |
|   +-- processing/
|
+-- core/
|   +-- domain/
|   |   +-- documents/
|   |   +-- evidence/
|   |   +-- reports/
|   |   +-- assets/
|   |   +-- users/
|   |
|   +-- ingestion/
|   |   +-- pdf/
|   |   +-- docx/
|   |   +-- xlsx/
|   |   +-- images/
|   |   +-- text/
|   |
|   +-- extraction/
|   |   +-- ocr/
|   |   +-- layout/
|   |   +-- tables/
|   |   +-- links/
|   |
|   +-- retrieval/
|   |
|   +-- ai/
|   |   +-- gateway/
|   |   +-- prompts/
|   |   +-- planners/
|   |   +-- agents/
|   |
|   +-- validation/
|   |
|   +-- provenance/
|   |
|   +-- reports/
|       +-- planner/
|       +-- templates/
|       +-- layout/
|       +-- pdf/
|   |
|   +-- connectors/
|       +-- local/
|       +-- future/
|
+-- models/
|
+-- data/
|   +-- cache/
|   +-- indexes/
|   +-- workspace/
|
+-- tests/
|   +-- ingestion/
|   +-- extraction/
|   +-- retrieval/
|   +-- ai/
|   +-- reports/
|   +-- security/
|
+-- installer/
|
+-- docs/
```

Adapt the exact structure if there is a strong engineering reason, but document the reason before making a major deviation.

---

# 27. PROCESSING JOB SYSTEM

Large reports cannot be generated as one blocking request.

Create a job system.

Example:

```text
Job
 |
 +-- job_id
 +-- type
 +-- status
 +-- progress
 +-- current_stage
 +-- started_at
 +-- completed_at
 +-- errors[]
```

Stages:

```text
DISCOVERY
INGESTION
OCR
EXTRACTION
NORMALIZATION
INDEXING
PLANNING
GENERATION
VALIDATION
COMPOSITION
RENDERING
READY_FOR_REVIEW
```

The UI must display progress and errors.

Jobs should be resumable where practical.

---

# 28. REPORT GENERATION SHOULD BE INCREMENTAL

Never regenerate an entire 400-page report because one paragraph changed.

Maintain section-level dependencies.

Example:

```text
Financial Section
    |
    +--> source A
    +--> source B
    +--> source C
```

If source B or its interpretation changes:

```text
invalidate affected section
       |
       v
regenerate section
       |
       v
validate
       |
       v
recompose PDF
```

---

# 29. TESTING STRATEGY

Create automated tests for:

## Unit tests

- parsers
- date extraction
- metadata extraction
- provenance
- calculations
- validation
- report model
- template rendering

## Integration tests

- PDF -> canonical model
- XLSX -> canonical model
- OCR -> canonical model
- retrieval -> evidence
- evidence -> LLM
- LLM -> report section
- report -> HTML
- HTML -> PDF

## Security tests

- unauthorized tool access
- path traversal
- malformed documents
- malicious input files
- secret exposure
- unauthorized network access
- upload authorization

## Regression tests

Use the provided reference annual report as a test corpus for representative structures.

Create representative fixtures for:

- text-heavy pages
- scanned pages
- financial tables
- charts
- photo grids
- hyperlinks
- audit/C&AG sections
- CSR sections
- complex layouts

---

# 30. GOLDEN DATASET

Create a regression dataset:

```text
testdata/reference_report/
|
+-- digital_pages/
+-- scanned_pages/
+-- financial_tables/
+-- charts/
+-- photographs/
+-- hyperlinks/
+-- audit_sections/
+-- csr_sections/
+-- complex_layouts/
```

Store expected extraction/provenance results where possible.

Every major parser/model change should be tested against this dataset.

---

# 31. MODEL EVALUATION

Create a model benchmark harness.

Models:

```text
Gemma 4
Llama 3.1
```

and future local models.

Evaluate identical tasks:

```text
Task 1: summarize evidence
Task 2: identify relevant evidence
Task 3: generate section
Task 4: interpret tables
Task 5: identify contradictions
Task 6: edit section
Task 7: follow provenance
Task 8: generate report plan
```

Record:

```text
accuracy
grounding
hallucination rate
latency
tokens/sec
RAM
GPU memory
CPU usage
```

Do not select a model based only on subjective writing quality.

---

# 32. REPORT QUALITY METRICS

Create measurable quality checks.

Examples:

```text
source coverage
provenance coverage
unsupported-claim rate
numerical error rate
broken-link rate
missing-section rate
layout overflow rate
image placement quality
OCR accuracy
table extraction accuracy
```

The long-term goal is to minimize manual correction.

---

# 33. USER INTERFACE

The UI should conceptually contain:

```text
Dashboard
 |
 +-- New Report
 +-- Data Sources
 +-- Processing Jobs
 +-- Evidence Search
 +-- Report Planner
 +-- Report Editor
 +-- Source Viewer
 +-- Asset Manager
 +-- Validation
 +-- Preview
 +-- Export
 +-- Settings
 +-- Security/Audit
```

## New Report flow

```text
1. Select data source
2. Select reporting period
3. Discover/index data
4. Review discovered material
5. Analyze previous report/reference
6. Generate report plan
7. Review plan
8. Generate sections
9. Validate
10. Review/edit with agent
11. Choose visual template
12. Render preview
13. Approve
14. Export PDF
15. Optional authorized upload
```

---

# 34. ERROR HANDLING

The system must fail safely.

Examples:

If OCR fails:

```text
Do not silently invent text.
Mark extraction failure.
Allow retry.
```

If source evidence is missing:

```text
Do not fabricate.
Mark "insufficient evidence".
```

If numerical sources conflict:

```text
Flag conflict.
Show sources.
Request human resolution where needed.
```

If PDF rendering fails:

```text
Preserve report model.
Show rendering error.
Allow retry.
```

---

# 35. OBSERVABILITY

Implement local diagnostic logs.

Logs should record:

- processing stage
- duration
- failures
- model used
- parser used
- document IDs
- job IDs

Avoid logging confidential content unnecessarily.

Provide a diagnostic export mechanism that can exclude sensitive source contents.

---

# 36. PERFORMANCE STRATEGY

The application must be designed for large documents.

Use:

- streaming where appropriate
- chunked processing
- background workers
- caching
- incremental indexing
- incremental report generation
- page-level processing
- section-level regeneration

Do not load an entire 400-page report and all source documents into one Python object if unnecessary.

Do not place the entire corpus into a single LLM context.

Use retrieval.

---

# 37. STORAGE MANAGEMENT

The application should track:

```text
original source
processed representation
OCR result
structured extraction
embeddings/indexes
generated report
temporary render files
```

Provide cleanup policies for temporary artifacts.

Never delete original source data automatically unless explicitly authorized.

---

# 38. INSTALLATION

The final application should install locally with:

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

The model should be installable/downloadable as part of the application's setup process, subject to the model's licensing/distribution requirements.

Do not assume a user already has Python or Node.js installed.

The production installer should eventually bundle/package the necessary runtime components.

---

# 39. DEVELOPMENT PHASES

Implement incrementally.

## Phase 0 — Architecture and workspace

Deliver:

- repository structure
- architecture documentation
- development environment
- dependency management
- basic desktop shell
- Python service
- health checks

## Phase 1 — Local data connector

Deliver:

- folder selection
- file discovery
- hashing
- metadata extraction
- supported-format detection
- ingestion job system

## Phase 2 — Document extraction

Deliver:

- PDF extraction
- OCR
- DOCX
- XLSX
- CSV/TXT
- images
- canonical document model
- provenance

## Phase 3 — Search

Deliver:

- SQLite
- FTS5
- metadata filters
- temporal search
- semantic retrieval
- evidence ranking

## Phase 4 — Local AI

Deliver:

- AI Gateway
- llama.cpp integration
- Gemma integration
- Llama integration
- benchmark harness

## Phase 5 — Report Planner

Deliver:

- previous-report analysis
- report structure model
- dynamic sections
- new top-level sections
- evidence-to-section mapping

## Phase 6 — Report Generation

Deliver:

- section generation
- tables
- charts
- hyperlinks
- provenance

## Phase 7 — Image intelligence

Deliver:

- asset database
- image relevance
- duplicate detection
- layout selection
- captions

## Phase 8 — PDF renderer

Deliver:

- HTML/CSS
- Chromium/Playwright
- classic template
- modern template
- TOC
- page numbering
- links

## Phase 9 — Agentic editing

Deliver:

- source-aware editing
- correction workflow
- diff
- validation
- approval

## Phase 10 — Security

Security begins in Phase 0 and is continuously implemented.

Finalize:

- credential storage
- encrypted sensitive storage
- authorization
- audit log
- network restrictions
- secure tool execution

## Phase 11 — Full regression

Run the complete reference-report test suite.

## Phase 12 — Packaging

Build installers for:

- Windows
- macOS
- Linux

---

# 40. FIRST VERTICAL SLICE

Before attempting a 400-page report, build a complete small end-to-end slice:

```text
10–20 representative source files
       |
       v
ingestion
       |
       v
OCR/extraction
       |
       v
canonical model
       |
       v
search
       |
       v
local LLM
       |
       v
report plan
       |
       v
5–10 page report
       |
       v
provenance
       |
       v
human correction
       |
       v
validation
       |
       v
PDF
```

Do not proceed to massive-scale generation until this vertical slice is reliable.

---

# 41. IMPLEMENTATION RULE FOR THE IDE AGENT

When implementing:

1. Inspect the existing workspace first.
2. Do not overwrite existing work without understanding it.
3. Maintain a clear task list.
4. Implement one phase at a time.
5. Run tests after meaningful changes.
6. Fix failures before moving forward.
7. Keep architecture documentation synchronized with implementation.
8. Never silently replace one major technology with another.
9. If a selected library is technically unsuitable, explain the issue and propose alternatives before changing the architecture.
10. Keep interfaces modular.
11. Keep AI providers behind the AI Gateway.
12. Keep data sources behind DataConnector.
13. Keep PDF templates behind the report renderer abstraction.
14. Keep provenance independent of UI.
15. Keep security controls independent of the LLM.

---

# 42. DEFINITION OF DONE

A feature is not complete merely because the code compiles.

For each major feature:

```text
Implementation
+
Unit tests
+
Integration tests where applicable
+
Error handling
+
Logging
+
Documentation
+
Security review
+
Performance measurement where applicable
```

must be considered.

---

# 43. IMPORTANT ARCHITECTURAL PRINCIPLE

The final system should look like:

```text
                  ┌──────────────────┐
                  │    Desktop UI    │
                  └────────┬─────────┘
                           │
                    Application Core
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        v                  v                  v
 Data Connectors     Document Engine     Report Engine
        │                  │                  │
        │                  v                  │
        │          Canonical Model            │
        │                  │                  │
        └──────────────────┼──────────────────┘
                           v
                   Retrieval Engine
                           │
                           v
                     Local AI Gateway
                           │
                           v
                  Report Planner/Agent
                           │
                           v
                     Validation
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
                          PDF
                           │
                     Human Approval
                           │
                           v
                  Optional Upload
```

The system's **source data, structured evidence, deterministic calculations, provenance, validation and report model** must remain independent of the local LLM.

The LLM is a powerful reasoning/generation component inside this architecture—not the architecture itself.

---

# 44. IMMEDIATE IMPLEMENTATION ORDER

Start with the following exact order:

```text
1. Create repository and architecture docs
2. Create Tauri + React desktop shell
3. Create Python processing service
4. Implement LocalFolderConnector
5. Implement ingestion/job system
6. Implement canonical document model
7. Implement PDF/document extraction
8. Implement OCR/layout/table extraction
9. Implement provenance
10. Implement SQLite + FTS5
11. Implement temporal metadata/search
12. Implement retrieval
13. Implement AI Gateway
14. Integrate local model runtime
15. Build model benchmark harness
16. Build Report Planner
17. Build section generator
18. Build validation engine
19. Build image asset pipeline
20. Build Report JSON model
21. Build HTML/CSS renderer
22. Build classic template
23. Build modern template
24. Build source viewer
25. Build agentic correction system
26. Add security/audit hardening
27. Build regression suite
28. Benchmark on target hardware
29. Build installers
30. Run complete end-to-end test
```

Do not jump directly to step 17 and generate PDFs from raw documents.

The foundation must be built first.

---

# 45. EXPECTED DEVELOPMENT BEHAVIOR

Act as a senior engineer.

Before implementing a component, determine:

- its responsibility,
- its inputs,
- its outputs,
- dependencies,
- failure modes,
- security implications,
- test strategy.

Keep the implementation modular enough that:

```text
Gemma -> another local model
LocalFolder -> CIL server
Classic template -> new template
SQLite -> future database
PaddleOCR -> another OCR engine
```

can be changed without rewriting unrelated parts.

At every stage prioritize:

**correctness > traceability > security > maintainability > performance > visual polish.**

Visual quality is important, but the system must never sacrifice factual correctness and provenance for appearance.

---

# 46. FINAL PRODUCT VISION

The finished application should allow a user to do approximately:

```text
Select:
    "FY 2025-26 source folder"

Select:
    "Previous report/reference"

Select:
    "Modern template"

Click:
    "Generate Report"

System:
    discovers files
    extracts documents
    OCRs scans
    extracts tables
    indexes evidence
    identifies dates
    analyzes previous structure
    discovers current topics
    creates dynamic report plan
    selects relevant evidence
    generates sections locally
    validates facts/numbers
    selects appropriate images
    composes the report
    renders PDF

User:
    reviews
    asks agent for corrections
    accepts/rejects changes

System:
    regenerates only affected sections
    revalidates
    creates final PDF

User:
    approves

System:
    optionally uploads through authorized connector
```

The target is a **secure, local-first, source-traceable, dynamically structured, agent-editable report-generation platform** capable of eventually supporting CIL subsidiary production workflows without coupling the prototype to an unknown future server architecture.
