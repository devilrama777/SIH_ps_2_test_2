# Architecture Document 18: Multi-Engine OCR & Layout Intelligence Subsystem

## 1. Context & Master Plan Reference
- **Section 7: Local AI & Document Processing Stack Selection**:
  - Evaluation of Docling vs. PaddleOCR / PP-StructureV3 vs. local lightweight raster engines.
  - Coordinate extraction, reading order preservation, and complex table structure recovery.
  - Strict air-gap constraint: Zero network roundtrips or reliance on remote OCR/vision APIs.
- **Section 31: Document Processing Pipeline Design**:
  - Distinguishes native digital PDFs from scanned / bitmap-only PDFs.
  - Page-level OCR triggering when native text density falls below threshold (`< 40` chars and has raster images).
- **Section 34: Performance Benchmarking Protocol**:
  - Empirical metrics: throughput (pages/sec), latency per page (ms), memory footprint (MB delta), character confidence, and table cell extraction accuracy.

---

## 2. Architecture Overview

```
                        +-------------------------------+
                        |       Input PDF Document      |
                        +---------------+---------------+
                                        |
                                        v
                       +---------------------------------+
                       |          PDFExtractor           |
                       |  - Extracts text blocks & links |
                       |  - Checks text density & images |
                       +----------------+----------------+
                                        |
                 [Native Text >= 40]   / \   [Scanned / Bitmap Page]
                 +--------------------+   +-----------------------+
                 |                                                |
                 v                                                v
    +-------------------------+                     +---------------------------+
    | Native Digital Pipeline |                     |   MultiEngineOCRManager   |
    | - BoundingBox extraction|                     +-------------+-------------+
    | - Reading order preserve|                                   |
    +------------+------------+            +----------------------+----------------------+
                 |                         |                      |                      |
                 |                         v                      v                      v
                 |               +------------------+   +-------------------+  +-------------------+
                 |               |  PaddleOCREngine |   |  DoclingOCREngine |  |  PyMuPDFOCREngine |
                 |               | (PP-StructureV3) |   |  (Layout Model)   |  |   (Raster OCR)    |
                 |               +---------+--------+   +---------+---------+  +---------+---------+
                 |                         |                      |                      |
                 |                         +----------------------+----------------------+
                 |                                                |
                 |                                                v
                 |                                  +---------------------------+
                 |                                  |       OCRPageResult       |
                 |                                  | - Lines with BoundingBox  |
                 |                                  | - Tables (headers & cells)|
                 |                                  | - Reading order & conf.   |
                 |                                  +-------------+-------------+
                 |                                                |
                 +-----------------------+------------------------+
                                         |
                                         v
                          +-----------------------------+
                          |      CanonicalDocument      |
                          | - DocumentElement list      |
                          | - DocumentType: SCANNED_PDF |
                          | - Page.ocr_applied = True   |
                          | - Markdown with provenance  |
                          +-----------------------------+
```

---

## 3. Component Details

### 3.1 Base Engine Contract (`core/extraction/ocr/base.py`)
- `BaseOCREngine`: Abstract interface requiring:
  - `engine_name: str`
  - `recognize_page(image_bytes: bytes, page_number: int) -> OCRPageResult`
  - `health_check() -> OCRHealth`
- `OCRPageResult`:
  - `lines: List[OCRTextLine]` (each with `text`, `bbox: BoundingBox`, `confidence`, `reading_order`, `is_heading`)
  - `tables: List[OCRTableResult]` (structured `headers: List[str]`, `rows: List[List[str]]`, `bbox: BoundingBox`, `confidence`)
  - `to_document_elements(document_id: str, start_index: int) -> List[DocumentElement]` seamlessly maps OCR results into canonical document elements.

### 3.2 Implemented OCR Engines
1. **PaddleOCR / PP-StructureV3 (`core/extraction/ocr/paddle_engine.py`)**:
   - Primary high-accuracy layout analysis and table recovery engine.
   - Detects layout regions (headings, paragraphs, tables) and preserves reading order.
   - Provides CPU fallback for air-gapped environments without CUDA drivers.
2. **Docling Layout Intelligence (`core/extraction/ocr/docling_engine.py`)**:
   - Multimodal document understanding framework adapter.
   - Converts scanned pages to structured markdown and tabular ASTs.
3. **PyMuPDF Raster OCR (`core/extraction/ocr/pymupdf_engine.py`)**:
   - Ultra-lightweight zero-dependency CPU bitmap layout analyzer.
   - Extracts bounding coordinates, line geometries, and table grid regions with high speed and low memory footprint.

### 3.3 MultiEngineOCRManager (`core/extraction/ocr/manager.py`)
- Registry of available OCR engines.
- Dynamic switching via REST API or configuration (`set_active_engine`).
- Automatic fault-tolerant fallback chain: if native PP-Structure or Docling is absent or throws an exception during processing, the manager automatically executes the next engine in the fallback chain without failing the document pipeline.

### 3.4 Benchmarking Harness (`core/extraction/ocr/benchmark.py`)
- `OCRBenchmarkHarness`: Evaluates OCR engines on synthetic test documents containing headings, operational paragraphs, and financial/production tabular grids.
- Computes:
  - Throughput: `pages_per_second`
  - Latency: `avg_latency_ms`
  - Character and detection confidence: `avg_confidence`
  - Table grid detection accuracy: `tables_detected`
  - Memory consumption: `ram_usage_mb` and `peak_ram_mb` using `psutil`
- Recommends the optimal engine based on hardware availability and throughput.

---

## 4. REST API Integration (`apps/processing/server.py`)
- `GET /api/v1/ocr/engines`: Returns active engine and health status for all registered engines.
- `POST /api/v1/ocr/engines/select`: Allows runtime selection of active OCR engine.
- `POST /api/v1/ocr/process-page`: Runs page image OCR on base64 payload and returns structured `OCRPageResult`.
- `POST /api/v1/ocr/benchmark`: Triggers benchmarking harness and returns `OCRBenchmarkReport`.
