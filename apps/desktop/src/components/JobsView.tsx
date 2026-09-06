import React, { useState, useEffect } from "react";
import {
  Activity,
  AlertTriangle,
  Ban,
  CheckCircle2,
  FileText,
  Layers,
  Pause,
  Play,
  Sparkles,
} from "lucide-react";

interface JobErrorItem {
  stage: string;
  message: string;
  item_id?: string;
  timestamp: string;
}

interface IngestionJobData {
  job_id: string;
  job_type: string;
  status: string;
  progress: number;
  current_stage: string;
  total_items: number;
  processed_items: number;
  failed_items: number;
  started_at?: string;
  completed_at?: string;
  errors: JobErrorItem[];
  metadata: { source_path?: string };
}

interface ReportJobData {
  job_id: string;
  status: string;
  current_stage: string;
  progress_percent: number;
  completed_stages: string[];
  config: {
    subsidiary_code?: string;
    reporting_period?: string;
    template_style?: string;
    output_format?: string;
  };
  created_at: string;
  updated_at: string;
  error_message?: string | null;
  intermediate_artifacts?: Record<string, any>;
}

interface JobsViewProps {
  selectedJobId?: string | null;
}

const API_BASE = "http://127.0.0.1:8765";

const PIPELINE_STAGES = [
  "DISCOVERY",
  "INGESTION",
  "OCR",
  "EXTRACTION",
  "NORMALIZATION",
  "INDEXING",
  "PLANNING",
  "GENERATION",
  "VALIDATION",
  "COMPOSITION",
  "RENDERING",
  "READY_FOR_REVIEW",
];

const SUBSIDIARIES = ["CIL", "BCCL", "CCL", "ECL", "WCL", "SECL", "NCL", "MCL", "CMPDIL"];

