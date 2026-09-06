# 08 — Content Generation & Deterministic Validation Engine Architecture

## Overview
Phase 6 implements Section 16 (*Section Content Generator*) and Section 17 (*Deterministic Validation Engine*) of the CIL Local AI Report Generator Master Implementation Specification.

The core design principle is:
> **The LLM is NEVER the source of truth for numbers, dates, or arithmetic.**
> Generation is strictly constrained by an explicit `SectionEvidencePackage`. The deterministic validation engine enforces mathematical invariants, temporal alignment, and coordinate-level provenance without invoking an LLM.

```
+----------------------------+
|        ReportPlan          |
+--------------+-------------+
               |
               v
+----------------------------+
|      SectionGenerator      |  <-- Local AI Gateway (Rule-based / GGUF)
| - Formats Evidence Package |  <-- Enforces [DOC:..] & [COORD:..] citations
| - Discovers Insufficiency  |  <-- Flags missing primary evidence
+--------------+-------------+
               |
               v
+----------------------------+
|      Intermediate Report   |  <-- Domain Report model with NarrativeBlocks
+--------------+-------------+
               |
               v
+-------------------------------------------------------------+
|               Deterministic Validation Engine               |
|                                                             |
| +---------------------+  +--------------------------------+ |
| | NumericalValidator  |  | TemporalValidator              | |
| | - % sum (~100.0%)   |  | - Fiscal year alignment        | |
| | - Unit collisions   |  | - Obsolete historical dates    | |
| | - Table column sums |  +--------------------------------+ |
| +---------------------+                                     |
| +---------------------+  +--------------------------------+ |
| | ProvenanceValidator |  | StructuralValidator            | |
| | - Coordinate syntax |  | - Mandatory statutory chapters | |
| | - Uncited numbers   |  | - Heading hierarchy nesting    | |
| +---------------------+  +--------------------------------+ |
|                                                             |
| Visual Bounds (cols > 10) & Link URL Scheme Validation      |
+------------------------------+------------------------------+
                               |
                               v
               +-------------------------------+
               |       ValidationReport        |
               | - Overall status (Pass/Warn)  |
               | - Blocking errors vs warnings |
               | - JSON audit persistence      |
               +-------------------------------+
```

## Key Components

### 1. `SectionGenerator` (`core/reports/generator/section_generator.py`)
- Takes an individual `PlannedSection` containing a verified `SectionEvidencePackage`.
- If evidence is absent or empty, yields a `NarrativeBlock` marked `insufficient_evidence=True` and tags the section with `ValidationStatus.WARNING`.
- When evidence exists, compiles the evidence into a citation-grounded prompt adhering to `SYSTEM_PROMPT_FACTUAL`.
- Parses generated text paragraphs and extracts bracketed citations `[DOC:filename:Pxx]` and `[COORD:workbook:sheet:cell]` into structured `ProvenanceRecord` and `EvidenceReference` models.

### 2. `MasterReportGenerator` (`core/reports/generator/report_generator.py`)
- Iterates over planned sections node by node.
- Constructs the domain `Report` intermediate representation.
- Invokes the `ValidationEngine` across all sections and document hierarchy.
- Persists both `{report_id}.json` and `{report_id}_validation.json` into `data/workspace/reports/`.

### 3. `ValidationEngine` (`core/validation/`)
Composed of four specialized deterministic checkers:
- **`NumericalValidator`**:
  - Checks percentage distributions (sum within `[98.5%, 101.5%]`).
  - Flags unit collisions (e.g. Mixing MT and Tonnes without conversion factor).
  - Verifies tabular arithmetic (table `Total` row matches column sum).
- **`TemporalValidator`**:
  - Compares 4-digit years in text against the report's target fiscal period.
  - Flags text exclusively referencing years older than 2 years from the target period.
- **`ProvenanceValidator`**:
  - Identifies quantitative claims (MT, crores, %, MW, ₹) lacking evidence references.
  - Validates syntax and existence of citations.
- **`StructuralValidator`**:
  - Enforces mandatory statutory chapters (*Corporate Overview*, *Operational Performance*, *Financial Highlights*, *Safety*, *Auditors' Report*).
  - Validates heading level nesting (e.g. disallows jumping directly from level 1 to level 3).

### 4. REST API Endpoints
- `POST /api/v1/reports/generate`: Generates report and validation findings from an approved `ReportPlan`.
- `GET /api/v1/reports`: Lists generated reports.
- `GET /api/v1/reports/{report_id}`: Retrieves full domain `Report` document.
- `GET /api/v1/reports/{report_id}/validation`: Retrieves `ValidationReport`.
- `POST /api/v1/reports/{report_id}/validate`: Re-runs deterministic audit checks on an existing report.

### 5. Desktop Views
- **`ReportEditorView.tsx`**: Two-column layout with Document Hierarchy TOC, section-level validation badges, narrative blocks, and clickable evidence coordinate pills.
- **`ValidationView.tsx`**: KPI dashboard (Audit Gate, Blocking Errors, Warnings, Total Inspected Issues), category filters, and detailed findings list.
