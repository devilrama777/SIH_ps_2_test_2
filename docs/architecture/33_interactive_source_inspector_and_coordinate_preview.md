# Phase 33: Interactive Source Inspector & Coordinate Preview

## 1. Overview
Section 1.4, Section 11, and Section 15 of the CIL Local AI Report Generator specification mandate coordinate-level traceability. Every numeric figure, table cell, or statement generated must link to exact document coordinates:
- PDF/Scanned Documents: Page number and bounding box `[x0, y0, x1, y1]`.
- Spreadsheets (XLSX/CSV): Workbook name, sheet name, cell identifier (e.g., `G27`), and row/column index.

Phase 33 provides:
1. **Interactive SVG Coordinate Overlays**:
   - Zero-dependency, lightweight vector overlays projected over source page canvases.
   - Semi-transparent highlight boxes with hover tooltips displaying element identifiers, confidence scores, and raw textual snippets.
2. **Spreadsheet Cell Matrix Inspector**:
   - Lightweight tabular visualization placing the extracted cell within its local sheet context (surrounding rows and columns).
3. **Audit REST API**:
   - `POST /api/v1/inspector/visualize` enabling the desktop frontend and auditor views to request coordinate previews on-the-fly.

## 2. Component Workflow

```
[Auditor Clicks Generated Metric / Table Row]
                       │
                       ▼
[ProvenanceRecord.bbox or spreadsheet_coord]
                       │
                       ▼
[VisualSourceInspector.create_inspector_from_provenance()]
       │                                     │
       ├─ (If BoundingBox)                   └─ (If SpreadsheetCoordinate)
       ▼                                     ▼
[generate_svg_overlay()]              [render_spreadsheet_grid()]
  • SVG <rect> bounds                   • HTML Table Context
  • Tooltip & Confidence badge           • Highlighted Target Cell
                       │
                       ▼
[VisualInspectorReport] -> HTML Component / Overlay Canvas
```

## 3. Verification & Compliance
- Verified via `tests/reports/test_visual_coordinate_preview.py`:
  - `test_generate_svg_overlay`: verified SVG structure, viewBox, coordinates, and labels.
  - `test_render_spreadsheet_grid`: verified workbook, sheet, cell styling, and surrounding context.
  - `test_create_inspector_from_provenance`: verified seamless conversion of `ProvenanceRecord`.
  - `test_visual_inspector_rest_api`: verified REST API invocation and response schema.
- 100% test pass rate achieved.