export const JobsView: React.FC<JobsViewProps> = ({ selectedJobId }) => {
  const [activeTab, setActiveTab] = useState<"reports" | "ingestion">("reports");

  // Report Pipeline Jobs
  const [reportJobs, setReportJobs] = useState<ReportJobData[]>([]);
  const [activeReportJobId, setActiveReportJobId] = useState<string | null>(null);
  const [activeReportJob, setActiveReportJob] = useState<ReportJobData | null>(null);

  // Ingestion Jobs
  const [ingestionJobs, setIngestionJobs] = useState<IngestionJobData[]>([]);
  const [activeIngestionJobId, setActiveIngestionJobId] = useState<string | null>(null);
  const [activeIngestionJob, setActiveIngestionJob] = useState<IngestionJobData | null>(null);

  // New Report Job Dialog / Controls
  const [showNewJobModal, setShowNewJobModal] = useState(false);
  const [newSub, setNewSub] = useState("BCCL");
  const [newPeriod, setNewPeriod] = useState("FY 2024-25");
  const [newTemplate, setNewTemplate] = useState("classic");
  const [isStartingJob, setIsStartingJob] = useState(false);

  const fetchReportJobs = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/report-jobs`);
      if (res.ok) {
        const data: ReportJobData[] = await res.json();
        setReportJobs(data);
        if (!activeReportJobId && data.length > 0) {
          setActiveReportJobId(data[0].job_id);
        }
      }
    } catch {
      // Backend not reached
    }
  };

  const fetchActiveReportJob = async (id: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/report-jobs/${id}`);
      if (res.ok) {
        const data: ReportJobData = await res.json();
        setActiveReportJob(data);
      }
    } catch {
      // Backend not reached
    }
  };

  const fetchIngestionJobs = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/jobs`);
      if (res.ok) {
        const data: IngestionJobData[] = await res.json();
        setIngestionJobs(data);
        if (!activeIngestionJobId && data.length > 0) {
          setActiveIngestionJobId(data[0].job_id);
        }
      }
    } catch {
      // Backend not reached
    }
  };

  const fetchActiveIngestionJob = async (id: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/jobs/${id}`);
      if (res.ok) {
        const data: IngestionJobData = await res.json();
        setActiveIngestionJob(data);
      }
    } catch {
      // Backend not reached
    }
  };

  useEffect(() => {
    fetchReportJobs();
    fetchIngestionJobs();
    const interval = setInterval(() => {
      fetchReportJobs();
      fetchIngestionJobs();
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (selectedJobId) {
      if (selectedJobId.startsWith("rjob_")) {
        setActiveTab("reports");
        setActiveReportJobId(selectedJobId);
      } else {
        setActiveTab("ingestion");
        setActiveIngestionJobId(selectedJobId);
      }
    }
  }, [selectedJobId]);

  useEffect(() => {
    if (activeReportJobId) {
      fetchActiveReportJob(activeReportJobId);
    }
  }, [activeReportJobId]);

  useEffect(() => {
    if (activeIngestionJobId) {
      fetchActiveIngestionJob(activeIngestionJobId);
    }
  }, [activeIngestionJobId]);

  // Report Job Actions
  const handlePauseReportJob = async () => {
    if (!activeReportJobId) return;
    try {
      await fetch(`${API_BASE}/api/v1/report-jobs/${activeReportJobId}/pause`, { method: "POST" });
      fetchActiveReportJob(activeReportJobId);
      fetchReportJobs();
    } catch {}
  };

  const handleResumeReportJob = async () => {
    if (!activeReportJobId) return;
    try {
      await fetch(`${API_BASE}/api/v1/report-jobs/${activeReportJobId}/resume`, { method: "POST" });
      fetchActiveReportJob(activeReportJobId);
      fetchReportJobs();
    } catch {}
  };

  const handleCancelReportJob = async () => {
    if (!activeReportJobId) return;
    try {
      await fetch(`${API_BASE}/api/v1/report-jobs/${activeReportJobId}/cancel`, { method: "POST" });
      fetchActiveReportJob(activeReportJobId);
      fetchReportJobs();
    } catch {}
  };

  const handleStartNewReportJob = async () => {
    setIsStartingJob(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/report-jobs/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          subsidiary_code: newSub,
          reporting_period: newPeriod,
          template_style: newTemplate,
          run_sync: false,
        }),
      });
      if (res.ok) {
        const created: ReportJobData = await res.json();
        setShowNewJobModal(false);
        setActiveReportJobId(created.job_id);
        fetchReportJobs();
      }
    } catch {}
    setIsStartingJob(false);
  };

  // Ingestion Job Actions
  const handleCancelIngestion = async () => {
    if (!activeIngestionJobId) return;
    try {
      await fetch(`${API_BASE}/api/v1/jobs/${activeIngestionJobId}/cancel`, { method: "POST" });
      fetchActiveIngestionJob(activeIngestionJobId);
      fetchIngestionJobs();
    } catch {}
  };


  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      {/* Header & Tabs */}
      <div className="card" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
        <div>
          <h3 className="card-title">
            <Activity size={18} color="var(--accent-gold)" />
            Unified 12-Stage Job Orchestrator (Section 27)
          </h3>
          <p style={{ fontSize: "0.82rem", color: "var(--text-secondary)", marginTop: "2px" }}>
            Observable, checkpoint-backed, resumable lifecycle execution for document ingestion and publication generation.
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
          {/* Tab Switcher */}
          <div style={{ display: "flex", background: "var(--bg-elevated)", borderRadius: "var(--radius-sm)", padding: "3px", border: "1px solid var(--border-medium)" }}>
            <button
              onClick={() => setActiveTab("reports")}
              style={{
                padding: "6px 14px",
                borderRadius: "var(--radius-sm)",
                border: "none",
                fontSize: "0.8rem",
                fontWeight: 600,
                cursor: "pointer",
                background: activeTab === "reports" ? "var(--accent-gold)" : "transparent",
                color: activeTab === "reports" ? "#000" : "var(--text-secondary)",
                transition: "all 0.15s ease",
              }}
            >
              Report Pipeline ({reportJobs.length})
            </button>
            <button
              onClick={() => setActiveTab("ingestion")}
              style={{
                padding: "6px 14px",
                borderRadius: "var(--radius-sm)",
                border: "none",
                fontSize: "0.8rem",
                fontWeight: 600,
                cursor: "pointer",
                background: activeTab === "ingestion" ? "var(--accent-gold)" : "transparent",
                color: activeTab === "ingestion" ? "#000" : "var(--text-secondary)",
                transition: "all 0.15s ease",
              }}
            >
              Folder Ingestion ({ingestionJobs.length})
            </button>
          </div>

          {activeTab === "reports" && (
            <button
              className="btn btn-primary"
              onClick={() => setShowNewJobModal(true)}
              style={{ fontSize: "0.8rem", padding: "6px 12px" }}
            >
              <Sparkles size={14} />
              <span>New Report Pipeline</span>
            </button>
          )}
        </div>
      </div>

      {/* New Report Job Modal */}
      {showNewJobModal && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0, 0, 0, 0.7)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
          }}
        >
          <div className="card" style={{ width: "460px", maxWidth: "90vw", background: "var(--bg-surface)", border: "1px solid var(--border-medium)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <h4 style={{ display: "flex", alignItems: "center", gap: "8px", fontFamily: "var(--font-display)" }}>
                <Sparkles size={16} color="var(--accent-gold)" />
                Launch 12-Stage Report Job
              </h4>
              <button
                onClick={() => setShowNewJobModal(false)}
                style={{ background: "transparent", border: "none", color: "var(--text-muted)", cursor: "pointer", fontSize: "1.2rem" }}
              >
                &times;
              </button>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginBottom: "20px" }}>
              <div>
                <label style={{ fontSize: "0.75rem", color: "var(--text-secondary)", display: "block", marginBottom: "4px" }}>
                  Subsidiary Operating Entity
                </label>
                <select
                  value={newSub}
                  onChange={(e) => setNewSub(e.target.value)}
                  style={{ width: "100%", padding: "8px 10px", borderRadius: "var(--radius-sm)", background: "var(--bg-elevated)", border: "1px solid var(--border-medium)", color: "var(--text-primary)" }}
                >
                  {SUBSIDIARIES.map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>

              <div>
                <label style={{ fontSize: "0.75rem", color: "var(--text-secondary)", display: "block", marginBottom: "4px" }}>
                  Fiscal Reporting Period
                </label>
                <input
                  type="text"
                  value={newPeriod}
                  onChange={(e) => setNewPeriod(e.target.value)}
                  placeholder="e.g. FY 2024-25"
                  style={{ width: "100%", padding: "8px 10px", borderRadius: "var(--radius-sm)", background: "var(--bg-elevated)", border: "1px solid var(--border-medium)", color: "var(--text-primary)" }}
                />
              </div>

              <div>
                <label style={{ fontSize: "0.75rem", color: "var(--text-secondary)", display: "block", marginBottom: "4px" }}>
                  Design Template Theme
                </label>
                <select
                  value={newTemplate}
                  onChange={(e) => setNewTemplate(e.target.value)}
                  style={{ width: "100%", padding: "8px 10px", borderRadius: "var(--radius-sm)", background: "var(--bg-elevated)", border: "1px solid var(--border-medium)", color: "var(--text-primary)" }}
                >
                  <option value="classic">Classic CIL Official (Gold / Slate)</option>
                  <option value="modern">Modern Dynamic Glass (Cyan / Amber)</option>
                </select>
              </div>
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
              <button className="btn btn-secondary" onClick={() => setShowNewJobModal(false)}>
                Cancel
              </button>
              <button className="btn btn-primary" onClick={handleStartNewReportJob} disabled={isStartingJob}>
                {isStartingJob ? "Starting Pipeline..." : "Dispatch Job"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main Content Area */}
      {activeTab === "reports" ? (
        /* Report Pipeline Tab */
        <>
          {reportJobs.length > 0 && (
            <div className="card" style={{ padding: "10px 16px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                Selected Report Pipeline Job:
              </span>
              <select
                value={activeReportJobId || ""}
                onChange={(e) => setActiveReportJobId(e.target.value)}
                style={{
                  padding: "6px 12px",
                  borderRadius: "var(--radius-sm)",
                  background: "var(--bg-elevated)",
                  border: "1px solid var(--border-medium)",
                  color: "var(--text-primary)",
                  fontFamily: "var(--font-mono)",
                  fontSize: "0.82rem",
                }}
              >
                {reportJobs.map((j) => (
                  <option key={j.job_id} value={j.job_id}>
                    {j.job_id} — {j.config.subsidiary_code} ({j.config.reporting_period}) [{j.status.toUpperCase()} - {Math.round(j.progress_percent)}%]
                  </option>
                ))}
              </select>
            </div>
          )}

          {activeReportJob ? (
            <div className="card">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px", flexWrap: "wrap", gap: "10px" }}>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    <h4 style={{ fontFamily: "var(--font-display)", fontSize: "1.15rem", fontWeight: 700 }}>
                      {activeReportJob.config.subsidiary_code} Report Pipeline ({activeReportJob.config.reporting_period})
                    </h4>
                    <span
                      style={{
                        padding: "3px 10px",
                        borderRadius: "9999px",
                        fontSize: "0.72rem",
                        fontWeight: 700,
                        background:
                          activeReportJob.status === "completed"
                            ? "rgba(16, 185, 129, 0.15)"
                            : activeReportJob.status === "running"
                            ? "rgba(6, 182, 212, 0.15)"
                            : activeReportJob.status === "paused"
                            ? "rgba(245, 158, 11, 0.15)"
                            : "rgba(239, 68, 68, 0.15)",
                        color:
                          activeReportJob.status === "completed"
                            ? "var(--status-success)"
                            : activeReportJob.status === "running"
                            ? "var(--accent-cyan)"
                            : activeReportJob.status === "paused"
                            ? "var(--accent-gold)"
                            : "var(--status-error)",
                      }}
                    >
                      {activeReportJob.status.toUpperCase()}
                    </span>
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)", marginTop: "4px" }}>
                    Job ID: {activeReportJob.job_id} &bull; Template: {activeReportJob.config.template_style || "classic"} &bull; Created: {activeReportJob.created_at}
                  </div>
                </div>

                {/* Resumable Controls */}
                <div style={{ display: "flex", gap: "8px" }}>
                  {activeReportJob.status === "running" && (
                    <button className="btn btn-secondary" onClick={handlePauseReportJob} style={{ fontSize: "0.8rem", padding: "6px 12px" }}>
                      <Pause size={14} />
                      <span>Pause</span>
                    </button>
                  )}

                  {activeReportJob.status === "paused" && (
                    <button className="btn btn-primary" onClick={handleResumeReportJob} style={{ fontSize: "0.8rem", padding: "6px 12px" }}>
                      <Play size={14} />
                      <span>Resume Job</span>
                    </button>
                  )}

                  {(activeReportJob.status === "running" || activeReportJob.status === "paused" || activeReportJob.status === "pending") && (
                    <button
                      className="btn btn-secondary"
                      onClick={handleCancelReportJob}
                      style={{ color: "var(--status-error)", borderColor: "rgba(239, 68, 68, 0.3)", fontSize: "0.8rem", padding: "6px 12px" }}
                    >
                      <Ban size={14} />
                      <span>Cancel</span>
                    </button>
                  )}
                </div>
              </div>

              {/* Progress Bar & Counters */}
              <div style={{ marginBottom: "20px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem", marginBottom: "6px" }}>
                  <span style={{ color: "var(--text-secondary)" }}>
                    Current Stage: <strong style={{ color: "var(--accent-gold)" }}>{activeReportJob.current_stage}</strong>
                  </span>
                  <span style={{ fontFamily: "var(--font-mono)", fontWeight: 700, color: "var(--text-primary)" }}>
                    {Math.round(activeReportJob.progress_percent)}% ({activeReportJob.completed_stages.length} of {PIPELINE_STAGES.length} stages)
                  </span>
                </div>
                <div className="progress-bar-container" style={{ height: "10px" }}>
                  <div className="progress-bar-fill" style={{ width: `${Math.max(activeReportJob.progress_percent, 3)}%` }} />
                </div>
              </div>

              {/* 12-Stage Visual Stepper */}
              <div>
                <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "10px", fontWeight: 700 }}>
                  Section 27 Execution Lifecycle (12 Resumable Checkpoints)
                </div>
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(6, 1fr)",
                    gap: "8px",
                  }}
                >
                  {PIPELINE_STAGES.map((stg, i) => {
                    const isCompleted = activeReportJob.completed_stages.includes(stg) || activeReportJob.status === "completed";
                    const isCurrent = activeReportJob.current_stage === stg && activeReportJob.status !== "completed";
                    return (
                      <div
                        key={stg}
                        style={{
                          padding: "10px 6px",
                          borderRadius: "var(--radius-sm)",
                          background: isCurrent
                            ? "rgba(245, 158, 11, 0.15)"
                            : isCompleted
                            ? "rgba(16, 185, 129, 0.08)"
                            : "var(--bg-elevated)",
                          border: isCurrent
                            ? "1px solid rgba(245, 158, 11, 0.4)"
                            : isCompleted
                            ? "1px solid rgba(16, 185, 129, 0.25)"
                            : "1px solid var(--border-subtle)",
                          textAlign: "center",
                          display: "flex",
                          flexDirection: "column",
                          alignItems: "center",
                          gap: "4px",
                        }}
                      >
                        {isCompleted ? (
                          <CheckCircle2 size={13} color="var(--status-success)" />
                        ) : isCurrent ? (
                          <Activity size={13} color="var(--accent-gold)" />
                        ) : (
                          <div style={{ width: "13px", height: "13px", borderRadius: "50%", border: "1px solid var(--text-muted)" }} />
                        )}
                        <div
                          style={{
                            fontSize: "0.68rem",
                            fontWeight: 700,
                            color: isCurrent
                              ? "var(--accent-gold)"
                              : isCompleted
                              ? "var(--status-success)"
                              : "var(--text-muted)",
                          }}
                        >
                          {i + 1}. {stg}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Error Callout if Any */}
              {activeReportJob.error_message && (
                <div style={{ marginTop: "16px", padding: "12px", borderRadius: "var(--radius-sm)", background: "rgba(239, 68, 68, 0.1)", border: "1px solid rgba(239, 68, 68, 0.3)", display: "flex", alignItems: "center", gap: "10px" }}>
                  <AlertTriangle size={18} color="var(--status-error)" />
                  <span style={{ fontSize: "0.82rem", color: "var(--status-error)" }}>
                    Pipeline Error: {activeReportJob.error_message}
                  </span>
                </div>
              )}
            </div>
          ) : (
            <div className="card" style={{ textAlign: "center", padding: "40px" }}>
              <FileText size={36} color="var(--text-muted)" style={{ margin: "0 auto 12px" }} />
              <h4 style={{ color: "var(--text-primary)", marginBottom: "4px" }}>No Report Pipeline Jobs Yet</h4>
              <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem", marginBottom: "16px" }}>
                Click <strong>New Report Pipeline</strong> to launch an end-to-end 12-stage publication workflow.
              </p>
              <button className="btn btn-primary" onClick={() => setShowNewJobModal(true)}>
                <Sparkles size={15} />
                <span>Launch Report Job</span>
              </button>
            </div>
          )}
        </>
      ) : (
        /* Folder Ingestion Tab */
        <>
          {ingestionJobs.length > 0 && (
            <div className="card" style={{ padding: "10px 16px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                Selected Folder Ingestion Job:
              </span>
              <select
                value={activeIngestionJobId || ""}
                onChange={(e) => setActiveIngestionJobId(e.target.value)}
                style={{
                  padding: "6px 12px",
                  borderRadius: "var(--radius-sm)",
                  background: "var(--bg-elevated)",
                  border: "1px solid var(--border-medium)",
                  color: "var(--text-primary)",
                  fontFamily: "var(--font-mono)",
                  fontSize: "0.82rem",
                }}
              >
                {ingestionJobs.map((j) => (
                  <option key={j.job_id} value={j.job_id}>
                    {j.job_id} — {j.status} ({j.progress}%)
                  </option>
                ))}
              </select>
            </div>
          )}

          {activeIngestionJob ? (
            <div className="card">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    <h4 style={{ fontFamily: "var(--font-display)", fontSize: "1.1rem", fontWeight: 700 }}>
                      {activeIngestionJob.job_type.toUpperCase()}
                    </h4>
                    <span
                      style={{
                        padding: "2px 8px",
                        borderRadius: "9999px",
                        fontSize: "0.72rem",
                        fontWeight: 700,
                        background:
                          activeIngestionJob.status === "COMPLETED"
                            ? "rgba(16, 185, 129, 0.15)"
                            : activeIngestionJob.status === "RUNNING"
                            ? "rgba(6, 182, 212, 0.15)"
                            : "rgba(239, 68, 68, 0.15)",
                        color:
                          activeIngestionJob.status === "COMPLETED"
                            ? "var(--status-success)"
                            : activeIngestionJob.status === "RUNNING"
                            ? "var(--accent-cyan)"
                            : "var(--status-error)",
                      }}
                    >
                      {activeIngestionJob.status}
                    </span>
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)", marginTop: "4px" }}>
                    Source: {activeIngestionJob.metadata?.source_path || "—"}
                  </div>
                </div>

                {activeIngestionJob.status === "RUNNING" && (
                  <button
                    className="btn btn-secondary"
                    onClick={handleCancelIngestion}
                    style={{ color: "var(--status-error)", borderColor: "rgba(239, 68, 68, 0.3)" }}
                  >
                    <Ban size={15} />
                    <span>Cancel Job</span>
                  </button>
                )}
              </div>

              {/* Ingestion Progress */}
              <div style={{ marginBottom: "20px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem", marginBottom: "6px" }}>
                  <span style={{ color: "var(--text-secondary)" }}>
                    Current Stage: <strong style={{ color: "var(--accent-gold)" }}>{activeIngestionJob.current_stage}</strong>
                  </span>
                  <span style={{ fontFamily: "var(--font-mono)", fontWeight: 700, color: "var(--text-primary)" }}>
                    {activeIngestionJob.progress}% ({activeIngestionJob.processed_items} of {activeIngestionJob.total_items} items)
                  </span>
                </div>
                <div className="progress-bar-container" style={{ height: "10px" }}>
                  <div className="progress-bar-fill" style={{ width: `${Math.max(activeIngestionJob.progress, 3)}%` }} />
                </div>
              </div>

              {/* Errors table */}
              {activeIngestionJob.errors && activeIngestionJob.errors.length > 0 && (
                <div className="card" style={{ borderColor: "rgba(239, 68, 68, 0.3)", marginTop: "14px" }}>
                  <h5 style={{ color: "var(--status-error)", display: "flex", alignItems: "center", gap: "6px", marginBottom: "10px" }}>
                    <AlertTriangle size={15} />
                    Ingestion Errors ({activeIngestionJob.errors.length})
                  </h5>
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8rem" }}>
                    <thead>
                      <tr style={{ borderBottom: "1px solid var(--border-subtle)", color: "var(--text-muted)", textAlign: "left" }}>
                        <th style={{ padding: "8px" }}>Stage</th>
                        <th style={{ padding: "8px" }}>Item ID / File</th>
                        <th style={{ padding: "8px" }}>Message</th>
                      </tr>
                    </thead>
                    <tbody>
                      {activeIngestionJob.errors.map((err, idx) => (
                        <tr key={idx} style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.04)" }}>
                          <td style={{ padding: "8px", fontWeight: 600, color: "var(--status-error)" }}>{err.stage}</td>
                          <td style={{ padding: "8px", fontFamily: "var(--font-mono)", color: "var(--text-secondary)" }}>{err.item_id || "—"}</td>
                          <td style={{ padding: "8px", color: "var(--text-primary)" }}>{err.message}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          ) : (
            <div className="card" style={{ textAlign: "center", padding: "40px" }}>
              <Layers size={36} color="var(--text-muted)" style={{ margin: "0 auto 12px" }} />
              <h4 style={{ color: "var(--text-primary)", marginBottom: "4px" }}>No Active Ingestion Job</h4>
              <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem" }}>
                Select a folder in <strong>Data Sources</strong> and start an ingestion job to see real-time progress.
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
};
