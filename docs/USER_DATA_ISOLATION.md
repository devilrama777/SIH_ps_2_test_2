# MineIntel — Multi-User Data Isolation Architecture

## 1. Overview
In multi-analyst workstation environments, different local operators must have completely segregated workspaces and records. Data isolation is enforced strictly at the backend and database layer rather than merely hidden in the React UI.

## 2. Directory Hierarchy
Each authenticated user is allocated an isolated directory tree under `data/workspace/users/<user_id>/`:

```
data/workspace/
    users/
        usr_8f3a91.../
            ├── workspace/     (Scratch files, transient job state)
            ├── documents/     (User-ingested PDF, XLSX, DOCX sources)
            ├── reports/       (Draft and finalized statutory reports)
            ├── assets/        (Extracted figures, charts, photos)
            ├── indexes/       (User-specific vector/lexical embeddings)
            └── cache/         (OCR intermediate text and bounding boxes)
```

## 3. Database Ownership & Schema Enforcement
1. **Document Ownership**: The `documents` table in SQLite carries a dedicated `user_id` column with index `idx_documents_user`.
2. **FTS5 & Lexical Retrieval**: The hybrid search engine (`HybridSearchEngine`) scopes BM25 full-text queries:
   ```sql
   SELECT ... FROM fts_elements fts
   JOIN elements e ON fts.element_id = e.element_id
   JOIN documents d ON e.document_id = d.document_id
   WHERE fts_elements MATCH :query
     AND (d.user_id = :authenticated_user_id OR d.user_id = 'system')
   ```
   User A is prevented from retrieving or viewing documents uploaded by User B.

## 4. Agent Tool & Filesystem Sandboxing
Autonomous report editing tools (`core/reports/agent_tools.py`) operate strictly within the resolved boundary of the authenticated user's workspace path. Relative path navigation escaping the user's root (`../../`) is rejected with a `403 Forbidden` security block.

## 5. Clean User Switching
When User A logs out:
- All React state (`reports`, `dataSources`, `jobs`, `evidenceList`, `validationIssues`) is immediately purged.
- No cached reports or evidence fragments remain in DOM or localStorage.
- User B signing in sees an empty/new workspace specific to User B's account.
