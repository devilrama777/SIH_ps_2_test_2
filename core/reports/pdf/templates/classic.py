"""
Classic Corporate Template (Template A) — Section 20 of Master Plan.
Inspired by official CIL subsidiary annual reports: deep navy and gold palette,
formal serif typography for headings, bordered tables, and formal TOC.
"""

CLASSIC_CSS = """
@page {
  size: A4;
  margin: 20mm 15mm 20mm 15mm;
  @top-center {
    content: "COAL INDIA LIMITED SUBSIDIARY — ANNUAL REPORT";
    font-family: 'Times New Roman', Times, serif;
    font-size: 8pt;
    color: #555;
    border-bottom: 1px solid #ccc;
    padding-bottom: 3mm;
  }
  @bottom-right {
    content: "Page " counter(page);
    font-family: 'Times New Roman', Times, serif;
    font-size: 8pt;
    color: #555;
  }
  @bottom-left {
    content: "CONFIDENTIAL & PROPRIETARY — STRICTLY AUDITED";
    font-family: 'Times New Roman', Times, serif;
    font-size: 7pt;
    color: #777;
  }
}

@page :first {
  @top-center { content: none; }
  @bottom-right { content: none; }
  @bottom-left { content: none; }
  margin: 0;
}

body {
  font-family: 'Georgia', 'Times New Roman', serif;
  font-size: 10.5pt;
  line-height: 1.6;
  color: #1a202c;
  background-color: #ffffff;
  margin: 0;
  padding: 0;
}

.page-break {
  page-break-before: always;
}

.report-table-container, .table-wrapper, table, .metric-card, .asset-figure, .figure-container {
  break-inside: avoid;
  page-break-inside: avoid;
}


/* Cover Page */
.cover-page {
  height: 90vh;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  text-align: center;
  padding: 40px 20px;
  border: 4px double #1a365d;
  box-sizing: border-box;
}

.cover-header .brand-title {
  font-size: 26pt;
  font-weight: bold;
  color: #1a365d;
  text-transform: uppercase;
  letter-spacing: 2px;
  margin-bottom: 8px;
}

.cover-header .subsidiary-name {
  font-size: 18pt;
  color: #2b6cb0;
  font-style: italic;
}

.cover-center {
  margin: auto 0;
}

.cover-center .report-title {
  font-size: 24pt;
  font-weight: bold;
  color: #1a202c;
  margin-bottom: 12px;
}

.cover-center .period-badge {
  display: inline-block;
  font-size: 14pt;
  font-weight: bold;
  padding: 6px 24px;
  background-color: #1a365d;
  color: #ffffff;
  border-radius: 4px;
}

.cover-footer {
  font-size: 9pt;
  color: #4a5568;
  border-top: 1px solid #cbd5e0;
  padding-top: 12px;
}

/* Table of Contents */
.toc-container {
  margin-bottom: 30px;
}

.toc-title {
  font-size: 18pt;
  font-weight: bold;
  color: #1a365d;
  border-bottom: 2px solid #1a365d;
  padding-bottom: 6px;
  margin-bottom: 18px;
}

.toc-item {
  display: flex;
  justify-content: space-between;
  margin: 8px 0;
  font-size: 10.5pt;
}

.toc-item.level-1 {
  font-weight: bold;
  margin-top: 12px;
}

.toc-item.level-2 {
  padding-left: 20px;
  font-weight: normal;
}

/* Sections */
.section-title-l1 {
  font-size: 18pt;
  color: #1a365d;
  border-bottom: 2px solid #1a365d;
  padding-bottom: 6px;
  margin-top: 24px;
  margin-bottom: 14px;
}

.section-title-l2 {
  font-size: 14pt;
  color: #2c5282;
  margin-top: 18px;
  margin-bottom: 10px;
}

.section-title-l3 {
  font-size: 11pt;
  font-weight: bold;
  color: #2d3748;
  margin-top: 12px;
}

/* Narrative Blocks & Citations */
p {
  margin-bottom: 12px;
  text-align: justify;
}

.citation-ref {
  font-family: 'Courier New', monospace;
  font-size: 8pt;
  background-color: #edf2f7;
  color: #2b6cb0;
  border: 1px solid #cbd5e0;
  padding: 1px 4px;
  border-radius: 3px;
  text-decoration: none;
}

.warning-callout {
  background-color: #fffaf0;
  border-left: 4px solid #dd6b20;
  padding: 10px 14px;
  font-size: 9pt;
  margin: 12px 0;
}

/* Tables */
table {
  width: 100%;
  border-collapse: collapse;
  margin: 16px 0;
  font-size: 9pt;
  font-family: 'Arial', sans-serif;
}

th, td {
  border: 1px solid #cbd5e0;
  padding: 6px 10px;
  text-align: left;
}

th {
  background-color: #1a365d;
  color: #ffffff;
  font-weight: bold;
}

tr:nth-child(even) {
  background-color: #f7fafc;
}

tr.total-row {
  font-weight: bold;
  background-color: #edf2f7;
}

/* Images & Captions */
figure {
  margin: 16px 0;
  text-align: center;
}

figcaption {
  font-size: 8.5pt;
  font-style: italic;
  color: #4a5568;
  margin-top: 4px;
}
"""
