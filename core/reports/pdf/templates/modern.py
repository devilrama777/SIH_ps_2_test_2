"""
Modern Corporate Template (Template B) — Section 20 of Master Plan.
Contemporary clean visual design: slate, electric blue and teal palette,
sleek sans-serif typography (Inter/System), card metric highlights, and modern tables.
"""

MODERN_CSS = """
@page {
  size: A4;
  margin: 18mm 16mm 18mm 16mm;
  @top-right {
    content: "ANNUAL REPORT " counter(page);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    font-size: 8pt;
    font-weight: 600;
    color: #64748b;
    border-bottom: 2px solid #e2e8f0;
    padding-bottom: 4mm;
  }
  @top-left {
    content: "COAL INDIA LIMITED";
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    font-size: 8pt;
    font-weight: 700;
    color: #2563eb;
    border-bottom: 2px solid #e2e8f0;
    padding-bottom: 4mm;
  }
  @bottom-center {
    content: "Confidential Local Document Intelligence Platform";
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    font-size: 7.5pt;
    color: #94a3b8;
  }
}

@page :first {
  @top-left { content: none; }
  @top-right { content: none; }
  @bottom-center { content: none; }
  margin: 0;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  font-size: 10pt;
  line-height: 1.65;
  color: #1e293b;
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


/* Modern Cover Page */
.cover-page {
  height: 90vh;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 30px;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  color: #ffffff;
  border-radius: 12px;
  box-sizing: border-box;
}

.cover-header .brand-title {
  font-size: 14pt;
  font-weight: 700;
  color: #38bdf8;
  letter-spacing: 1.5px;
  text-transform: uppercase;
}

.cover-header .subsidiary-name {
  font-size: 24pt;
  font-weight: 800;
  color: #ffffff;
  margin-top: 6px;
}

.cover-center {
  margin: auto 0;
}

.cover-center .report-title {
  font-size: 30pt;
  font-weight: 900;
  line-height: 1.2;
  color: #ffffff;
  margin-bottom: 16px;
}

.cover-center .period-badge {
  display: inline-block;
  font-size: 13pt;
  font-weight: 700;
  padding: 8px 22px;
  background: #2563eb;
  color: #ffffff;
  border-radius: 20px;
}

.cover-footer {
  display: flex;
  justify-content: space-between;
  font-size: 8.5pt;
  color: #94a3b8;
  border-top: 1px solid rgba(255, 255, 255, 0.15);
  padding-top: 16px;
}

/* Table of Contents */
.toc-container {
  margin-bottom: 30px;
}

.toc-title {
  font-size: 20pt;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.5px;
  border-bottom: 3px solid #2563eb;
  padding-bottom: 8px;
  margin-bottom: 20px;
}

.toc-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-radius: 6px;
  margin: 4px 0;
}

.toc-item.level-1 {
  font-weight: 700;
  font-size: 11pt;
  background-color: #f8fafc;
  color: #0f172a;
}

.toc-item.level-2 {
  padding-left: 24px;
  font-size: 9.5pt;
  color: #475569;
}

/* Sections */
.section-title-l1 {
  font-size: 20pt;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.5px;
  border-bottom: 2px solid #e2e8f0;
  padding-bottom: 8px;
  margin-top: 30px;
  margin-bottom: 16px;
}

.section-title-l2 {
  font-size: 14pt;
  font-weight: 700;
  color: #2563eb;
  margin-top: 20px;
  margin-bottom: 10px;
}

.section-title-l3 {
  font-size: 11pt;
  font-weight: 600;
  color: #334155;
  margin-top: 14px;
}

/* Narrative & Citations */
p {
  margin-bottom: 14px;
  color: #334155;
}

.citation-ref {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, monospace;
  font-size: 7.5pt;
  font-weight: 600;
  background-color: #eff6ff;
  color: #1d4ed8;
  border: 1px solid #bfdbfe;
  padding: 2px 6px;
  border-radius: 4px;
  text-decoration: none;
}

.warning-callout {
  background-color: #fefce8;
  border-left: 4px solid #ca8a04;
  padding: 12px 16px;
  font-size: 9pt;
  border-radius: 0 6px 6px 0;
  margin: 14px 0;
  color: #854d0e;
}

/* Tables */
table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  margin: 20px 0;
  font-size: 9pt;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e2e8f0;
}

th, td {
  padding: 8px 12px;
  text-align: left;
}

th {
  background-color: #f1f5f9;
  color: #0f172a;
  font-weight: 700;
  border-bottom: 1px solid #cbd5e1;
}

tr:nth-child(even) td {
  background-color: #f8fafc;
}

tr:hover td {
  background-color: #f1f5f9;
}

tr.total-row td {
  font-weight: 800;
  background-color: #e2e8f0;
  color: #0f172a;
}

/* Images & Captions */
figure {
  margin: 20px 0;
  text-align: center;
}

figcaption {
  font-size: 8pt;
  font-weight: 500;
  color: #64748b;
  margin-top: 6px;
}
"""
