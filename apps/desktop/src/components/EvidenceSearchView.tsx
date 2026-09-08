import React, { useState } from "react";
import {
  Search,
  Calendar,
  FileText,
  FileSpreadsheet,
  Layers,
  MapPin,
} from "lucide-react";

interface RankedEvidenceItem {
  element_id: string;
  document_id: string;
  source_reference: string;
  page_number?: number;
  element_type: string;
  text: string;
  score: number;
  provenance_id?: string;
  reporting_period?: string;
  spreadsheet_coord?: {
    workbook_name: string;
    sheet_name: string;
    cell?: string;
    raw_value?: any;
  };
}

import { API_BASE } from "../services/config";

export const EvidenceSearchView: React.FC = () => {
  const [queryText, setQueryText] = useState<string>("operational performance");
  const [reportingPeriod, setReportingPeriod] = useState<string>("");
  const [docType, setDocType] = useState<string>("");
  const [results, setResults] = useState<RankedEvidenceItem[]>([]);
  const [isSearching, setIsSearching] = useState<boolean>(false);
  const [hasSearched, setHasSearched] = useState<boolean>(false);

  const handleSearch = async (overrideText?: string, overridePeriod?: string) => {
    const q = overrideText !== undefined ? overrideText : queryText;
    const p = overridePeriod !== undefined ? overridePeriod : reportingPeriod;

    if (!q.trim()) return;

    setIsSearching(true);
    setHasSearched(true);

    try {
      const res = await fetch(`${API_BASE}/api/v1/evidence/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query_text: q,
          reporting_period: p || undefined,
          document_type: docType || undefined,
          limit: 20,
        }),
      });

      if (res.ok) {
        const data: RankedEvidenceItem[] = await res.json();
        setResults(data);
      } else {
        setResults([]);
      }
    } catch {
      setResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      {/* Search Filter Header */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">
            <Search size={18} color="var(--accent-gold)" />
            Hybrid Evidence Retrieval (Section 11)
          </h3>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
            SQLite FTS5 BM25 + Temporal Ranking + Provenance Linkage
          </span>
        </div>

        <p style={{ fontSize: "0.84rem", color: "var(--text-secondary)", marginBottom: "16px" }}>
          Query evidence across ingested PDFs, spreadsheets, and Word documents. Results return
          precise provenance down to page bounding boxes and spreadsheet cells.
        </p>

        {/* Input Controls */}
        <div style={{ display: "flex", gap: "10px", flexWrap: "wrap", alignItems: "center" }}>
          <div style={{ flex: 1, minWidth: "280px" }}>
            <input
              type="text"
              value={queryText}
              onChange={(e) => setQueryText(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              placeholder="e.g., 'operational performance', 'raw coal dispatches', 'safety audit'..."
              style={{
                width: "100%",
                padding: "10px 14px",
                borderRadius: "var(--radius-sm)",
                border: "1px solid var(--border-medium)",
                background: "var(--bg-elevated)",
                color: "var(--text-primary)",
                fontSize: "0.85rem",
              }}
            />
          </div>

          <div style={{ width: "180px" }}>
            <input
              type="text"
              value={reportingPeriod}
              onChange={(e) => setReportingPeriod(e.target.value)}
              placeholder="Period (e.g. March 2025)"
              style={{
                width: "100%",
                padding: "10px 14px",
                borderRadius: "var(--radius-sm)",
                border: "1px solid var(--border-medium)",
                background: "var(--bg-elevated)",
                color: "var(--text-primary)",
                fontSize: "0.85rem",
              }}
            />
          </div>

          <div style={{ width: "160px" }}>
            <select
              value={docType}
              onChange={(e) => setDocType(e.target.value)}
              style={{
                width: "100%",
                padding: "10px 14px",
                borderRadius: "var(--radius-sm)",
                border: "1px solid var(--border-medium)",
                background: "var(--bg-elevated)",
                color: "var(--text-primary)",
                fontSize: "0.85rem",
              }}
            >
              <option value="">All Document Types</option>
              <option value="digital_pdf">Digital PDF</option>
              <option value="scanned_pdf">Scanned PDF</option>
              <option value="xlsx">Excel (XLSX)</option>
              <option value="csv">CSV Datasets</option>
              <option value="docx">Word (DOCX)</option>
            </select>
          </div>

          <button
            className="btn btn-primary"
            onClick={() => handleSearch()}
            disabled={isSearching}
          >
            <Search size={16} />
            <span>{isSearching ? "Searching..." : "Retrieve Evidence"}</span>
          </button>
        </div>

        {/* Section 11 Example Query Pills */}
        <div style={{ display: "flex", gap: "8px", marginTop: "12px", alignItems: "center" }}>
          <span style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>Example Queries:</span>
          <button
            className="btn btn-secondary"
            style={{ padding: "4px 10px", fontSize: "0.72rem" }}
            onClick={() => {
              setQueryText("operational performance information");
              setReportingPeriod("March 2025");
              handleSearch("operational performance information", "March 2025");
            }}
          >
            Section 11: "March 2025 operational performance"
          </button>
          <button
            className="btn btn-secondary"
            style={{ padding: "4px 10px", fontSize: "0.72rem" }}
            onClick={() => {
              setQueryText("coal production");
              setReportingPeriod("");
              handleSearch("coal production", "");
            }}
          >
            "Coal Production"
          </button>
        </div>
      </div>

      {/* Results List */}
      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        {isSearching ? (
          <div className="card" style={{ padding: "30px", textAlign: "center", color: "var(--text-secondary)" }}>
            Executing hybrid FTS5 and temporal ranking...
          </div>
        ) : results.length > 0 ? (
          <>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "0 4px" }}>
              <span style={{ fontSize: "0.82rem", color: "var(--text-secondary)" }}>
                Retrieved <strong>{results.length}</strong> ranked evidence elements with provenance
              </span>
            </div>

            {results.map((ev) => (
              <div
                key={ev.element_id}
                className="card"
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "10px",
                  borderLeft: "3px solid var(--accent-gold)",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
                    <span
                      style={{
                        padding: "2px 8px",
                        borderRadius: "4px",
                        background: "rgba(245, 158, 11, 0.15)",
                        color: "var(--accent-gold)",
                        fontFamily: "var(--font-mono)",
                        fontSize: "0.72rem",
                        fontWeight: 700,
                        textTransform: "uppercase",
                      }}
                    >
                      {ev.element_type}
                    </span>

                    {ev.reporting_period && (
                      <span
                        style={{
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "4px",
                          padding: "2px 8px",
                          borderRadius: "4px",
                          background: "var(--bg-elevated)",
                          color: "var(--accent-cyan)",
                          fontSize: "0.72rem",
                          fontWeight: 600,
                        }}
                      >
                        <Calendar size={12} />
                        <span>{ev.reporting_period}</span>
                      </span>
                    )}

                    <span style={{ fontSize: "0.72rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                      ID: {ev.element_id}
                    </span>
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <span style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>Relevance:</span>
                    <span
                      style={{
                        fontFamily: "var(--font-mono)",
                        fontWeight: 700,
                        fontSize: "0.75rem",
                        color: "var(--status-success)",
                        background: "rgba(16, 185, 129, 0.1)",
                        padding: "2px 6px",
                        borderRadius: "4px",
                      }}
                    >
                      {ev.score.toFixed(3)}
                    </span>
                  </div>
                </div>

                {/* Evidence Text / Data */}
                <div
                  style={{
                    fontSize: "0.88rem",
                    color: "var(--text-primary)",
                    lineHeight: 1.5,
                    background: "rgba(0, 0, 0, 0.2)",
                    padding: "10px 14px",
                    borderRadius: "var(--radius-sm)",
                    border: "1px solid var(--border-subtle)",
                  }}
                >
                  {ev.text}
                </div>

                {/* Provenance Coordinates Footer */}
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    fontSize: "0.75rem",
                    color: "var(--text-secondary)",
                    paddingTop: "6px",
                    borderTop: "1px solid var(--border-subtle)",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    {ev.spreadsheet_coord ? (
                      <span style={{ display: "inline-flex", alignItems: "center", gap: "4px", color: "var(--accent-gold)", fontWeight: 600 }}>
                        <FileSpreadsheet size={13} />
                        <span>
                          Sheet: {ev.spreadsheet_coord.sheet_name}, Cell: {ev.spreadsheet_coord.cell}
                        </span>
                      </span>
                    ) : ev.page_number ? (
                      <span style={{ display: "inline-flex", alignItems: "center", gap: "4px" }}>
                        <FileText size={13} />
                        <span>Page {ev.page_number}</span>
                      </span>
                    ) : null}

                    <span style={{ fontFamily: "var(--font-mono)", color: "var(--text-muted)", fontSize: "0.72rem" }}>
                      Source: {ev.source_reference}
                    </span>
                  </div>

                  <span style={{ fontSize: "0.72rem", color: "var(--status-success)", display: "flex", alignItems: "center", gap: "4px" }}>
                    <MapPin size={12} />
                    <span>Exact Coordinate Provenance</span>
                  </span>
                </div>
              </div>
            ))}
          </>
        ) : hasSearched ? (
          <div className="card" style={{ padding: "40px", textAlign: "center" }}>
            <Layers size={36} color="var(--text-muted)" style={{ margin: "0 auto 12px" }} />
            <h4 style={{ color: "var(--text-primary)", marginBottom: "4px" }}>No Evidence Matches Found</h4>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem" }}>
              Try broadening your query keywords or clearing the reporting period filter.
            </p>
          </div>
        ) : null}
      </div>
    </div>
  );
};
