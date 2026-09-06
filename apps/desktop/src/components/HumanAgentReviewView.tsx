import React, { useState, useEffect } from "react";
import {
  GitPullRequest,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Sparkles,
  Send,
  Clock,
  ShieldCheck,
} from "lucide-react";

interface DiffLine {
  operation: string; // '+', '-', ' '
  text: string;
}

interface EditProposalData {
  proposal_id: string;
  report_id: string;
  section_id: string;
  user_instruction: string;
  original_text: string;
  proposed_text: string;
  diff_lines: DiffLine[];
  validation_status: string;
  validation_issues_count: number;
  status: string; // 'pending_review', 'accepted', 'rejected'
  created_at: string;
}

interface ReportOption {
  report_id: string;
  title: string;
  version: number;
  sections?: { section_id: string; title: string }[];
}

const API_BASE = "http://127.0.0.1:8765";

export const HumanAgentReviewView: React.FC = () => {
  const [reports, setReports] = useState<ReportOption[]>([]);
  const [selectedReportId, setSelectedReportId] = useState<string>("");
  const [selectedSectionId, setSelectedSectionId] = useState<string>("");
  const [userInstruction, setUserInstruction] = useState<string>("");
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [activeProposal, setActiveProposal] = useState<EditProposalData | null>(null);
  const [proposals, setProposals] = useState<EditProposalData[]>([]);
  const [actionFeedback, setActionFeedback] = useState<string | null>(null);

  const fetchReports = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/reports`);
      if (res.ok) {
        const data = await res.json();
        setReports(data);
        if (data.length > 0 && !selectedReportId) {
          setSelectedReportId(data[0].report_id);
          if (data[0].sections && data[0].sections.length > 0) {
            setSelectedSectionId(data[0].sections[0].section_id);
          }
        }
      }
    } catch {}
  };

  const fetchProposals = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/agent/review/proposals`);
      if (res.ok) {
        const data = await res.json();
        setProposals(data);
        if (!activeProposal && data.length > 0) {
          setActiveProposal(data[0]);
        }
      }
    } catch {}
  };

  useEffect(() => {
    fetchReports();
    fetchProposals();
  }, []);

  const handleProposeEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedReportId || !selectedSectionId || !userInstruction.trim()) return;

    setIsGenerating(true);
    setActionFeedback(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/agent/review/propose-edit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          report_id: selectedReportId,
          section_id: selectedSectionId,
          user_instruction: userInstruction.trim(),
        }),
      });

      if (res.ok) {
        const proposal: EditProposalData = await res.json();
        setActiveProposal(proposal);
        fetchProposals();
        setActionFeedback("Generated grounded revision proposal with verified source evidence.");
      } else {
        setActionFeedback("Failed to generate edit proposal. Check report and section IDs.");
      }
    } catch (err) {
      setActionFeedback("Network error connecting to AI agent editing service.");
    }
    setIsGenerating(false);
  };

  const handleAccept = async () => {
    if (!activeProposal) return;
    try {
      const res = await fetch(`${API_BASE}/api/v1/agent/review/proposals/${activeProposal.proposal_id}/accept`, {
        method: "POST",
      });
      if (res.ok) {
        const data = await res.json();
        setActionFeedback(`Proposal accepted and applied to Report ${data.report_id} (Version ${data.version}).`);
        fetchProposals();
        fetchReports();
        setActiveProposal({ ...activeProposal, status: "accepted" });
      }
    } catch {}
  };

  const handleReject = async () => {
    if (!activeProposal) return;
    try {
      const res = await fetch(`${API_BASE}/api/v1/agent/review/proposals/${activeProposal.proposal_id}/reject`, {
        method: "POST",
      });
      if (res.ok) {
        setActionFeedback(`Proposal ${activeProposal.proposal_id} was rejected without altering report.`);
        fetchProposals();
        setActiveProposal({ ...activeProposal, status: "rejected" });
      }
    } catch {}
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      {/* Header */}
      <div className="card" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h3 className="card-title">
            <GitPullRequest size={18} color="var(--accent-gold)" />
            Human + Agent Review &amp; Diff System (Section 22)
          </h3>
          <p style={{ fontSize: "0.82rem", color: "var(--text-secondary)", marginTop: "2px" }}>
            Source-aware editing with zero blind string replacement: evidence re-grounding, mathematical validation, and human sign-off.
          </p>
        </div>

        {actionFeedback && (
          <div
            style={{
              padding: "6px 14px",
              borderRadius: "var(--radius-sm)",
              fontSize: "0.78rem",
              background: "rgba(16, 185, 129, 0.15)",
              color: "var(--status-success)",
              border: "1px solid rgba(16, 185, 129, 0.3)",
              display: "flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            <ShieldCheck size={14} />
            <span>{actionFeedback}</span>
          </div>
        )}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "360px 1fr", gap: "20px" }}>
        {/* Left Column: Instruction Panel & History */}
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {/* Correction Input Form */}
          <div className="card">
            <h4 style={{ fontSize: "0.92rem", fontWeight: 700, marginBottom: "14px", display: "flex", alignItems: "center", gap: "8px" }}>
              <Sparkles size={16} color="var(--accent-gold)" />
              Request Agentic Revision
            </h4>

            <form onSubmit={handleProposeEdit} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <div>
                <label style={{ fontSize: "0.75rem", color: "var(--text-secondary)", display: "block", marginBottom: "4px" }}>
                  Target Report
                </label>
                <select
                  value={selectedReportId}
                  onChange={(e) => {
                    setSelectedReportId(e.target.value);
                    const rep = reports.find((r) => r.report_id === e.target.value);
                    if (rep && rep.sections && rep.sections.length > 0) {
                      setSelectedSectionId(rep.sections[0].section_id);
                    }
                  }}
                  style={{
                    width: "100%",
                    padding: "8px 10px",
                    borderRadius: "var(--radius-sm)",
                    background: "var(--bg-elevated)",
                    border: "1px solid var(--border-medium)",
                    color: "var(--text-primary)",
                    fontSize: "0.82rem",
                  }}
                >
                  {reports.map((r) => (
                    <option key={r.report_id} value={r.report_id}>
                      {r.title || r.report_id} (v{r.version || 1})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label style={{ fontSize: "0.75rem", color: "var(--text-secondary)", display: "block", marginBottom: "4px" }}>
                  Section ID
                </label>
                <input
                  type="text"
                  value={selectedSectionId}
                  onChange={(e) => setSelectedSectionId(e.target.value)}
                  placeholder="e.g. sec_01, operational_review"
                  style={{
                    width: "100%",
                    padding: "8px 10px",
                    borderRadius: "var(--radius-sm)",
                    background: "var(--bg-elevated)",
                    border: "1px solid var(--border-medium)",
                    color: "var(--text-primary)",
                    fontSize: "0.82rem",
                    fontFamily: "var(--font-mono)",
                  }}
                />
              </div>

              <div>
                <label style={{ fontSize: "0.75rem", color: "var(--text-secondary)", display: "block", marginBottom: "4px" }}>
                  Correction Instruction
                </label>
                <textarea
                  rows={4}
                  value={userInstruction}
                  onChange={(e) => setUserInstruction(e.target.value)}
                  placeholder="e.g. The coal dispatch figures in this section are outdated. Re-ground against the March audited dispatch statement and correct the metric."
                  style={{
                    width: "100%",
                    padding: "8px 10px",
                    borderRadius: "var(--radius-sm)",
                    background: "var(--bg-elevated)",
                    border: "1px solid var(--border-medium)",
                    color: "var(--text-primary)",
                    fontSize: "0.82rem",
                    resize: "vertical",
                  }}
                />
              </div>

              <button
                type="submit"
                className="btn btn-primary"
                disabled={isGenerating || !userInstruction.trim()}
                style={{ marginTop: "4px" }}
              >
                <Send size={14} />
                <span>{isGenerating ? "Agent Verifying Sources..." : "Propose Grounded Edit"}</span>
              </button>
            </form>
          </div>

          {/* Proposals History */}
          <div className="card">
            <h4 style={{ fontSize: "0.85rem", fontWeight: 700, marginBottom: "10px", color: "var(--text-secondary)", display: "flex", alignItems: "center", gap: "6px" }}>
              <Clock size={15} />
              Recent Edit Proposals ({proposals.length})
            </h4>

            {proposals.length === 0 ? (
              <p style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
                No proposals yet. Submit an instruction above.
              </p>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "8px", maxHeight: "280px", overflowY: "auto" }}>
                {proposals.map((p) => (
                  <div
                    key={p.proposal_id}
                    onClick={() => setActiveProposal(p)}
                    style={{
                      padding: "8px 12px",
                      borderRadius: "var(--radius-sm)",
                      background: activeProposal?.proposal_id === p.proposal_id ? "rgba(245, 158, 11, 0.15)" : "var(--bg-elevated)",
                      border: activeProposal?.proposal_id === p.proposal_id ? "1px solid var(--accent-gold)" : "1px solid var(--border-subtle)",
                      cursor: "pointer",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", marginBottom: "4px" }}>
                      <span style={{ fontFamily: "var(--font-mono)", fontWeight: 700, color: "var(--text-primary)" }}>
                        {p.proposal_id}
                      </span>
                      <span
                        style={{
                          fontWeight: 700,
                          fontSize: "0.68rem",
                          color:
                            p.status === "accepted"
                              ? "var(--status-success)"
                              : p.status === "rejected"
                              ? "var(--status-error)"
                              : "var(--accent-gold)",
                        }}
                      >
                        {p.status.toUpperCase()}
                      </span>
                    </div>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                      {p.user_instruction}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Visual Side-by-Side Diff & Action Controls */}
        <div>
          {activeProposal ? (
            <div className="card" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              {/* Proposal Header & Actions */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "10px" }}>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    <h4 style={{ fontFamily: "var(--font-display)", fontSize: "1.1rem", fontWeight: 700 }}>
                      Proposal {activeProposal.proposal_id}
                    </h4>
                    <span
                      style={{
                        padding: "2px 8px",
                        borderRadius: "9999px",
                        fontSize: "0.72rem",
                        fontWeight: 700,
                        background:
                          activeProposal.status === "accepted"
                            ? "rgba(16, 185, 129, 0.15)"
                            : activeProposal.status === "rejected"
                            ? "rgba(239, 68, 68, 0.15)"
                            : "rgba(245, 158, 11, 0.15)",
                        color:
                          activeProposal.status === "accepted"
                            ? "var(--status-success)"
                            : activeProposal.status === "rejected"
                            ? "var(--status-error)"
                            : "var(--accent-gold)",
                      }}
                    >
                      {activeProposal.status.toUpperCase()}
                    </span>
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)", marginTop: "4px" }}>
                    Report: {activeProposal.report_id} &bull; Section: {activeProposal.section_id}
                  </div>
                </div>

                {/* Human Review Action Gate */}
                <div style={{ display: "flex", gap: "10px" }}>
                  {activeProposal.status === "pending_review" ? (
                    <>
                      <button
                        className="btn btn-secondary"
                        onClick={handleReject}
                        style={{ color: "var(--status-error)", borderColor: "rgba(239, 68, 68, 0.3)", fontSize: "0.8rem", padding: "6px 14px" }}
                      >
                        <XCircle size={15} />
                        <span>Reject Revision</span>
                      </button>
                      <button
                        className="btn btn-primary"
                        onClick={handleAccept}
                        style={{ fontSize: "0.8rem", padding: "6px 16px" }}
                      >
                        <CheckCircle2 size={15} />
                        <span>Accept &amp; Apply to Report</span>
                      </button>
                    </>
                  ) : (
                    <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)", display: "flex", alignItems: "center", gap: "6px" }}>
                      <CheckCircle2 size={16} color="var(--status-success)" />
                      <span>Review Finalized ({activeProposal.status})</span>
                    </div>
                  )}
                </div>
              </div>

              {/* User Instruction Context */}
              <div style={{ padding: "10px 14px", borderRadius: "var(--radius-sm)", background: "var(--bg-elevated)", border: "1px solid var(--border-subtle)" }}>
                <span style={{ fontSize: "0.72rem", color: "var(--text-muted)", textTransform: "uppercase", display: "block", marginBottom: "2px", fontWeight: 700 }}>
                  User Correction Request
                </span>
                <span style={{ fontSize: "0.85rem", color: "var(--text-primary)" }}>
                  "{activeProposal.user_instruction}"
                </span>
              </div>

              {/* Validation Status Callout */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "10px 14px",
                  borderRadius: "var(--radius-sm)",
                  background:
                    activeProposal.validation_issues_count === 0
                      ? "rgba(16, 185, 129, 0.1)"
                      : "rgba(245, 158, 11, 0.1)",
                  border:
                    activeProposal.validation_issues_count === 0
                      ? "1px solid rgba(16, 185, 129, 0.3)"
                      : "1px solid rgba(245, 158, 11, 0.3)",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  {activeProposal.validation_issues_count === 0 ? (
                    <CheckCircle2 size={16} color="var(--status-success)" />
                  ) : (
                    <AlertTriangle size={16} color="var(--accent-gold)" />
                  )}
                  <span style={{ fontSize: "0.82rem", fontWeight: 600, color: "var(--text-primary)" }}>
                    {activeProposal.validation_issues_count === 0
                      ? "Deterministic Math & Provenance Validation Passed"
                      : `Validation Warning: ${activeProposal.validation_issues_count} issue(s) detected in proposed draft`}
                  </span>
                </div>
                <span style={{ fontSize: "0.75rem", fontFamily: "var(--font-mono)", color: "var(--text-secondary)" }}>
                  Validation Status: {activeProposal.validation_status}
                </span>
              </div>

              {/* Visual Unified Diff Container */}
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                  <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 700 }}>
                    Section Narrative Diff Viewer
                  </span>
                  <div style={{ display: "flex", gap: "12px", fontSize: "0.72rem" }}>
                    <span style={{ color: "var(--status-error)" }}>- Original Lines (Replaced)</span>
                    <span style={{ color: "var(--status-success)" }}>+ Proposed Lines (Substantiated)</span>
                  </div>
                </div>

                <div
                  style={{
                    backgroundColor: "#0d1117",
                    borderRadius: "var(--radius-sm)",
                    border: "1px solid var(--border-subtle)",
                    fontFamily: "var(--font-mono)",
                    fontSize: "0.82rem",
                    lineHeight: "1.6",
                    overflowX: "auto",
                    padding: "12px",
                  }}
                >
                  {activeProposal.diff_lines && activeProposal.diff_lines.length > 0 ? (
                    activeProposal.diff_lines.map((line, idx) => {
                      const isAdd = line.operation === "+";
                      const isDel = line.operation === "-";
                      return (
                        <div
                          key={idx}
                          style={{
                            display: "flex",
                            gap: "10px",
                            padding: "2px 6px",
                            borderRadius: "2px",
                            backgroundColor: isAdd
                              ? "rgba(46, 160, 67, 0.15)"
                              : isDel
                              ? "rgba(248, 81, 73, 0.15)"
                              : "transparent",
                            color: isAdd
                              ? "#3fb950"
                              : isDel
                              ? "#f85149"
                              : "var(--text-secondary)",
                          }}
                        >
                          <span style={{ userSelect: "none", width: "16px", fontWeight: 700 }}>
                            {line.operation}
                          </span>
                          <span style={{ flex: 1, whiteSpace: "pre-wrap" }}>
                            {line.text}
                          </span>
                        </div>
                      );
                    })
                  ) : (
                    <div style={{ color: "var(--text-muted)", textAlign: "center", padding: "20px" }}>
                      No textual differences detected.
                    </div>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="card" style={{ textAlign: "center", padding: "60px 20px" }}>
              <GitPullRequest size={42} color="var(--text-muted)" style={{ margin: "0 auto 14px" }} />
              <h4 style={{ color: "var(--text-primary)", marginBottom: "6px" }}>No Proposal Selected</h4>
              <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem", maxWidth: "440px", margin: "0 auto" }}>
                Select an existing proposal from the list on the left, or input a natural language correction instruction to review grounded diffs.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
