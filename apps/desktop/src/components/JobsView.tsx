import React, { useState, useEffect } from "react";
import {
  Activity,
  AlertTriangle,
  Ban,
  Layers,
} from "lucide-react";

interface JobErrorItem {
  stage: string;
  message: string;
  item_id?: string;
  timestamp: string;
}

interface JobData {
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

interface JobsViewProps {
  selectedJobId?: string | null;
}

const API_BASE = "http://127.0.0.1:8765";

const STAGES = [
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

export const JobsView: React.FC<JobsViewProps> = ({ selectedJobId }) => {
  const [jobs, setJobs] = useState<JobData[]>([]);
  const [activeJobId, setActiveJobId] = useState<string | null>(selectedJobId || null);
  const [activeJob, setActiveJob] = useState<JobData | null>(null);

  const fetchJobs = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/jobs`);
      if (res.ok) {
        const data: JobData[] = await res.json();
        setJobs(data);
        if (!activeJobId && data.length > 0) {
          setActiveJobId(data[0].job_id);
        }
      }
    } catch {
      // Backend not reached
    }
  };

  const fetchActiveJob = async (id: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/jobs/${id}`);
      if (res.ok) {
        const data: JobData = await res.json();
        setActiveJob(data);
      }
    } catch {
      // Backend not reached
    }
  };

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 4000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (selectedJobId) {
      setActiveJobId(selectedJobId);
    }
  }, [selectedJobId]);

  useEffect(() => {
    if (activeJobId) {
      fetchActiveJob(activeJobId);
      const interval = setInterval(() => fetchActiveJob(activeJobId), 2000);
      return () => clearInterval(interval);
    }
  }, [activeJobId]);

  const handleCancel = async () => {
    if (!activeJobId) return;
    try {
      await fetch(`${API_BASE}/api/v1/jobs/${activeJobId}/cancel`, { method: "POST" });
      fetchActiveJob(activeJobId);
    } catch {
      // Backend not reached
    }
  };

  const currentStageIndex = activeJob ? STAGES.indexOf(activeJob.current_stage) : -1;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      {/* Header & Job Selector */}
      <div className="card" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h3 className="card-title">
            <Activity size={18} color="var(--accent-gold)" />
            Processing Job System (Section 27)
          </h3>
          <p style={{ fontSize: "0.82rem", color: "var(--text-secondary)", marginTop: "2px" }}>
            12-stage observable, resumable pipeline for folder discovery, indexing, and report generation.
          </p>
        </div>

        {jobs.length > 0 && (
          <select
            value={activeJobId || ""}
            onChange={(e) => setActiveJobId(e.target.value)}
            style={{
              padding: "8px 14px",
              borderRadius: "var(--radius-sm)",
              background: "var(--bg-elevated)",
              border: "1px solid var(--border-medium)",
              color: "var(--text-primary)",
              fontFamily: "var(--font-mono)",
              fontSize: "0.8rem",
            }}
          >
            {jobs.map((j) => (
              <option key={j.job_id} value={j.job_id}>
                {j.job_id} — {j.status} ({j.progress}%)
              </option>
            ))}
          </select>
        )}
      </div>

      {activeJob ? (
        <>
          {/* Active Job Status Banner */}
          <div className="card">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <h4 style={{ fontFamily: "var(--font-display)", fontSize: "1.1rem", fontWeight: 700 }}>
                    {activeJob.job_type.toUpperCase()}
                  </h4>
                  <span
                    style={{
                      padding: "2px 8px",
                      borderRadius: "9999px",
                      fontSize: "0.72rem",
                      fontWeight: 700,
                      background:
                        activeJob.status === "COMPLETED"
                          ? "rgba(16, 185, 129, 0.15)"
                          : activeJob.status === "RUNNING"
                          ? "rgba(6, 182, 212, 0.15)"
                          : "rgba(239, 68, 68, 0.15)",
                      color:
                        activeJob.status === "COMPLETED"
                          ? "var(--status-success)"
                          : activeJob.status === "RUNNING"
                          ? "var(--accent-cyan)"
                          : "var(--status-error)",
                    }}
                  >
                    {activeJob.status}
                  </span>
                </div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)", marginTop: "4px" }}>
                  Source: {activeJob.metadata?.source_path || "—"}
                </div>
              </div>

              {activeJob.status === "RUNNING" && (
                <button
                  className="btn btn-secondary"
                  onClick={handleCancel}
                  style={{ color: "var(--status-error)", borderColor: "rgba(239, 68, 68, 0.3)" }}
                >
                  <Ban size={15} />
                  <span>Cancel Job</span>
                </button>
              )}
            </div>

            {/* Progress Bar & Counters */}
            <div style={{ marginBottom: "20px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem", marginBottom: "6px" }}>
                <span style={{ color: "var(--text-secondary)" }}>
                  Current Stage: <strong style={{ color: "var(--accent-gold)" }}>{activeJob.current_stage}</strong>
                </span>
                <span style={{ fontFamily: "var(--font-mono)", fontWeight: 700, color: "var(--text-primary)" }}>
                  {activeJob.progress}% ({activeJob.processed_items} of {activeJob.total_items} items)
                </span>
              </div>
              <div className="progress-bar-container" style={{ height: "10px" }}>
                <div className="progress-bar-fill" style={{ width: `${Math.max(activeJob.progress, 3)}%` }} />
              </div>
            </div>

            {/* 12-Stage Visual Stepper */}
            <div style={{ marginTop: "14px" }}>
              <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "10px" }}>
                Section 27 Pipeline Lifecycle
              </div>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(6, 1fr)",
                  gap: "8px",
                }}
              >
                {STAGES.map((stg, i) => {
                  const isCompleted = currentStageIndex > i || activeJob.status === "COMPLETED";
                  const isCurrent = currentStageIndex === i && activeJob.status !== "COMPLETED";
                  return (
                    <div
                      key={stg}
                      style={{
                        padding: "8px",
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
                      }}
                    >
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
          </div>

          {/* Job Errors Table */}
          {activeJob.errors && activeJob.errors.length > 0 && (
            <div className="card" style={{ borderColor: "rgba(239, 68, 68, 0.3)" }}>
              <div className="card-header">
                <h4 className="card-title" style={{ color: "var(--status-error)" }}>
                  <AlertTriangle size={18} />
                  Logged Errors ({activeJob.errors.length})
                </h4>
              </div>

              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8rem" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid var(--border-subtle)", color: "var(--text-muted)", textAlign: "left" }}>
                    <th style={{ padding: "8px" }}>Stage</th>
                    <th style={{ padding: "8px" }}>Item ID / File</th>
                    <th style={{ padding: "8px" }}>Message</th>
                  </tr>
                </thead>
                <tbody>
                  {activeJob.errors.map((err, idx) => (
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
        </>
      ) : (
        <div className="card" style={{ textAlign: "center", padding: "40px" }}>
          <Layers size={36} color="var(--text-muted)" style={{ margin: "0 auto 12px" }} />
          <h4 style={{ color: "var(--text-primary)", marginBottom: "4px" }}>No Active Ingestion Job</h4>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem" }}>
            Select a folder in <strong>Data Sources</strong> and start an ingestion job to see real-time progress.
          </p>
        </div>
      )}
    </div>
  );
};
