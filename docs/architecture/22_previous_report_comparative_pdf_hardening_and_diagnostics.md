# Architecture Document 22: Previous Report Comparative Analysis, Industrial PDF Print Engine Hardening, & Air-Gapped Diagnostics

## 1. Context & Architectural Overview
Adhering to **Section 14 (Previous Report Analysis)**, **Section 19 & 20 (PDF Generation & Visual Modes)**, and **Section 35 (Observability & Air-Gapped Diagnostics)** of the *Master Implementation Specification*, this document details:
1. **Comparative Report Analysis & YoY Synthesis**: Automated cross-year structural diffing and variance calculations ($\Delta$ absolute, $\Delta\%$ growth) across key Coal India performance indicators.
2. **Industrial PDF Print Engine Hardening**: Dynamic subsidiary running headers, cover page suppression (`@page :first`), `break-inside: avoid` table and figure pagination protection, and clickable Table of Contents anchors.
3. **Air-Gapped Diagnostic & Audit Packaging**: Sanitized, SHA-256 verifiable support bundle generation stripping private tokens and confidential document payloads.

---

## 2. Section 14: Previous Report Comparative Intelligence

### 2.1 Cross-Report Structural Diffing
When analyzing previous-year subsidiary reports against newly planned outlines:
$$\text{Structural Similarity} = \frac{2 \times (|\text{Retained}| + |\text{Renamed}|)}{|\text{Prior Sections}| + |\text{Current Sections}|} \times 100\%$$

- **Retained Sections**: Exact normalized semantic match.
- **Renamed Sections**: Detected via token-overlap intersection (removing section digits, stemming possessives, matching core operational keywords).
- **Added Sections**: Emerging chapters (e.g. ESG & Solar Initiatives, First Mile Connectivity).
- **Removed Sections**: Deprecated or merged chapters.

### 2.2 Year-over-Year (YoY) Metric Variance Formulations
For each standardized Coal India operational or financial metric:
$$\Delta_{\text{abs}} = M_{\text{current}} - M_{\text{prior}}$$
$$\Delta\% = \begin{cases} \left(\frac{\Delta_{\text{abs}}}{M_{\text{prior}}}\right) \times 100\% & \text{if } M_{\text{prior}} > 0 \\ 100.0\% & \text{if } M_{\text{prior}} = 0 \land M_{\text{current}} > 0 \\ 0.0\% & \text{otherwise} \end{cases}$$

Trend evaluation accounts for directional preference:
- **Higher is Better**: Raw Coal Production, Coal Offtake, Gross Revenue, Profit After Tax, Afforestation Area.
- **Lower is Better**: Fatal Accidents, Serious Injuries, Equipment Breakdowns.

Standard output is formatted into publication-grade `YoYComparativeTable` instances with full source provenance citations.

---

## 3. Section 19 & 20: PDF Print Hardening & Paged Media CSS

### 3.1 Paged Media Dynamic Running Headers
Running headers are injected dynamically from active subsidiary settings and reporting periods:
```css
@page {
  size: A4;
  margin: 18mm 16mm 18mm 16mm;
  @top-left {
    content: "BHARAT COKING COAL LIMITED";
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    font-size: 8pt;
    font-weight: 700;
    color: #2563eb;
    border-bottom: 2px solid #e2e8f0;
  }
  @top-right {
    content: "FY 2023-24 — PAGE " counter(page);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    font-size: 8pt;
    font-weight: 600;
    color: #64748b;
    border-bottom: 2px solid #e2e8f0;
  }
}
```

### 3.2 Pagination Isolation Rules
1. **Cover Suppression**: `@page :first { @top-left { content: none; } @top-right { content: none; } margin: 0; }` ensures clean cover presentation.
2. **Table & Figure Protection**: `break-inside: avoid; page-break-inside: avoid;` applied to `.report-table-container`, `.metric-card`, and `.asset-figure` blocks prevents split tables across page boundaries.
3. **Interactive TOC**: Injected `<div id="sec_...">` IDs link directly to Table of Contents anchors `<a href="#sec_...">`.

---

## 4. Section 35: Air-Gapped Diagnostic Bundle Exporter

### 4.1 Data Minimization & Scrubbing
The diagnostic exporter generates a verifiable `.zip` bundle for air-gapped technical assistance without compromising confidentiality:
1. **Redacted Data**: Plaintext passwords, API keys, bearer tokens, email addresses, and confidential coal reserve tables are replaced with hash masks or `[REDACTED]`.
2. **Preserved Telemetry**: Hardware specifications (CPU cores, RAM, OS), stage run durations, error traces, SQLite schema versions, and audit log chains.
3. **Integrity Manifest**: A SHA-256 cryptographic digest is calculated over the finished archive and returned via REST API to ensure tamper-proof offline delivery.
