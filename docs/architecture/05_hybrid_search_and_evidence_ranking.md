# Hybrid Search & Evidence Ranking (Section 10 & 11)

## 1. Overview

Phase 3 delivers the hybrid evidence retrieval engine. Rather than relying on black-box semantic retrieval alone, it combines:
1. **SQLite FTS5 BM25** full-text lexical search,
2. **Temporal metadata filters & boosts** (financial years, reporting quarters, months),
3. **Format & source type filtering**,
4. **Coordinate-level provenance resolution** down to page bounding boxes and spreadsheet cells.

---

## 2. SQLite Database & FTS5 Architecture (Section 10)

The persistence layer (`data/workspace/cil_report_intel.db`) contains:
- `documents`: Stores document identity, SHA-256 fingerprint, source URI, and reporting periods.
- `elements`: Stores atomic paragraphs, headings, spreadsheet cells, and bounding boxes.
- `tables`: Stores table schemas and row records.
- `provenance`: Links each element to its immutable provenance coordinates.
- `fts_elements` (FTS5): Porter-stemmed unicode61 full-text index on element text, document ID, and reporting period.

---

## 3. Hybrid Retrieval & Evidence Ranking (Section 11)

```text
User / Agent Query
        │
        ├──> FTS5 BM25 Lexical Score (50%)
        ├──> Temporal Match Boost (30%)
        └──> Exact Provenance Grounding (20%)
        │
        ▼
   Result Fusion
        │
        ▼
   Ranked Evidence List (with bounding boxes & spreadsheet coordinates)
        │
        ▼
   Report Planner & Section Generation Context
```

### Example Section 11 Query Execution:
`Query: "Find all March 2025 operational performance information."`
- Matches `"operational"`, `"performance"`, `"information"` via FTS5 BM25.
- Applies a `+0.2` score boost for documents indexed under `March 2025` or containing `2025-03` timestamps.
- Returns `RankedEvidence` referencing `Sheet: March, Cell: G27, Value: 1245.70`.
