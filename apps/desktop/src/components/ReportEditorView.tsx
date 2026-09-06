import React, { useState, useEffect } from "react";
import {
  FileText,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  ExternalLink,
  BookOpen,
  Layers,
  ShieldCheck,
} from "lucide-react";

const API_BASE = "http://127.0.0.1:8765";

interface ReportSummary {
  report_id: string;
  title: string;
  reporting_period: string;
  subsidiary_name: string;
  template_name: string;
  total_sections: number;
  created_at: string;
}

interface NarrativeBlock {
  block_id: string;
  text: string;
  confidence: number;
  insufficient_evidence: boolean;
  evidence_refs: Array<{
    evidence_id: string;
    excerpt_text?: string;
    provenance: {
      source_reference: string;
      page_number?: number;
      spreadsheet_coord?: {
        workbook_name: string;
        sheet_name: string;
        cell?: string;
      };
    };
  }>;
}

interface ReportSection {
  section_id: string;
  title: string;
  level: number;
  type: string;
  narrative_blocks: NarrativeBlock[];
  tables: Array<Record<string, any>>;
  validation_status: "valid" | "warning" | "error" | "unverified";
  subsections: ReportSection[];
}

interface FullReport {
  report_id: string;
  title: string;
  reporting_period: string;
  subsidiary_name: string;
  template_name: string;
  sections: ReportSection[];
}

