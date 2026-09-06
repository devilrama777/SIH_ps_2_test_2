# 10 — PDF Generation & Document Rendering Engine Architecture

## Overview
Phase 8 implements Section 19 (*PDF Generation*) and Section 20 (*Two Report Visual Modes*) of the CIL Local AI Report Generator Master Implementation Specification.

The engine transforms intermediate `Report` domain models into publication-ready, print-quality corporate PDFs using an air-gapped, local Chromium printing pipeline with PyMuPDF fallback:
```
Intermediate Report JSON
           |
           v
+-------------------------------+
|       ReportHtmlBuilder       |  <-- Injects Template A (Classic) or B (Modern)
|  - Standalone HTML5 / CSS3    |  <-- Inserts Dynamic Table of Contents (TOC)
|  - Page-break controls        |  <-- Citations formatting [DOC:...] & [COORD:...]
|  - Layout-aware image markup  |  <-- Structured tables with column totals
+--------------+----------------+
               |
               v
+-------------------------------+
|          PdfRenderer          |  <-- Discovers local headless Chromium (Edge/Chrome)
|  - Headless PDF print engine  |  <-- Native @page & @top/@bottom running headers
|  - PyMuPDF story fallback     |  <-- Page count & file size verification
+--------------+----------------+
               |
               +--------------------------------------+
               |                                      |
               v                                      v
     {report_id}_{template}.pdf             {report_id}_{template}.html
     (Official Printable Document)          (Standalone Web/Interactive View)
```

## Key Components

### 1. Dual Visual Templates (`core/reports/pdf/templates/`)
- **Template A — Existing-Report-Inspired ("Classic")** (`classic.py`):
  - Formal navy (`#1a365d`) and dark charcoal palette.
  - Serif typography (`Georgia`, `Times New Roman`).
  - Formal double-bordered cover page, running header rules, bordered tabular layouts with shaded total rows.
- **Template B — Modern Corporate ("Modern")** (`modern.py`):
  - Contemporary dark slate (`#0f172a`) and electric blue (`#2563eb`) palette.
  - Clean sans-serif typography (`Inter`, system UI font stack).
  - Gradient hero cover page, pill-style metric badges, card-style narrative containers, borderless striped tables.

### 2. `ReportHtmlBuilder` (`core/reports/pdf/html_builder.py`)
- Takes domain `Report` model and optional `ImageAssetCatalog` assignments.
- Renders:
  - Formal Cover Page with corporate subsidiary branding, fiscal year badge, and confidentiality disclaimer.
  - Dynamic Table of Contents with multi-level section numbering and hyperlink anchors (`#sec_id`).
  - Section hierarchy (L1/L2/L3 headings).
  - Formatted narrative blocks with inline styled citations `<span class="citation-ref">`.
  - Structured tables with header repetition (`thead`) and bold totals.
  - Section image layout containers (Hero, two-column, 2x2 grid, or captioned figures).

### 3. `PdfRenderer` (`core/reports/pdf/renderer.py`)
- Automatic discovery of local Chromium engines across Windows, macOS, and Linux:
  - `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`
  - `C:\Program Files\Microsoft\Edge\Application\msedge.exe`
  - `C:\Program Files\Google\Chrome\Application\chrome.exe`
  - System `chromium`, `chrome`, or `msedge` on PATH.
- Executes headless Chromium print CLI:
  `--headless --disable-gpu --run-all-compositor-stages-before-draw --no-pdf-header-footer --print-to-pdf="output.pdf"`
- Fallback path using PyMuPDF document writer if Chromium is unavailable.
- Computes rendering telemetry: page count, file size in bytes, and execution duration.

### 4. REST API Endpoints
- `POST /api/v1/reports/{report_id}/export/pdf?template=modern`: Compiles Report JSON to PDF using selected template.
- `GET /api/v1/reports/{report_id}/export/pdf?template=modern`: Streams / downloads the PDF file.
- `GET /api/v1/reports/{report_id}/export/html?template=modern`: Streams / downloads the compiled HTML file.

### 5. Desktop UI: `PdfExportView.tsx`
- Interactive template switcher (Template A Classic vs Template B Modern Corporate).
- Telemetry summary card (Pages, Size, Duration, Engine).
- Direct Download PDF and Open HTML buttons.
- Full-height live embedded preview frame.
