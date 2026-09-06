# Phase 31: Advanced Temporal Query & Timeline Indexing Engine

## 1. Overview
Section 5 and Section 11 of the Coal India Local AI Report Generator specification mandate time-aware intelligence and structured retrieval across multi-year reporting cycles (e.g. FY 2023-24, FY 2024-25, quarters Q1–Q4, and specific months like March or October).

Phase 31 implements:
1. **Natural Language Temporal Parsing**:
   - Automated extraction of financial years (`FY 2023-24`, `2024-25`), reporting quarters (`Q1`–`Q4`), calendar months (`March`, `October`), and 4-digit calendar years from user prompts.
   - Clean query derivation for keyword and BM25 FTS5 retrieval.
2. **Chronological Clustering**:
   - Groups retrieved multi-source evidence into distinct temporal periods (e.g. `2023-24 (March 2024)`, `2024-25 (October 2024)`).
3. **Temporal REST API**:
   - `POST /api/v1/search/temporal` exposing temporal querying directly to Tauri frontend and background workers.

## 2. Architecture & Components

```
User Temporal Query ("Find all March 2024 coal production evidence")
           │
           ▼
[TemporalQueryEngine.parse_temporal_query()]
   ├── extract_temporal_metadata() -> FY, Quarter, Month, Year
   └── Cleaned Query: "coal production"
           │
           ▼
[HybridSearchEngine.search()] (SQLite FTS5 BM25)
           │
           ▼
[Temporal Post-Filter & Score Boost]
           │
           ▼
[Timeline Clustering & Chronological Bucketing]
           │
           ▼
[TemporalQueryResult] -> Timeline Clusters + Ranked Evidence
```

## 3. Verification & Compliance
- Full integration tested via `tests/retrieval/test_temporal_query_engine.py`:
  - `test_parse_natural_language_temporal_queries`: validated regex parsing of FY, quarters, months, and years.
  - `test_temporal_search_indexing_and_clustering`: validated multi-document ingestion and chronological clustering.
  - `test_temporal_search_rest_api`: validated FastAPI HTTP endpoint response schema.
- Passed 3/3 tests with 100% pass rate.