export const ReportEditorView: React.FC = () => {
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [selectedReportId, setSelectedReportId] = useState<string | null>(null);
  const [fullReport, setFullReport] = useState<FullReport | null>(null);
  const [selectedSectionId, setSelectedSectionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isRevalidating, setIsRevalidating] = useState<boolean>(false);

  const fetchReports = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/reports`);
      if (res.ok) {
        const data: ReportSummary[] = await res.json();
        setReports(data);
        if (data.length > 0 && !selectedReportId) {
          setSelectedReportId(data[0].report_id);
        }
      }
    } catch (err) {
      console.error("Failed to load reports:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const loadFullReport = async (reportId: string) => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/reports/${reportId}`);
      if (res.ok) {
        const data: FullReport = await res.json();
        setFullReport(data);
        if (data.sections.length > 0) {
          setSelectedSectionId(data.sections[0].section_id);
        }
      }
    } catch (err) {
      console.error("Failed to load full report:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRevalidate = async () => {
    if (!selectedReportId) return;
    setIsRevalidating(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/reports/${selectedReportId}/validate`, {
        method: "POST",
      });
      if (res.ok) {
        await loadFullReport(selectedReportId);
      }
    } catch (err) {
      console.error("Validation error:", err);
    } finally {
      setIsRevalidating(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  useEffect(() => {
    if (selectedReportId) {
      loadFullReport(selectedReportId);
    }
  }, [selectedReportId]);

  // Find currently active section
  const findSection = (sections: ReportSection[], id: string): ReportSection | null => {
    for (const s of sections) {
      if (s.section_id === id) return s;
      const sub = findSection(s.subsections || [], id);
      if (sub) return sub;
    }
    return null;
  };

  const activeSection = fullReport && selectedSectionId ? findSection(fullReport.sections, selectedSectionId) : null;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      {/* Header Bar */}
      <div className="card" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "16px 20px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div style={{ background: "rgba(16, 185, 129, 0.1)", color: "#10b981", padding: "8px", borderRadius: "8px" }}>
            <FileText size={22} />
          </div>
          <div>
            <h2 style={{ fontSize: "1.15rem", margin: 0, fontWeight: 600 }}>Report Editor & Verified Content</h2>
            <p style={{ margin: 0, fontSize: "0.82rem", color: "var(--text-secondary)" }}>
              Section-by-section narrative inspection with coordinate-level source provenance
            </p>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <button className="btn btn-secondary" onClick={fetchReports} disabled={isLoading}>
            <RefreshCw size={15} className={isLoading ? "spin" : ""} /> Refresh
          </button>
          <button className="btn btn-primary" onClick={handleRevalidate} disabled={isRevalidating || !selectedReportId}>
            <ShieldCheck size={15} className={isRevalidating ? "spin" : ""} /> Run Deterministic Audit
          </button>
        </div>
      </div>

      {/* Main Two-Column Layout */}
      <div style={{ display: "grid", gridTemplateColumns: "320px 1fr", gap: "20px", alignItems: "start" }}>
        {/* Left Sidebar: Report selector & Table of Contents */}
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {/* Report Selector Dropdown */}
          <div className="card" style={{ padding: "16px" }}>
            <label style={{ fontSize: "0.78rem", textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--text-secondary)", fontWeight: 600 }}>
              Select Active Report
            </label>
            <select
              style={{
                width: "100%",
                marginTop: "6px",
                padding: "8px 12px",
                borderRadius: "6px",
                background: "var(--bg-secondary)",
                color: "var(--text-primary)",
                border: "1px solid var(--border-color)",
              }}
              value={selectedReportId || ""}
              onChange={(e) => setSelectedReportId(e.target.value)}
            >
              {reports.map((r) => (
                <option key={r.report_id} value={r.report_id}>
                  {r.title} ({r.reporting_period})
                </option>
              ))}
            </select>
          </div>

          {/* Table of Contents */}
          <div className="card" style={{ padding: "16px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "12px" }}>
              <Layers size={16} color="#3b82f6" />
              <h3 style={{ fontSize: "0.95rem", margin: 0, fontWeight: 600 }}>Document Hierarchy</h3>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "6px", maxHeight: "540px", overflowY: "auto" }}>
              {fullReport?.sections.map((sec) => (
                <button
                  key={sec.section_id}
                  onClick={() => setSelectedSectionId(sec.section_id)}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "8px 10px",
                    borderRadius: "6px",
                    border: "1px solid",
                    borderColor: selectedSectionId === sec.section_id ? "#3b82f6" : "transparent",
                    background: selectedSectionId === sec.section_id ? "rgba(59, 130, 246, 0.1)" : "var(--bg-secondary)",
                    color: "var(--text-primary)",
                    cursor: "pointer",
                    textAlign: "left",
                    fontSize: "0.85rem",
                  }}
                >
                  <span style={{ fontWeight: sec.level === 1 ? 600 : 400 }}>{sec.title}</span>
                  {sec.validation_status === "valid" ? (
                    <CheckCircle2 size={14} color="#10b981" />
                  ) : sec.validation_status === "warning" ? (
                    <AlertTriangle size={14} color="#f59e0b" />
                  ) : (
                    <XCircle size={14} color="#ef4444" />
                  )}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Right Panel: Active Section Content Viewer */}
        <div className="card" style={{ padding: "24px", minHeight: "600px" }}>
          {activeSection ? (
            <div>
              {/* Section Header */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", borderBottom: "1px solid var(--border-color)", paddingBottom: "16px", marginBottom: "20px" }}>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
                    <span style={{ fontSize: "0.75rem", background: "rgba(59, 130, 246, 0.15)", color: "#3b82f6", padding: "2px 8px", borderRadius: "12px", fontWeight: 600 }}>
                      Level {activeSection.level} &bull; {activeSection.type}
                    </span>
                    <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>ID: {activeSection.section_id}</span>
                  </div>
                  <h1 style={{ fontSize: "1.5rem", margin: 0, fontWeight: 700 }}>{activeSection.title}</h1>
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                  <span
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "4px",
                      fontSize: "0.8rem",
                      padding: "4px 10px",
                      borderRadius: "6px",
                      fontWeight: 600,
                      background:
                        activeSection.validation_status === "valid"
                          ? "rgba(16, 185, 129, 0.15)"
                          : activeSection.validation_status === "warning"
                          ? "rgba(245, 158, 11, 0.15)"
                          : "rgba(239, 68, 68, 0.15)",
                      color:
                        activeSection.validation_status === "valid"
                          ? "#10b981"
                          : activeSection.validation_status === "warning"
                          ? "#f59e0b"
                          : "#ef4444",
                    }}
                  >
                    {activeSection.validation_status === "valid" && <CheckCircle2 size={14} />}
                    {activeSection.validation_status === "warning" && <AlertTriangle size={14} />}
                    {activeSection.validation_status === "error" && <XCircle size={14} />}
                    {activeSection.validation_status.toUpperCase()}
                  </span>
                </div>
              </div>

              {/* Narrative Blocks */}
              <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
                {activeSection.narrative_blocks.map((block) => (
                  <div
                    key={block.block_id}
                    style={{
                      background: block.insufficient_evidence ? "rgba(245, 158, 11, 0.05)" : "var(--bg-secondary)",
                      border: "1px solid",
                      borderColor: block.insufficient_evidence ? "rgba(245, 158, 11, 0.3)" : "var(--border-color)",
                      borderRadius: "8px",
                      padding: "16px",
                    }}
                  >
                    {block.insufficient_evidence && (
                      <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "#f59e0b", fontSize: "0.8rem", fontWeight: 600, marginBottom: "8px" }}>
                        <AlertTriangle size={14} /> Insufficient primary evidence in reporting corpus
                      </div>
                    )}

                    <p style={{ margin: 0, fontSize: "0.95rem", lineHeight: "1.65", color: "var(--text-primary)" }}>
                      {block.text}
                    </p>

                    {/* Citations / Provenance Badges */}
                    {block.evidence_refs && block.evidence_refs.length > 0 && (
                      <div style={{ marginTop: "12px", display: "flex", flexWrap: "wrap", gap: "6px" }}>
                        {block.evidence_refs.map((ref, idx) => (
                          <span
                            key={idx}
                            style={{
                              display: "inline-flex",
                              alignItems: "center",
                              gap: "4px",
                              fontSize: "0.75rem",
                              background: "rgba(59, 130, 246, 0.12)",
                              color: "#60a5fa",
                              border: "1px solid rgba(59, 130, 246, 0.25)",
                              padding: "3px 8px",
                              borderRadius: "4px",
                            }}
                          >
                            <ExternalLink size={11} />
                            {ref.provenance.source_reference}
                            {ref.provenance.page_number && ` : P${ref.provenance.page_number}`}
                            {ref.provenance.spreadsheet_coord?.cell && ` [${ref.provenance.spreadsheet_coord.cell}]`}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div style={{ textAlign: "center", padding: "60px 0", color: "var(--text-secondary)" }}>
              <BookOpen size={40} style={{ opacity: 0.4, marginBottom: "12px" }} />
              <p>Select a section from the hierarchy to view narrative text and source evidence.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
