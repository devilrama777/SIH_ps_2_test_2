import React, { useState, useEffect } from "react";
import {
  Search,
  FileText,
  FileSpreadsheet,
  CheckCircle2,
  XCircle,
  Sparkles,
  GitCommit,
} from "lucide-react";

import { API_BASE } from "../services/config";

interface SourceResolution {
  source_reference: string;
  document_id?: string;
  page_number?: number;
  document_type: string;
  snippet_text?: string;
  spreadsheet_coord?: {
    workbook_name: string;
    sheet_name: string;
    cell?: string;
    raw_value?: any;
    formatted_value?: string;
  };
  found: boolean;
}

interface DiffLine {
  operation: string;
  text: string;
}

interface EditProposal {
  proposal_id: string;
  report_id: string;
  section_id: string;
  user_instruction: string;
  original_text: string;
  proposed_text: string;
  diff_lines: DiffLine[];
  validation_status: string;
  validation_issues_count: number;
  status: string;
}

interface ReportSummary {
  report_id: string;
  title: string;
}

export const SourceTraceabilityView: React.FC = () => {
  // Source Coordinate Lookup State
  const [sourceRef, setSourceRef] = useState<string>("CCL_Operations_FY25.pdf");
  const [pageNumber, setPageNumber] = useState<string>("4");
  const [cellAddress, setCellAddress] = useState<string>("");
  const [resolution, setResolution] = useState<SourceResolution | null>(null);
  const [isResolving, setIsResolving] = useState<boolean>(false);

  // Agentic Editing State
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [selectedReportId, setSelectedReportId] = useState<string | null>(null);
  const [targetSectionId, setTargetSectionId] = useState<string>("sec_ops_01");
  const [editInstruction, setEditInstruction] = useState<string>(
    "The raw coal production number needs revision. Verify against source document and update to 84.5 MT."
  );
  const [activeProposal, setActiveProposal] = useState<EditProposal | null>(null);
  const [isProposing, setIsProposing] = useState<boolean>(false);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const fetchReports = async () => {
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
    }
  };

  const handleResolveCoordinate = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!sourceRef) return;

    setIsResolving(true);
    try {
      let url = `${API_BASE}/api/v1/traceability/resolve?source_ref=${encodeURIComponent(sourceRef)}`;
      if (pageNumber) url += `&page=${pageNumber}`;
      if (cellAddress) url += `&cell=${encodeURIComponent(cellAddress)}`;

      const res = await fetch(url);
      if (res.ok) {
        const data: SourceResolution = await res.json();
        setResolution(data);
      }
    } catch (err) {
      console.error("Failed to resolve coordinate:", err);
    } finally {
      setIsResolving(false);
    }
  };

  const handleRequestEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedReportId || !editInstruction) return;

    setIsProposing(true);
    setActiveProposal(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/reports/${selectedReportId}/edit-agent`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          section_id: targetSectionId,
          instruction: editInstruction,
        }),
      });
      if (res.ok) {
        const proposal: EditProposal = await res.json();
        setActiveProposal(proposal);
      } else {
        const err = await res.json();
        alert(`Agent editing error: ${err.detail}`);
      }
    } catch (err) {
      console.error("Edit request failed:", err);
    } finally {
      setIsProposing(false);
    }
  };

  const handleAcceptProposal = async () => {
    if (!activeProposal) return;
    try {
      const res = await fetch(`${API_BASE}/api/v1/reports/proposals/${activeProposal.proposal_id}/accept`, {
        method: "POST",
      });
      if (res.ok) {
        setActionSuccess(`Edit accepted! Updated report saved to disk.`);
        setActiveProposal({ ...activeProposal, status: "accepted" });
      }
    } catch (err) {
      console.error("Acceptance failed:", err);
    }
  };

  const handleRejectProposal = async () => {
    if (!activeProposal) return;
    try {
      const res = await fetch(`${API_BASE}/api/v1/reports/proposals/${activeProposal.proposal_id}/reject`, {
        method: "POST",
      });
      if (res.ok) {
        setActionSuccess(`Edit proposal discarded without report changes.`);
        setActiveProposal({ ...activeProposal, status: "rejected" });
      }
    } catch (err) {
      console.error("Rejection failed:", err);
    }
  };

  useEffect(() => {
    fetchReports();
    handleResolveCoordinate();
  }, []);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      {/* Header Bar */}
      <div className="card" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "16px 20px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div style={{ background: "rgba(14, 165, 233, 0.1)", color: "#0ea5e9", padding: "8px", borderRadius: "8px" }}>
            <GitCommit size={22} />
          </div>
          <div>
            <h2 style={{ fontSize: "1.15rem", margin: 0, fontWeight: 600 }}>Source Traceability & Agentic Editing</h2>
            <p style={{ margin: 0, fontSize: "0.82rem", color: "var(--text-secondary)" }}>
              Section 21 coordinate-level provenance viewer and Section 22 human-in-the-loop review
            </p>
          </div>
        </div>
      </div>

      {/* Grid: Left = Source Coordinate Inspector, Right = Agentic Editing */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1.2fr", gap: "20px" }}>
        {/* Left Column: Coordinate Lookup & Source Evidence */}
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div className="card" style={{ padding: "20px" }}>
            <h3 style={{ fontSize: "1rem", margin: "0 0 14px 0", fontWeight: 600 }}>Coordinate Inspector</h3>

            <form onSubmit={handleResolveCoordinate} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <div>
                <label style={{ fontSize: "0.76rem", color: "var(--text-secondary)" }}>Source Reference (Filename)</label>
                <input
                  type="text"
                  value={sourceRef}
                  onChange={(e) => setSourceRef(e.target.value)}
                  placeholder="e.g. CCL_Operations_FY25.pdf"
                  style={{
                    width: "100%",
                    padding: "8px 12px",
                    borderRadius: "6px",
                    background: "var(--bg-secondary)",
                    color: "var(--text-primary)",
                    border: "1px solid var(--border-color)",
                    marginTop: "4px",
                  }}
                />
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                <div>
                  <label style={{ fontSize: "0.76rem", color: "var(--text-secondary)" }}>Page Number (PDF)</label>
                  <input
                    type="number"
                    value={pageNumber}
                    onChange={(e) => setPageNumber(e.target.value)}
                    placeholder="e.g. 14"
                    style={{
                      width: "100%",
                      padding: "8px 12px",
                      borderRadius: "6px",
                      background: "var(--bg-secondary)",
                      color: "var(--text-primary)",
                      border: "1px solid var(--border-color)",
                      marginTop: "4px",
                    }}
                  />
                </div>

                <div>
                  <label style={{ fontSize: "0.76rem", color: "var(--text-secondary)" }}>Cell Address (XLSX)</label>
                  <input
                    type="text"
                    value={cellAddress}
                    onChange={(e) => setCellAddress(e.target.value)}
                    placeholder="e.g. G27"
                    style={{
                      width: "100%",
                      padding: "8px 12px",
                      borderRadius: "6px",
                      background: "var(--bg-secondary)",
                      color: "var(--text-primary)",
                      border: "1px solid var(--border-color)",
                      marginTop: "4px",
                    }}
                  />
                </div>
              </div>

              <button type="submit" className="btn btn-primary" disabled={isResolving} style={{ marginTop: "4px" }}>
                <Search size={14} className={isResolving ? "spin" : ""} /> Locate Source Element
              </button>
            </form>

            {/* Quick Preset Coordinate Links */}
            <div style={{ marginTop: "14px", display: "flex", gap: "6px", flexWrap: "wrap" }}>
              <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)", alignSelf: "center" }}>Presets:</span>
              <button
                type="button"
                className="btn btn-secondary"
                style={{ fontSize: "0.72rem", padding: "3px 8px" }}
                onClick={() => {
                  setSourceRef("Annual_Report_2024.pdf");
                  setPageNumber("12");
                  setCellAddress("");
                  handleResolveCoordinate();
                }}
              >
                [DOC:Annual_Report_2024.pdf:P12]
              </button>

              <button
                type="button"
                className="btn btn-secondary"
                style={{ fontSize: "0.72rem", padding: "3px 8px" }}
                onClick={() => {
                  setSourceRef("Production_March.xlsx");
                  setPageNumber("");
                  setCellAddress("G27");
                  handleResolveCoordinate();
                }}
              >
                [COORD:Production_March.xlsx:G27]
              </button>
            </div>
          </div>

          {/* Evidence Resolution Box */}
          <div className="card" style={{ padding: "20px" }}>
            <h3 style={{ fontSize: "1rem", margin: "0 0 12px 0", fontWeight: 600 }}>Resolved Source Content</h3>

            {resolution ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  {resolution.document_type === "xlsx" ? (
                    <FileSpreadsheet size={16} color="#10b981" />
                  ) : (
                    <FileText size={16} color="#3b82f6" />
                  )}
                  <span style={{ fontSize: "0.85rem", fontWeight: 600 }}>{resolution.source_reference}</span>
                  {resolution.page_number && (
                    <span style={{ fontSize: "0.72rem", background: "rgba(59, 130, 246, 0.15)", color: "#3b82f6", padding: "2px 6px", borderRadius: "4px" }}>
                      Page {resolution.page_number}
                    </span>
                  )}
                  {resolution.spreadsheet_coord?.cell && (
                    <span style={{ fontSize: "0.72rem", background: "rgba(16, 185, 129, 0.15)", color: "#10b981", padding: "2px 6px", borderRadius: "4px" }}>
                      Cell {resolution.spreadsheet_coord.cell}
                    </span>
                  )}
                </div>

                <div
                  style={{
                    background: "var(--bg-secondary)",
                    padding: "12px",
                    borderRadius: "6px",
                    border: "1px solid var(--border-color)",
                    fontSize: "0.86rem",
                    lineHeight: "1.5",
                    whiteSpace: "pre-wrap",
                    fontFamily: "var(--font-mono, monospace)",
                  }}
                >
                  {resolution.snippet_text || "No text available."}
                </div>

                {/* Section 21: Visual Bounding Box Page Inspector */}
                {resolution.page_number && (
                  <div style={{ marginTop: "14px", display: "flex", flexDirection: "column", gap: "8px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <span style={{ fontSize: "0.78rem", fontWeight: 600, color: "var(--text-secondary)" }}>
                        Visual Page Inspection & Coordinate Overlay (Page {resolution.page_number})
                      </span>
                      <a
                        href={`${API_BASE}/api/v1/sources/page-preview?source_reference=${encodeURIComponent(
                          resolution.source_reference
                        )}&page_number=${resolution.page_number}`}
                        target="_blank"
                        rel="noreferrer"
                        style={{ fontSize: "0.74rem", color: "#3b82f6", textDecoration: "none" }}
                      >
                        Open Full Resolution ↗
                      </a>
                    </div>

                    <div
                      style={{
                        position: "relative",
                        maxHeight: "360px",
                        overflowY: "auto",
                        border: "1px solid var(--border-color)",
                        borderRadius: "6px",
                        background: "#090d16",
                        display: "flex",
                        justifyContent: "center",
                        padding: "10px",
                      }}
                    >
                      <img
                        src={`${API_BASE}/api/v1/sources/page-preview?source_reference=${encodeURIComponent(
                          resolution.source_reference
                        )}&page_number=${resolution.page_number}`}
                        alt="Source Page Coordinate Preview"
                        style={{
                          maxWidth: "100%",
                          height: "auto",
                          borderRadius: "4px",
                          boxShadow: "0 4px 12px rgba(0,0,0,0.5)",
                        }}
                      />
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                Execute a coordinate lookup above to view primary source excerpts.
              </p>
            )}
          </div>
        </div>

        {/* Right Column: Agentic Review & Editing Workflow */}
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div className="card" style={{ padding: "20px" }}>
            <h3 style={{ fontSize: "1rem", margin: "0 0 14px 0", fontWeight: 600 }}>Agentic Correction Workflow</h3>

            <form onSubmit={handleRequestEdit} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: "12px" }}>
                <div>
                  <label style={{ fontSize: "0.76rem", color: "var(--text-secondary)" }}>Active Report</label>
                  <select
                    style={{
                      width: "100%",
                      padding: "8px 12px",
                      borderRadius: "6px",
                      background: "var(--bg-secondary)",
                      color: "var(--text-primary)",
                      border: "1px solid var(--border-color)",
                      marginTop: "4px",
                    }}
                    value={selectedReportId || ""}
                    onChange={(e) => setSelectedReportId(e.target.value)}
                  >
                    {reports.map((r) => (
                      <option key={r.report_id} value={r.report_id}>
                        {r.title}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label style={{ fontSize: "0.76rem", color: "var(--text-secondary)" }}>Target Section ID</label>
                  <input
                    type="text"
                    value={targetSectionId}
                    onChange={(e) => setTargetSectionId(e.target.value)}
                    style={{
                      width: "100%",
                      padding: "8px 12px",
                      borderRadius: "6px",
                      background: "var(--bg-secondary)",
                      color: "var(--text-primary)",
                      border: "1px solid var(--border-color)",
                      marginTop: "4px",
                    }}
                  />
                </div>
              </div>

              <div>
                <label style={{ fontSize: "0.76rem", color: "var(--text-secondary)" }}>
                  Natural Language Correction Instruction
                </label>
                <textarea
                  rows={3}
                  value={editInstruction}
                  onChange={(e) => setEditInstruction(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "8px 12px",
                    borderRadius: "6px",
                    background: "var(--bg-secondary)",
                    color: "var(--text-primary)",
                    border: "1px solid var(--border-color)",
                    marginTop: "4px",
                    fontFamily: "inherit",
                  }}
                />
              </div>

              <button type="submit" className="btn btn-primary" disabled={isProposing} style={{ marginTop: "4px" }}>
                <Sparkles size={14} className={isProposing ? "spin" : ""} />
                {isProposing ? "Agent Checking Evidence & Generating Diff..." : "Submit to Editing Agent"}
              </button>
            </form>
          </div>

          {/* Diff Proposal Box */}
          {activeProposal && (
            <div className="card" style={{ padding: "20px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                <div>
                  <h4 style={{ margin: 0, fontSize: "0.95rem", fontWeight: 600 }}>Proposed Revision Diff</h4>
                  <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                    Proposal ID: {activeProposal.proposal_id} &bull; Status: {activeProposal.status.toUpperCase()}
                  </span>
                </div>

                <div style={{ display: "flex", gap: "8px" }}>
                  {activeProposal.status === "pending_review" && (
                    <>
                      <button className="btn btn-primary" onClick={handleAcceptProposal}>
                        <CheckCircle2 size={14} /> Accept & Apply
                      </button>
                      <button className="btn btn-secondary" onClick={handleRejectProposal}>
                        <XCircle size={14} /> Reject
                      </button>
                    </>
                  )}
                </div>
              </div>

              {/* Diff Viewer */}
              <div
                style={{
                  background: "#0f172a",
                  borderRadius: "6px",
                  padding: "12px",
                  fontFamily: "var(--font-mono, monospace)",
                  fontSize: "0.82rem",
                  maxHeight: "260px",
                  overflowY: "auto",
                }}
              >
                {activeProposal.diff_lines.map((line, idx) => {
                  const isAdd = line.operation === "+";
                  const isDel = line.operation === "-";
                  return (
                    <div
                      key={idx}
                      style={{
                        color: isAdd ? "#4ade80" : isDel ? "#f87171" : "#94a3b8",
                        background: isAdd ? "rgba(74, 222, 128, 0.1)" : isDel ? "rgba(248, 113, 113, 0.1)" : "transparent",
                        padding: "2px 6px",
                        whiteSpace: "pre-wrap",
                      }}
                    >
                      {line.operation} {line.text}
                    </div>
                  );
                })}
              </div>

              {actionSuccess && (
                <div style={{ marginTop: "12px", color: "#10b981", fontSize: "0.82rem", display: "flex", alignItems: "center", gap: "6px" }}>
                  <CheckCircle2 size={15} /> {actionSuccess}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
