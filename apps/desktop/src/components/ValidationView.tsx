import React, { useState, useEffect } from "react";
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  RefreshCw,
  ShieldCheck,
  Filter,
  Calculator,
  Calendar,
  Layers,
  Link,
  Eye,
  FileCheck,
} from "lucide-react";

import { API_BASE } from "../services/config";

interface ValidationIssue {
  category: "numerical" | "temporal" | "provenance" | "structural" | "visual" | "links";
  severity: "error" | "warning" | "info";
  section_id: string;
  message: string;
  context: Record<string, any>;
}

interface ValidationReportData {
  report_id: string;
  overall_status: "valid" | "warning" | "error" | "unverified";
  total_issues: number;
  error_count: number;
  warning_count: number;
  issues: ValidationIssue[];
  passed: boolean;
}

interface ReportSummary {
  report_id: string;
  title: string;
  reporting_period: string;
}

export const ValidationView: React.FC = () => {
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [selectedReportId, setSelectedReportId] = useState<string | null>(null);
  const [valReport, setValReport] = useState<ValidationReportData | null>(null);
  const [activeCategory, setActiveCategory] = useState<string>("all");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isRevalidating, setIsRevalidating] = useState<boolean>(false);

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
      console.error("Failed to fetch reports:", err);
    }
  };

  const fetchValidation = async (reportId: string) => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/reports/${reportId}/validation`);
      if (res.ok) {
        const data: ValidationReportData = await res.json();
        setValReport(data);
      }
    } catch (err) {
      console.error("Failed to fetch validation report:", err);
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
        const data: ValidationReportData = await res.json();
        setValReport(data);
      }
    } catch (err) {
      console.error("Revalidation failed:", err);
    } finally {
      setIsRevalidating(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  useEffect(() => {
    if (selectedReportId) {
      fetchValidation(selectedReportId);
    }
  }, [selectedReportId]);

  const filteredIssues = valReport
    ? activeCategory === "all"
      ? valReport.issues
      : valReport.issues.filter((i) => i.category === activeCategory)
    : [];

  const getCategoryIcon = (cat: string) => {
    switch (cat) {
      case "numerical":
        return <Calculator size={14} />;
      case "temporal":
        return <Calendar size={14} />;
      case "structural":
        return <Layers size={14} />;
      case "provenance":
        return <FileCheck size={14} />;
      case "visual":
        return <Eye size={14} />;
      case "links":
        return <Link size={14} />;
      default:
        return <AlertTriangle size={14} />;
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      {/* Header Bar */}
      <div className="card" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "16px 20px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div style={{ background: "rgba(59, 130, 246, 0.1)", color: "#3b82f6", padding: "8px", borderRadius: "8px" }}>
            <ShieldCheck size={22} />
          </div>
          <div>
            <h2 style={{ fontSize: "1.15rem", margin: 0, fontWeight: 600 }}>Deterministic Validation Engine</h2>
            <p style={{ margin: 0, fontSize: "0.82rem", color: "var(--text-secondary)" }}>
              Zero-LLM mathematical, temporal, provenance, and statutory structural verification
            </p>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <select
            style={{
              padding: "8px 12px",
              borderRadius: "6px",
              background: "var(--bg-secondary)",
              color: "var(--text-primary)",
              border: "1px solid var(--border-color)",
              minWidth: "220px",
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

          <button className="btn btn-secondary" onClick={() => selectedReportId && fetchValidation(selectedReportId)} disabled={isLoading}>
            <RefreshCw size={15} className={isLoading ? "spin" : ""} /> Refresh
          </button>

          <button className="btn btn-primary" onClick={handleRevalidate} disabled={isRevalidating || !selectedReportId}>
            <ShieldCheck size={15} className={isRevalidating ? "spin" : ""} /> Re-run Full Audit
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "16px" }}>
        <div className="card" style={{ padding: "16px", display: "flex", alignItems: "center", gap: "12px" }}>
          <div
            style={{
              background: valReport?.passed ? "rgba(16, 185, 129, 0.15)" : "rgba(239, 68, 68, 0.15)",
              color: valReport?.passed ? "#10b981" : "#ef4444",
              padding: "10px",
              borderRadius: "8px",
            }}
          >
            {valReport?.passed ? <CheckCircle2 size={24} /> : <XCircle size={24} />}
          </div>
          <div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", textTransform: "uppercase", fontWeight: 600 }}>
              Audit Gate
            </div>
            <div style={{ fontSize: "1.25rem", fontWeight: 700 }}>
              {valReport?.passed ? "PASSED" : "ACTION REQUIRED"}
            </div>
          </div>
        </div>

        <div className="card" style={{ padding: "16px", display: "flex", alignItems: "center", gap: "12px" }}>
          <div style={{ background: "rgba(239, 68, 68, 0.15)", color: "#ef4444", padding: "10px", borderRadius: "8px" }}>
            <XCircle size={24} />
          </div>
          <div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", textTransform: "uppercase", fontWeight: 600 }}>
              Errors (Blocking)
            </div>
            <div style={{ fontSize: "1.25rem", fontWeight: 700, color: "#ef4444" }}>
              {valReport?.error_count ?? 0}
            </div>
          </div>
        </div>

        <div className="card" style={{ padding: "16px", display: "flex", alignItems: "center", gap: "12px" }}>
          <div style={{ background: "rgba(245, 158, 11, 0.15)", color: "#f59e0b", padding: "10px", borderRadius: "8px" }}>
            <AlertTriangle size={24} />
          </div>
          <div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", textTransform: "uppercase", fontWeight: 600 }}>
              Warnings
            </div>
            <div style={{ fontSize: "1.25rem", fontWeight: 700, color: "#f59e0b" }}>
              {valReport?.warning_count ?? 0}
            </div>
          </div>
        </div>

        <div className="card" style={{ padding: "16px", display: "flex", alignItems: "center", gap: "12px" }}>
          <div style={{ background: "rgba(59, 130, 246, 0.15)", color: "#3b82f6", padding: "10px", borderRadius: "8px" }}>
            <Filter size={24} />
          </div>
          <div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", textTransform: "uppercase", fontWeight: 600 }}>
              Total Inspected Issues
            </div>
            <div style={{ fontSize: "1.25rem", fontWeight: 700 }}>
              {valReport?.total_issues ?? 0}
            </div>
          </div>
        </div>
      </div>

      {/* Category Filter Pills */}
      <div style={{ display: "flex", gap: "8px" }}>
        {["all", "numerical", "temporal", "provenance", "structural", "visual", "links"].map((cat) => (
          <button
            key={cat}
            onClick={() => setActiveCategory(cat)}
            className={`btn ${activeCategory === cat ? "btn-primary" : "btn-secondary"}`}
            style={{ fontSize: "0.8rem", padding: "6px 14px", textTransform: "capitalize" }}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Issue Findings List */}
      <div className="card" style={{ padding: "20px" }}>
        <h3 style={{ fontSize: "1rem", margin: "0 0 16px 0", fontWeight: 600 }}>Audit Findings & Exceptions</h3>

        {filteredIssues.length > 0 ? (
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {filteredIssues.map((issue, idx) => (
              <div
                key={idx}
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: "12px",
                  padding: "12px 16px",
                  background: "var(--bg-secondary)",
                  borderRadius: "8px",
                  borderLeft: `4px solid ${issue.severity === "error" ? "#ef4444" : "#f59e0b"}`,
                }}
              >
                <div style={{ color: issue.severity === "error" ? "#ef4444" : "#f59e0b", marginTop: "2px" }}>
                  {issue.severity === "error" ? <XCircle size={18} /> : <AlertTriangle size={18} />}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
                    <span
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "4px",
                        fontSize: "0.72rem",
                        padding: "2px 6px",
                        borderRadius: "4px",
                        background: "rgba(255, 255, 255, 0.08)",
                        fontWeight: 600,
                        textTransform: "uppercase",
                      }}
                    >
                      {getCategoryIcon(issue.category)}
                      {issue.category}
                    </span>
                    <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                      Section: <strong>{issue.section_id}</strong>
                    </span>
                  </div>
                  <p style={{ margin: 0, fontSize: "0.88rem", lineHeight: "1.4" }}>{issue.message}</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ textAlign: "center", padding: "40px 0", color: "var(--text-secondary)" }}>
            <CheckCircle2 size={36} color="#10b981" style={{ marginBottom: "8px" }} />
            <p>No validation issues detected in this category. Report conforms to deterministic invariants.</p>
          </div>
        )}
      </div>
    </div>
  );
};
