# Phase 32: Layout Intelligence & Chart OCR Analysis

## 1. Overview
In accordance with Section 9, 10, and 18 of the CIL Local AI Report Generator Master Implementation Specification, mining operational reports contain non-tabular visual analytical components: bar charts, monthly trajectory graphs, area plots for cumulative overburden removal, and percentage distribution diagrams.

Phase 32 implements:
1. **Local-First Chart Heuristics**:
   - Analyzes aspect ratio and color histogram variance to distinguish synthetic analytical charts/diagrams from natural field photographs without invoking cloud vision APIs.
2. **Chart Classification & Parsing**:
   - Classifies chart types (`bar`, `line`, `pie`, `area`) based on contextual cues.
   - Extracts structured numerical data points (`series`, `label`, `value`, `unit`) from local OCR text blocks.
3. **Element Enhancement Pipeline**:
   - Promotes generic `ElementType.IMAGE` or visual elements to `ElementType.CHART` with typed `ChartMetadata`.

## 2. Component Architecture

```
Image / Page Element
         │
         ▼
[ChartExtractor.is_chart_heuristic()]
   ├── Aspect ratio bounds [0.25 - 4.0]
   └── Palette color density analysis
         │
         ▼
[MultiEngineOCRManager.process_page_image()]
         │
         ▼
[ChartExtractor.parse_data_points_from_ocr()]
   └── Regex extraction: Label + Numerical Value + Unit (MT / %)
         │
         ▼
[DocumentElement(type=ElementType.CHART, metadata={"chart_metadata": ...})]
```

## 3. Verification & Compliance
- Tested via `tests/extraction/test_chart_extraction.py`:
  - `test_chart_heuristic`: verified discrimination on synthesized visual graphs.
  - `test_classify_chart_type`: verified categorical mapping of report titles.
  - `test_parse_data_points_from_ocr`: verified regex numeric extraction with units.
  - `test_enhance_element_to_chart`: verified schema transformation to `ElementType.CHART`.
- 100% test pass rate achieved.
