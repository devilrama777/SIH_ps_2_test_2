# Canonical Document Model Specification (Section 9)

## 1. Overview

The **Canonical Document Model** is the unified, format-agnostic intermediate representation for all documents ingested into the CIL Local AI Report Generator. It decouples document parsing from downstream search, AI reasoning, and report generation.

Regardless of whether a document begins as:
- a digital PDF,
- a scanned PDF,
- a DOCX memo,
- an XLSX operational workbook,
- a CSV dataset, or
- an image/scan,

it is mapped into an instance of `CanonicalDocument`.

---

## 2. Core Entities

### 2.1 CanonicalDocument
```python
class CanonicalDocument(BaseModel):
    document_id: str             # e.g., "doc_e4a8b29f012c" (SHA-256 derived)
    source_reference: str        # Absolute filesystem path or URI
    source_hash: str             # SHA-256 fingerprint of raw file
    document_type: DocumentType  # DIGITAL_PDF, SCANNED_PDF, XLSX, etc.
    reporting_year: Optional[str] # e.g., "2024-25"
    reporting_period: Optional[str]# e.g., "March 2025" or "Q4"
    dates: List[str]             # Extracted content timestamps
    file_size_bytes: int
    created_at: Optional[datetime]
    modified_at: Optional[datetime]
    ingested_at: datetime
    metadata: Dict[str, Any]
    pages: List[Page]
    tables: List[Dict[str, Any]]
    images: List[Dict[str, Any]]
    links: List[Dict[str, Any]]
    markdown_content: Optional[str] # Secondary LLM-friendly view
```

### 2.2 DocumentElement
```python
class DocumentElement(BaseModel):
    element_id: str              # e.g., "el_doc1_p117_00042"
    document_id: str
    type: ElementType            # HEADING, PARAGRAPH, TABLE_CELL, SPREADSHEET_CELL, etc.
    page_number: Optional[int]   # 1-indexed page
    bbox: Optional[BoundingBox]  # [x0, y0, x1, y1] coordinates
    text: Optional[str]
    confidence: Optional[float]  # 0.0 - 1.0 (OCR confidence or 1.0 for digital)
    reading_order: Optional[int]
    metadata: Dict[str, Any]
```

### 2.3 SpreadsheetCoordinate
```python
class SpreadsheetCoordinate(BaseModel):
    workbook_name: str
    sheet_name: str
    cell: Optional[str]          # e.g., "G27"
    cell_range: Optional[str]    # e.g., "A1:H30"
    row: Optional[int]
    column: Optional[int]
    raw_value: Optional[Any]
    formatted_value: Optional[str]
```

---

## 3. Provenance Linkage

Every fact or number cited in a report retains a pointer:
```json
{
  "statement": "Coal production in the Northern sector reached 1,245.70 MT in March 2025.",
  "evidence": {
    "evidence_id": "ev_004291",
    "provenance": {
      "provenance_id": "prov_7fa918b201",
      "document_id": "doc_e4a8b29f012c",
      "source_reference": "C:/data/coal_production_report.xlsx",
      "spreadsheet_coord": {
        "workbook_name": "coal_production_report.xlsx",
        "sheet_name": "March",
        "cell": "G27",
        "raw_value": 1245.70
      },
      "extraction_method": "xlsx_cell",
      "document_date": "2025-03-31",
      "reporting_period": "March 2025"
    }
  }
}
```

This guarantees complete non-repudiation, zero hallucination of figures, and automated source jumping in the Source Viewer UI.
