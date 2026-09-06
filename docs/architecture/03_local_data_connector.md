# Local Data Connector & Ingestion Job System (Sections 4, 5, 6, 27)

## 1. Overview

Phase 1 delivers the local ingestion foundation for the **CIL Local AI Report Generator**. It implements the `DataConnector` abstraction for local folders, recursive file discovery, streaming SHA-256 fingerprinting, temporal metadata extraction, and a persistent, resumable processing job system.

---

## 2. Supported Formats (Section 3)

The connector strictly accepts:
- **PDF**: Digital and scanned documents (`.pdf`)
- **Office Word**: Microsoft Word documents (`.docx`)
- **Office Excel**: Spreadsheet workbooks (`.xlsx`)
- **Tabular Data**: Comma-separated values (`.csv`)
- **Plain Text**: Text files (`.txt`)
- **Images**: Photographs, diagrams, maps (`.jpg`, `.jpeg`, `.png`, `.tiff`, `.tif`)

Disallowed files (such as `.zip`, `.tar.gz`, `.pptx`) are explicitly filtered and rejected.

---

## 3. Security & Path Traversal Prevention

- Path inputs are normalized and resolved via `Path(target).resolve()`.
- Symlink traversal outside the target directory root is prohibited (`followlinks=False`).
- Hidden directories (`.git`, `.venv`, `__pycache__`, etc.) and system volumes are automatically pruned from traversal.

---

## 4. Streaming Cryptographic Fingerprinting

To safely process 300–400 page PDFs and multi-megabyte datasets without exhausting system memory, file hashing uses 64KB chunked buffers:
```python
CHUNK_SIZE = 64 * 1024
hasher = hashlib.sha256()
with open(path, "rb") as f:
    while chunk := f.read(CHUNK_SIZE):
        hasher.update(chunk)
```
This produces a deterministic SHA-256 fingerprint used as a stable `document_id` and for deduplication across ingestion runs.

---

## 5. Temporal Organization (Section 5)

The system indexes temporal attributes regardless of folder organization:

### Case A: Directory Hierarchy
Example: `2024-25/Q4/March/production.xlsx`
- `financial_year`: `"2024-25"`
- `reporting_quarter`: `"Q4"`
- `reporting_month`: `"March"`
- `reporting_period`: `"March 2024"`

### Case B: Embedded in Filename
Example: `coal_production_report_march_2025.csv` or `CIL_Annual_Report_2024_25_Full_Data_Report.pdf`
- `financial_year`: `"2024-25"`
- `reporting_month`: `"March"`
- `reporting_period`: `"March 2025"`
- `source_method`: `"filename"`

Filesystem modification times are explicitly **not** assumed to represent the true reporting period.

---

## 6. Resumable Ingestion Job System (Section 6 & 27)

Jobs are persisted in a local SQLite database (`data/workspace/ingestion_jobs.db`):
- `jobs`: Tracks `job_id`, `status`, `progress` (0.0–100.0%), `current_stage`, `total_items`, `processed_items`, and `failed_items`.
- `job_items`: Records completed file paths and SHA-256 hashes.
- `job_errors`: Logs stage-specific failures without aborting the entire batch.

### Resumability Guarantee:
If a 500-file batch is interrupted at file 317, re-running the job checks `is_item_completed(job_id, file_hash)` and skips already completed files, ensuring zero redundant work.
