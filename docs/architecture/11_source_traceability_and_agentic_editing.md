# 11 — Source Traceability & Agentic Review System Architecture

## Overview
Phase 9 implements Section 21 (*Source Traceability UI*), Section 22 (*Human + Agent Review System*), and Section 23 (*Agent Tool Security*) of the CIL Local AI Report Generator Master Implementation Specification.

The system empowers domain specialists and corporate auditors to:
1. Inspect any factual statement, table cell, or figure down to primary source PDF page text or spreadsheet cell coordinates (`[DOC:...]` and `[COORD:...]`).
2. Issue natural-language correction commands to a local editing agent (e.g., *"The production figure in this section is incorrect. Re-check the source and correct it."*).
3. Review structured line diffs and deterministic validation results before approving modifications.
4. Execute edits via controlled, security-gated tool layers that prevent arbitrary filesystem/network access.

```
+-------------------------------------------------------------+
|                      User Instruction                       |
| "The production figure is inaccurate. Update to 84.5 MT."   |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                     ReportEditingAgent                      |
|                                                             |
| 1. Locate affected section in Report JSON                   |
| 2. Query primary evidence via ControlledAgentTools          |
|    - search_documents(query)                                |
|    - get_source(doc_id)                                     |
|    - get_page(doc_id, page_number)                          |
| 3. Re-ground narrative using Local AI Gateway (SYSTEM_FACT)  |
| 4. Deterministic validation via ValidationEngine            |
| 5. Compute line diff (difflib compare)                      |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                        EditProposal                         |
| - proposal_id, diff_lines (+, -, ' ')                       |
| - original_text vs proposed_text                            |
| - validation_status (VALID / WARNING)                       |
+------------------------------+------------------------------+
                               |
                +--------------+--------------+
                |                             |
     [User Accepts Change]         [User Rejects Change]
                |                             |
                v                             v
   Report updated on disk           Proposal discarded
   (version bumped to v+1)          (report unchanged)
```

## Key Components

### 1. `SourceTraceabilityService` (`core/reports/traceability/viewer.py`)
- Resolves citations `[DOC:filename:Pxx]` and `[COORD:workbook:sheet:cell]` to canonical document elements.
- For PDFs: extracts page-level text snippets and element bounding boxes.
- For Spreadsheets: resolves workbook, sheet name, exact cell address (e.g. `G27`), raw numeric value, and formatted text.

### 2. `ControlledAgentTools` (`core/reports/agent/tools.py`)
- Implements Section 23 security sandboxing.
- Authorizes and executes discrete operations without arbitrary OS execution:
  - `search_documents(query, limit)`
  - `get_source(document_id)`
  - `get_page(document_id, page_number)`
  - `get_image(asset_id)`

### 3. `ReportEditingAgent` (`core/reports/agent/editing_agent.py`)
- Takes `report_id`, `section_id`, and `user_instruction`.
- Generates an `EditProposal` without blindly modifying the report.
- Computes unified diff lines (`+` additions, `-` deletions, ` ` unchanged).
- Reruns numerical, temporal, and provenance validation on the proposed section.
- Provides human approval gates: `accept_proposal(proposal_id)` and `reject_proposal(proposal_id)`.

### 4. REST API Endpoints
- `GET /api/v1/traceability/resolve`: Resolves source citation coordinates to snippet text and spreadsheet cells.
- `POST /api/v1/reports/{report_id}/edit-agent`: Invokes the agent to evaluate evidence and construct an `EditProposal`.
- `POST /api/v1/reports/proposals/{proposal_id}/accept`: Human approval to apply changes and increment report version.
- `POST /api/v1/reports/proposals/{proposal_id}/reject`: Discards proposal without changing report.

### 5. Desktop UI: `SourceTraceabilityView.tsx`
- Interactive Coordinate Inspector with presets for PDF page references and spreadsheet coordinates.
- Primary source excerpt viewer displaying document type badges and text matrices.
- Agentic review box with natural language prompt input and interactive color-coded diff viewer.
- Accept / Reject action buttons with instant feedback.
