# Report Planner & Dynamic Hierarchy Specification

## 1. Architectural Purpose

The **Report Planner subsystem** (`core/reports/planner/`) addresses the critical requirement in **Sections 13, 14, and 15** of the *CIL Local AI Report Generator Master Implementation Specification*:

> *Never ask the LLM to directly write a 300–400 page report in one prompt.*
>
> *Use: Evidence -> Report Planner -> Report Plan -> Section Evidence Sets -> Section Generation -> Validation -> Composition.*

The planner synthesizes structural insights from previous CIL annual reports (without copying text) and automatically adapts the table of contents to current-period evidence, inserting newly discovered chapters (e.g. *Digital Mine Transformation*, *First Mile Connectivity*, *Solar Power Expansion*).

```
+-----------------------------------------------------------------------------------------+
|                                  Evidence Ingestion Corpus                              |
|               (PDFs, Word Docs, Excel Spreadsheets, CSVs, Photographic Assets)          |
+-----------------------------------------------------------------------------------------+
                                             |
            +--------------------------------+--------------------------------+
            |                                                                 |
            v                                                                 v
+-------------------------------+                         +-------------------------------+
|    ReferenceReportAnalyzer    |                         |      TopicDiscoveryEngine     |
|   (Previous-Year Reference)   |                         |   (Current-Period Evidence)   |
| - Recurring corporate themes  |                         | - Scans emergent keywords     |
| - Table/Image frequency ratios|                         | - Classifies new initiatives  |
| - Section hierarchy outline   |                         | - Formulates discovery reasons|
+-------------------------------+                         +-------------------------------+
            |                                                                 |
            +--------------------------------+--------------------------------+
                                             v
                             +-------------------------------+
                             |         ReportPlanner         |
                             | - CIL Mandatory Baseline      |
                             | - Injects Discovered Chapters |
                             | - Builds Tree Hierarchy       |
                             +-------------------------------+
                                             |
                                             v
                             +-------------------------------+
                             |    EvidenceToSectionMapper    |
                             | - Hybrid FTS5 BM25 queries    |
                             | - Spreadsheet cell isolation  |
                             | - Sufficiency evaluation      |
                             +-------------------------------+
                                             |
                                             v
                             +-------------------------------+
                             |       ReportPlan / Skeleton   |
                             |    (Sections + Evidence Sets) |
                             +-------------------------------+
```

---

## 2. Dynamic Section Taxonomy

In accordance with Section 13, sections in the planned hierarchy are explicitly typed:

| Section Type | Enumeration | Description |
|---|---|---|
| Mandatory | `SectionType.MANDATORY` | Statutory or essential chapters present in all CIL subsidiary reports (e.g., Corporate Profile, Operational Review, Capex, DGMS Safety, Audited Accounts). |
| Recurring | `SectionType.RECURRING` | Standard annual chapters observed in the reference report that recur when evidence exists. |
| Optional | `SectionType.OPTIONAL` | Sections included only when requested by operators or when supporting evidence is robust. |
| Conditional | `SectionType.CONDITIONAL` | Triggered only when specific metrics cross a threshold (e.g., *Mine Water Community Potable Supply*). |
| Discovered | `SectionType.DISCOVERED` | Emerging subsection automatically formed when significant new initiatives are discovered in evidence. |
| New Top-Level | `SectionType.NEW_TOP_LEVEL` | Entirely new major chapters formed when substantial organizational transformation data is detected (e.g., *Digital Mine Transformation*). |

---

## 3. Evidence Packaging & Sufficiency Scoring

For each section node in the plan, `EvidenceToSectionMapper` compiles a `SectionEvidencePackage`:
- `ranked_evidence`: Ordered text chunks with BM25 + temporal scores.
- `spreadsheet_coordinates`: Explicit workbook, sheet, and cell addresses (e.g., `stats.xlsx > March > G27`).
- `sufficiency_score`: Floating point score ($0.0 \dots 1.0$) measuring evidence density.
- `is_sufficient`: Boolean flag indicating whether sufficient ground-truth material exists to generate the section without risk of hallucination.

---

## 4. API Endpoints

- `POST /api/v1/reports/plan`: Formulate a new dynamic report plan.
- `GET /api/v1/reports/plans`: List historical report plans.
- `GET /api/v1/reports/plans/{plan_id}`: Retrieve plan tree and evidence sets.
