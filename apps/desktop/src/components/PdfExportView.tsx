import React, { useState, useEffect } from "react";
import {
  FileDown,
  Printer,
  FileText,
  ExternalLink,
  Layers,
  Clock,
  HardDrive,
  BookOpen,
} from "lucide-react";

import { API_BASE } from "../services/config";

interface ReportSummary {
  report_id: string;
  title: string;
  reporting_period: string;
  subsidiary_name: string;
  template_name: string;
}

interface PdfRenderResult {
  report_id: string;
  template_name: string;
  pdf_path: string;
  html_path: string;
  page_count: number;
  file_size_bytes: number;
  render_time_seconds: number;
  renderer_engine: string;
}

export const PdfExportView: React.FC = () => {
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [selectedReportId, setSelectedReportId] = useState<string | null>(null);
  const [selectedTemplate, setSelectedTemplate] = useState<"modern" | "classic">("modern");
  const [isRendering, setIsRendering] = useState<boolean>(false);
  const [renderResult, setRenderResult] = useState<PdfRenderResult | null>(null);

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

  const handleRenderPdf = async () => {
    if (!selectedReportId) return;
    setIsRendering(true);
    try {
      const res = await fetch(
        `${API_BASE}/api/v1/reports/${selectedReportId}/export/pdf?template=${selectedTemplate}`,
        { method: "POST" }
      );
      if (res.ok) {
        const data: PdfRenderResult = await res.json();
        setRenderResult(data);
      } else {
        const err = await res.json();
        alert(`Export failed: ${err.detail}`);
      }
    } catch (err) {
      console.error("Failed to render PDF:", err);
    } finally {
      setIsRendering(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      {/* Header Bar */}
      <div className="card" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "16px 20px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div style={{ background: "rgba(37, 99, 235, 0.1)", color: "#2563eb", padding: "8px", borderRadius: "8px" }}>
            <FileDown size={22} />
          </div>
          <div>
            <h2 style={{ fontSize: "1.15rem", margin: 0, fontWeight: 600 }}>PDF Document Publishing Engine</h2>
            <p style={{ margin: 0, fontSize: "0.82rem", color: "var(--text-secondary)" }}>
              Section 19 & 20 air-gapped Chromium PDF compilation with dual visual templates
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
              minWidth: "240px",
            }}
            value={selectedReportId || ""}
            onChange={(e) => {
              setSelectedReportId(e.target.value);
              setRenderResult(null);
            }}
          >
            {reports.map((r) => (
              <option key={r.report_id} value={r.report_id}>
                {r.title} ({r.reporting_period})
              </option>
            ))}
          </select>

          <button
            className="btn btn-primary"
            onClick={handleRenderPdf}
            disabled={isRendering || !selectedReportId}
          >
            <Printer size={15} className={isRendering ? "spin" : ""} />
            {isRendering ? "Compiling PDF..." : "Export Official PDF"}
          </button>
        </div>
      </div>

      {/* Template Selection Cards (Section 20: Classic vs Modern) */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
        <div
          className="card"
          onClick={() => setSelectedTemplate("modern")}
          style={{
            padding: "16px",
            cursor: "pointer",
            border: `2px solid ${selectedTemplate === "modern" ? "#2563eb" : "var(--border-color)"}`,
            background: selectedTemplate === "modern" ? "rgba(37, 99, 235, 0.05)" : "var(--card-bg)",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
            <span style={{ fontWeight: 700, fontSize: "1rem", color: "#2563eb" }}>Template B — Modern Corporate</span>
            {selectedTemplate === "modern" && <span style={{ fontSize: "0.72rem", background: "#2563eb", color: "#fff", padding: "2px 8px", borderRadius: "10px", fontWeight: 600 }}>ACTIVE</span>}
          </div>
          <p style={{ margin: 0, fontSize: "0.83rem", color: "var(--text-secondary)", lineHeight: "1.4" }}>
            Contemporary visual design with dark slate hero cover, vibrant electric blue accents, card-style layout, and sleek minimalist typography.
          </p>
        </div>

        <div
          className="card"
          onClick={() => setSelectedTemplate("classic")}
          style={{
            padding: "16px",
            cursor: "pointer",
            border: `2px solid ${selectedTemplate === "classic" ? "#1a365d" : "var(--border-color)"}`,
            background: selectedTemplate === "classic" ? "rgba(26, 54, 93, 0.05)" : "var(--card-bg)",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
            <span style={{ fontWeight: 700, fontSize: "1rem", color: "#1a365d" }}>Template A — Classic CIL Reference</span>
            {selectedTemplate === "classic" && <span style={{ fontSize: "0.72rem", background: "#1a365d", color: "#fff", padding: "2px 8px", borderRadius: "10px", fontWeight: 600 }}>ACTIVE</span>}
          </div>
          <p style={{ margin: 0, fontSize: "0.83rem", color: "var(--text-secondary)", lineHeight: "1.4" }}>
            Official subsidiary annual report aesthetic with deep navy corporate headers, serif typography, formal bordered data tables, and statutory layout.
          </p>
        </div>
      </div>

      {/* Render Telemetry & Quick Action Bar */}
      {renderResult && (
        <div className="card" style={{ padding: "16px 20px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "24px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <BookOpen size={16} color="#2563eb" />
                <span style={{ fontSize: "0.85rem" }}>
                  Pages: <strong>{renderResult.page_count}</strong>
                </span>
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <HardDrive size={16} color="#10b981" />
                <span style={{ fontSize: "0.85rem" }}>
                  Size: <strong>{formatBytes(renderResult.file_size_bytes)}</strong>
                </span>
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <Clock size={16} color="#f59e0b" />
                <span style={{ fontSize: "0.85rem" }}>
                  Render Time: <strong>{renderResult.render_time_seconds}s</strong>
                </span>
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <Layers size={16} color="#8b5cf6" />
                <span style={{ fontSize: "0.85rem" }}>
                  Engine: <strong style={{ textTransform: "uppercase" }}>{renderResult.renderer_engine}</strong>
                </span>
              </div>
            </div>

            <div style={{ display: "flex", gap: "10px" }}>
              <a
                href={`${API_BASE}/api/v1/reports/${selectedReportId}/export/pdf?template=${selectedTemplate}`}
                target="_blank"
                rel="noreferrer"
                className="btn btn-primary"
                style={{ textDecoration: "none" }}
              >
                <FileDown size={14} /> Download PDF
              </a>

              <a
                href={`${API_BASE}/api/v1/reports/${selectedReportId}/export/html?template=${selectedTemplate}`}
                target="_blank"
                rel="noreferrer"
                className="btn btn-secondary"
                style={{ textDecoration: "none" }}
              >
                <ExternalLink size={14} /> Open HTML Print View
              </a>
            </div>
          </div>
        </div>
      )}

      {/* Live Document Preview Frame */}
      {selectedReportId ? (
        <div className="card" style={{ padding: "0", overflow: "hidden", height: "650px", display: "flex", flexDirection: "column" }}>
          <div style={{ padding: "10px 16px", background: "var(--bg-secondary)", borderBottom: "1px solid var(--border-color)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--text-secondary)" }}>
              DOCUMENT VIEW: {selectedReportId}_{selectedTemplate}.html
            </span>
            <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>Air-Gapped Local Renderer</span>
          </div>

          <iframe
            title="Report Preview"
            src={`${API_BASE}/api/v1/reports/${selectedReportId}/export/html?template=${selectedTemplate}`}
            style={{ width: "100%", height: "100%", border: "none", background: "#ffffff" }}
          />
        </div>
      ) : (
        <div className="card" style={{ textAlign: "center", padding: "60px 0", color: "var(--text-secondary)" }}>
          <FileText size={42} style={{ opacity: 0.3, marginBottom: "12px" }} />
          <p>Select a generated corporate report to preview and export to PDF.</p>
        </div>
      )}
    </div>
  );
};
