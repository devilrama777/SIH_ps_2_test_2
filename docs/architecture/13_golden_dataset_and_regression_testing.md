# Phase 13 Architecture: Golden Dataset & End-to-End Regression Harness

## 1. Overview & Objective

The **CIL Local AI Report Generator** operates in mission-critical corporate reporting environments where factual hallucination, numerical drift, or orphan claims are unacceptable. Phase 11 establishes a deterministic, reproducible, air-gapped Golden Dataset and Automated Regression Harness that rigorously tests the complete vertical slice of the platform.

```
+----------------------------------------------------------------------------------------------------+
|                                    GOLDEN DATASET HARNESS                                         |
+----------------------------------------------------------------------------------------------------+
| 1. Golden Reference Creation:                                                                      |
|    - 5 Ingestion fixtures (PDF mock, Financial Excel, CSR Word doc, Audit MD, Image Assets)        |
|    - ground_truth.json (Expected financials, production metrics, CSR expenditure, audit claims)    |
|                                                                                                    |
| 2. End-to-End Pipeline Execution:                                                                  |
|    Ingestion -> Canonical Extraction -> FTS5 Vector Index -> Blueprint Plan -> Section Generation  |
|    -> Deterministic Verification -> Image Cataloging & Layout -> Headless PDF Rendering           |
|                                                                                                    |
| 3. Quality & Regression Metrics Computation (Section 32):                                          |
|    - Source Coverage (Target >= 85%)                                                               |
|    - Provenance Coverage (Target >= 95%)                                                           |
|    - Unsupported Claim Rate (Target <= 0.05)                                                       |
|    - Numerical Error Rate (Target = 0.00)                                                          |
|                                                                                                    |
| 4. Cryptographic Audit Log & Persistent Regression Reports                                         |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Architectural Components

### 2.1 Golden Dataset Builder (`core.evaluation.golden_dataset.GoldenDatasetBuilder`)
Builds realistic multi-modal fixtures simulating an actual CIL subsidiary (e.g. Northern Coalfields Limited / Central Coalfields Limited):
- **Digital PDF Content**: Executive overview, Coal production records (137.5 MT target, 142.1 MT actual), Washery efficiency.
- **Financial Statements (`financial_tables.xlsx`)**: Balance sheet, Profit & Loss statements with exact INR Crores (Revenue: Rs. 24,150 Cr; Profit After Tax: Rs. 4,820 Cr).
- **CSR Documentation (`csr_sections.docx`)**: Community welfare, drinking water, skill development expenditure (Rs. 182.5 Cr).
- **Statutory Audit Log (`audit_sections.md`)**: Comptroller and Auditor General (CAG) compliance notes, internal auditor observations.
- **Image Assets**: High-resolution mining pit photographs and reclamation aerial imagery.
- **`ground_truth.json`**: Ground truth targets including expected numerical figures, key management personnel, and cross-reference citations.

### 2.2 Quality & Regression Metrics (`core.evaluation.metrics.QualityMetricCalculator`)
In strict adherence to Section 32 of the Master Implementation Plan:
1. **Source Coverage**:
   $$\text{Source Coverage} = \frac{\text{Unique Ingested Files Referenced}}{\text{Total Usable Ingested Files}}$$
2. **Provenance Coverage**:
   $$\text{Provenance Coverage} = \frac{\text{Substantive Paragraphs / Tables with Verified Provenance}}{\text{Total Substantive Paragraphs / Tables}}$$
3. **Unsupported Claim Rate**:
   $$\text{Unsupported Claim Rate} = 1.0 - \text{Provenance Coverage}$$
4. **Numerical Error Rate**:
   $$\text{Numerical Error Rate} = \frac{\text{Calculated Numbers Mismatching Source Records}}{\text{Total Quantitative Assertions}}$$
   *Deterministic Rule*: Every figure generated must match canonical spreadsheet or extracted table numbers to 0% error tolerance.
5. **Format Validation**:
   Verifies that rendered PDF output exists, is non-empty, and complies with corporate PDF/A-compliant structures.

### 2.3 End-to-End Regression Harness (`core.evaluation.golden_harness.GoldenRegressionHarness`)
Coordinates the end-to-end integration without mock shortcuts:
1. Ingests golden folder via `LocalFilesystemConnector` and `DiscoveryService`.
2. Extracts content using canonical parsers (`PdfExtractor`, `ExcelExtractor`, `WordExtractor`, `MarkdownExtractor`).
3. Indexes chunks into SQLite FTS5 vector/lexical store.
4. Generates standard 7-chapter CIL report blueprint using `ReportPlanner`.
5. Maps evidence deterministically using `EvidenceMapper`.
6. Executes local draft generation via `SectionGenerator`.
7. Audits every claim and table through `DeterministicVerifier`.
8. Enriches layout with photograph assets from `ImageAssetCatalog`.
9. Compiles final output using `PdfRenderer` and records all actions into SHA-256 chained `AuditLogger`.

---

## 3. REST API Surface

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/v1/evaluation/run-golden-suite` | Triggers asynchronous/synchronous golden dataset test suite execution |
| `GET` | `/api/v1/evaluation/latest-report` | Returns latest golden regression run metrics, coverage scores, and pass/fail status |

---

## 4. Verification & Validation

The suite is thoroughly verified via automated tests:
- `tests/evaluation/test_golden_dataset.py`: Verifies fixture generation, metadata validity, and ground truth schema.
- `tests/evaluation/test_metrics.py`: Tests recursive subsection traversal, 100% provenance verification, and zero-division fallbacks.
- `tests/evaluation/test_evaluation_api.py`: Tests the REST API endpoints and state retrieval.
- `tests/regression/test_golden_dataset_pipeline.py`: Validates the full vertical integration slice from raw files to metric calculations.
