# Document Extraction & Canonical Population (Sections 6, 7, 8, 9)

## 1. Overview

Phase 2 implements deterministic, format-specific extraction engines that transform unstructured and semi-structured local documents into the **Canonical Document Model** with coordinate-level provenance tracking.

---

## 2. Format Parsers & Strategies

### 2.1 PDF Extraction (`core/extraction/pdf_extractor.py`)
- Leverages PyMuPDF (`fitz`) for fast, local, native extraction.
- Preserves exact page dimensions: `width` and `height`.
- Extracts text blocks with bounding boxes: `[x0, y0, x1, y1]`.
- Implements heading vs paragraph heuristics based on font sizing, title-casing, and line breaks.
- **Scanned PDF Strategy (Section 7)**:
  - If a page contains full-page raster imagery with <40 characters of native text, it is flagged with `has_scanned_content = True`.
  - The document type is classified as `DocumentType.SCANNED_PDF`.
  - Image coordinates and bounding boxes are preserved for OCR processing.
- Extracts embedded hyperlinks with target URIs and bounding boxes.

### 2.2 Excel Extraction (`core/extraction/xlsx_extractor.py`)
- Leverages `openpyxl` with `data_only=True` to retrieve calculated values from formulas.
- Extracts workbooks across all worksheets.
- Populates `tables` structures with detected headers and body rows.
- Creates individual `DocumentElement` instances of type `ElementType.SPREADSHEET_CELL`.
- Generates exact cell-level coordinates:
  ```json
  {
    "workbook_name": "coal_stats.xlsx",
    "sheet_name": "March",
    "cell": "G27",
    "row": 27,
    "column": 7,
    "raw_value": 1245.70
  }
  ```

### 2.3 Word Document Extraction (`core/extraction/docx_extractor.py`)
- Leverages `python-docx` to extract paragraphs, heading levels 1–5, and embedded tables.
- Preserves reading order and table cell contents.

### 2.4 CSV & Plain Text (`core/extraction/text_csv_extractor.py`)
- CSV: Parses tabular records, header rows, and cell coordinates.
- TXT: Breaks content into paragraphs, detecting chapter/section titles.

### 2.5 Images (`core/extraction/image_extractor.py`)
- Leverages `Pillow` to inspect dimensions, aspect ratio, color mode, and DPI.

---

## 3. Unified Dispatcher & Persistence

- `UnifiedDocumentExtractor` inspects the detected format and routes the file to the corresponding extractor.
- The resulting `CanonicalDocument` is persisted to `data/workspace/canonical_documents/{document_id}.json`.
- The document ID is deterministically derived from `generate_document_id(source_uri, file_bytes)` ensuring reproducible provenance.
