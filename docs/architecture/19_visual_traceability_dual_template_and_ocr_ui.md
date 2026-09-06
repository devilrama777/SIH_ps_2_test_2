# Architecture Document 19: Visual Traceability Inspector, Dual-Template Live Preview & OCR Subsystem UI

## 1. Context & Master Plan Reference
- **Section 20: Two Report Visual Modes**:
  - Classic CIL Annual Report style (traditional government PSU format, formal typography, official CIL brand headers, bordered tables, and statutory sign-offs).
  - Modern Corporate Annual Report style (clean contemporary visual design, vibrant accents, asymmetrical visual grids, stat callouts).
  - Live interactive HTML preview rendered directly from the canonical intermediate `Report` model.
- **Section 21: Source Traceability UI & Visual Bounding Box Inspector**:
  - Interactive source inspector allowing users to click any statement, table, or number and see its exact visual bounding box highlighted on the rendered source document page.
  - Full coordinate preservation (`[x0, y0, x1, y1]`) rendered on-the-fly under strict local air-gapped CPU operation.
- **Section 33: User Interface & Section 7/34 OCR Management**:
  - Dedicated Multi-Engine OCR & Layout Intelligence control view (`OCRControlView.tsx`).
  - Runtime switching between Docling, PaddleOCR / PP-StructureV3, and PyMuPDF Raster OCR.
  - One-click empirical benchmark harness execution displaying comparative pages/second throughput, latency, confidence, and memory footprint.

---

## 2. Architecture & Data Flow

```
                      +------------------------------------------+
                      |         Desktop Application UI           |
                      |  - SourceTraceabilityView.tsx            |
                      |  - PdfExportView.tsx (Live HTML Preview) |
                      |  - OCRControlView.tsx                    |
                      +--------------------+---------------------+
                                           |
                       HTTP GET (Preview / Traceability / OCR)
                                           |
                                           v
    +-------------------------------------------------------------------------------+
    |                          FastAPI Local Backend                                |
    +--------------------------------------+----------------------------------------+
    |                                      |                                        |
    v                                      v                                        v
+------------------------+  +-------------------------------+  +--------------------------+
| GET /sources/page-prev |  | GET /reports/{id}/preview-html|  | /api/v1/ocr/             |
|                        |  |                               |  | - engines                |
| 1. Resolve Document &  |  | 1. Load intermediate Report   |  | - engines/select         |
|    Page in Workspace   |  |    model JSON                 |  | - process-page           |
| 2. PyMuPDF fitz raster |  | 2. HTMLReportBuilder renders  |  | - benchmark              |
|    dpi=150 to RGBA     |  |    Classic or Modern mode     |  |                          |
| 3. PIL overlay: amber  |  | 3. Return compiled standalone |  | Managed by               |
|    box & crimson border|  |    HTML with embedded styles  |  | MultiEngineOCRManager    |
| 4. Return image/png    |  | 4. Return text/html           |  | & OCRBenchmarkHarness    |
+------------------------+  +-------------------------------+  +--------------------------+
```

---

## 3. Implementation Details

### 3.1 Visual Bounding Box Page Preview (`GET /api/v1/sources/page-preview`)
- Located in `apps/processing/server.py`.
- Accepts parameters:
  - `document_id`: Canonical document identifier.
  - `source_reference`: Direct path or filename of source file.
  - `page_number`: 1-indexed page number.
  - `element_id`: Specific `DocumentElement` ID whose bounding box should be highlighted.
  - `bbox`: Explicit bounding box coordinates (`x0,y0,x1,y1`).
- Execution:
  - If the physical PDF is present, PyMuPDF renders the page to a PNG pixmap at 150 DPI.
  - If the physical file is an image (PNG/JPG/TIFF), PIL opens the file directly.
  - If synthetic or in unit test mode, a clean synthetic page layout is dynamically generated.
  - PIL creates an RGBA overlay layer, clamping coordinates to the image bounds and painting a semi-transparent amber fill (`(255, 215, 0, 85)`) with a crisp crimson border (`(220, 38, 38, 255)`) and a `SOURCE: {element_id}` tag.
  - Returns `image/png` response for direct display in frontend `<img>` tags or canvas elements.

### 3.2 Dual-Template Live HTML Preview (`GET /api/v1/reports/{report_id}/preview-html`)
- Located in `apps/processing/server.py`.
- Accepts `report_id` and `template` (`classic` or `modern`).
- Loads the intermediate `Report` JSON model from `data/workspace/reports/{report_id}.json`.
- Runs `pdf_renderer.render_report(report, template_name=template)` to compile the full HTML representation with CSS stylesheets, typography, tables, and provenance footnotes.
- Returns raw `text/html` suitable for desktop iframe rendering.

### 3.3 Desktop OCR & Layout Intelligence View (`OCRControlView.tsx`)
- Located in `apps/desktop/src/components/OCRControlView.tsx`.
- Registered as `"ocr"` tab in `Sidebar.tsx`, `Header.tsx`, and `App.tsx`.
- Features:
  - Status cards for all registered local engines (`PaddleOCR/PP-StructureV3`, `Docling Multimodal`, `PyMuPDF Raster OCR`).
  - Active engine switcher with one-click runtime reassignment.
  - Empirical benchmark runner calling `POST /api/v1/ocr/benchmark` and rendering a responsive metrics table (Throughput pps, Latency ms, Confidence %, Tables Found, RAM Footprint MB).
  - Interactive OCR sandbox to verify layout recognition and coordinate extraction.
