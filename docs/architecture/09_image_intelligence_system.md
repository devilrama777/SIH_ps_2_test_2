# 09 — Image Intelligence System Architecture

## Overview
Phase 7 implements Section 18 (*Image Intelligence System*) of the CIL Local AI Report Generator Master Implementation Specification.

Images are not simply pasted into the corporate report; they pass through an asset intelligence pipeline:
```
Raw Local Images (PNG, JPG, WEBP)
           |
           v
+-------------------------------+
|       ImageAssetAnalyzer      |  <-- Pillow-powered technical profiling
|  - Dimensions (width, height) |  <-- Aspect ratio calculation
|  - Exact SHA-256 hash         |  <-- 64-bit dHash perceptual hashing
|  - Quality grading            |  <-- Semantic keyword taxonomy
+--------------+----------------+
               |
               v
+-------------------------------+
|       ImageAssetCatalog       |  <-- SQLite persistent database (assets.db)
|  - Bitwise deduplication      |  <-- Perceptual similarity (Hamming dist <= 4)
|  - Tag filtering & search     |  <-- Section-to-asset assignments
+--------------+----------------+
               |
               v
+-------------------------------+
|  DeterministicLayoutSelector  |  <-- Deterministic placement decision
|  - Single Hero Banner         |  <-- Two-column (text + image)
|  - 2x2 Image Grid             |  <-- Standard image with caption
|  - Controlled Spacing         |  <-- Semantic HTML/CSS container markup
+-------------------------------+
```

## Key Components

### 1. `ImageAsset` & `ImageAssetAssignment` (`core/assets/models.py`)
- Represents image files with:
  - Technical metrics (`width`, `height`, `aspect_ratio`, `dpi`, `file_size_bytes`, `format`).
  - Cryptographic & perceptual fingerprints (`sha256_hash`, `phash` 16-character hex dHash).
  - Quality classification (`EXCELLENT`, `ACCEPTABLE`, `LOW_RES`, `UNSUITABLE`).
  - Provenance traceability (`provenance_id`, `source_document_id`, `page_number`).
  - Deduplication status (`is_duplicate`, `duplicate_of`).
  - Recommended layout and taxonomy tags (`mining`, `machinery`, `sustainability`, `safety`, `dispatch`, `csr`, `governance`).

### 2. `ImageAssetAnalyzer` (`core/assets/analyzer.py`)
- Computes SHA-256 streaming hash over 64KB blocks.
- Computes 64-bit Difference Hash (dHash) using PIL resize to 9x8 grayscale, comparing adjacent pixels per row to produce a 16-character hex fingerprint.
- Evaluates Hamming distance between perceptual hashes.
- Determines quality grade based on publication standards (e.g., width < 150px -> `UNSUITABLE`, >= 1400px -> `EXCELLENT`).

### 3. `ImageAssetCatalog` (`core/assets/catalog.py`)
- Backed by SQLite (`data/workspace/assets.db`).
- On registration, checks if exact SHA-256 already exists; if so, marks `is_duplicate=True` and links `duplicate_of`.
- Performs perceptual near-duplicate scan against existing non-flat hashes with Hamming distance threshold <= 4.
- Persists assignments linking assets to report sections with layout mode, captions, and display order.

### 4. `DeterministicLayoutSelector` (`core/assets/layout_selector.py`)
- Rules for layout determination:
  - 1 widescreen image (aspect ratio >= 1.6, width >= 1000px) -> `single_hero`
  - 1 tall portrait image (aspect ratio <= 0.85) -> `two_column`
  - Exactly 4 images in section -> `grid_2x2`
  - 2-3 images or standard landscape -> `with_caption` or `controlled_spacing`
- Generates clean semantic HTML/CSS markup used directly by the PDF rendering engine in Phase 8.

### 5. Desktop UI: `AssetManagerView.tsx`
- Interactive visual asset gallery with quality grade pills and duplicate badges.
- Filtering by domain tags (*mining*, *machinery*, *sustainability*, *safety*, *dispatch*, *csr*, *governance*).
- Inspector panel showing technical specs, perceptual dHash, local path, and section assignment controls.
