import React from "react";
import {
  FileText,
  Layers,
  Activity,
  Bot,
  ArrowRight,
  Shield,
  FileCheck,
  Sparkles,
} from "lucide-react";
import { SystemDiagnosticsWidget, DiagnosticsData } from "./SystemDiagnosticsWidget";
import { NavTab } from "./Sidebar";

interface DashboardViewProps {
  diagnostics: DiagnosticsData | null;
  isLoadingDiag: boolean;
  onNavigate: (tab: NavTab) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  diagnostics,
  isLoadingDiag,
  onNavigate,
}) => {
  return (
    <div className="dashboard-grid">
      {/* Hero Banner */}
      <div className="card col-span-12 banner-card">
        <div className="banner-content">
          <div className="banner-badge">
            <Sparkles size={13} />
            <span>Architecture Phase 0 Initialized</span>
          </div>
          <h2 className="banner-title">
            Local-First Report Intelligence Platform
          </h2>
          <p className="banner-desc">
            Generating high-volume (300–400 page) CIL subsidiary annual reports with strict local execution,
            deterministic numerical calculations, and coordinate-level provenance tracking.
          </p>
          <div style={{ marginTop: "18px", display: "flex", gap: "12px" }}>
            <button
              className="btn btn-primary"
              onClick={() => onNavigate("sources")}
            >
              <span>Explore Data Sources</span>
              <ArrowRight size={15} />
            </button>
            <button
              className="btn btn-secondary"
              onClick={() => onNavigate("validation")}
            >
              <span>Validation Engine</span>
            </button>
          </div>
        </div>

        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "8px",
            background: "rgba(10, 13, 18, 0.6)",
            padding: "16px 20px",
            borderRadius: "var(--radius-md)",
            border: "1px solid var(--border-subtle)",
            minWidth: "220px",
          }}
        >
          <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", textTransform: "uppercase" }}>
            Air-gapped Status
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "var(--status-success)", fontWeight: 700 }}>
            <Shield size={18} />
            <span>Strictly Local Mode</span>
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
            Zero cloud AI or remote OCR dependencies
          </div>
        </div>
      </div>

      {/* 4 Stat Cards */}
      <div className="card col-span-3 stat-card">
        <div className="stat-icon">
          <FileText size={22} />
        </div>
        <div className="stat-info">
          <span className="stat-label">Source Documents</span>
          <span className="stat-value">Local FS</span>
          <span className="stat-hint">Phase 1: Folder Connector</span>
        </div>
      </div>

      <div className="card col-span-3 stat-card">
        <div className="stat-icon cyan">
          <Layers size={22} />
        </div>
        <div className="stat-info">
          <span className="stat-label">Canonical Model</span>
          <span className="stat-value">Ready</span>
          <span className="stat-hint">Section 9 Spec implemented</span>
        </div>
      </div>

      <div className="card col-span-3 stat-card">
        <div className="stat-icon emerald">
          <Activity size={22} />
        </div>
        <div className="stat-info">
          <span className="stat-label">Job System</span>
          <span className="stat-value">12 Stages</span>
          <span className="stat-hint">Section 27 observable jobs</span>
        </div>
      </div>

      <div className="card col-span-3 stat-card">
        <div className="stat-icon">
          <Bot size={22} />
        </div>
        <div className="stat-info">
          <span className="stat-label">AI Gateway</span>
          <span className="stat-value">Modular</span>
          <span className="stat-hint">llama.cpp / Gemma / Llama</span>
        </div>
      </div>

      {/* 7 Cols: Architectural Roadmap & Verification */}
      <div className="card col-span-7">
        <div className="card-header">
          <h3 className="card-title">
            <FileCheck size={18} color="var(--accent-cyan)" />
            Implementation Roadmap Status
          </h3>
          <span style={{ fontSize: "0.75rem", color: "var(--accent-gold)", fontWeight: 600 }}>
            Phase 0 Complete
          </span>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginTop: "10px" }}>
          <div
            style={{
              padding: "12px 14px",
              borderRadius: "var(--radius-sm)",
              background: "rgba(16, 185, 129, 0.08)",
              border: "1px solid rgba(16, 185, 129, 0.2)",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <div>
              <div style={{ fontWeight: 600, fontSize: "0.85rem", color: "var(--status-success)" }}>
                ✓ Phase 0 — Architecture & Workspace Foundation
              </div>
              <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "2px" }}>
                Repository monorepo, canonical models, DataConnector & AIGateway contracts, FastAPI service, tests.
              </div>
            </div>
            <span style={{ fontSize: "0.72rem", background: "var(--status-success)", color: "#000", fontWeight: 700, padding: "2px 8px", borderRadius: "4px" }}>
              Active
            </span>
          </div>

          <div
            style={{
              padding: "12px 14px",
              borderRadius: "var(--radius-sm)",
              background: "var(--bg-elevated)",
              border: "1px solid var(--border-subtle)",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <div>
              <div style={{ fontWeight: 600, fontSize: "0.85rem", color: "var(--text-primary)" }}>
                Phase 1 — Local Data Connector
              </div>
              <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "2px" }}>
                Folder selection, recursive file discovery, SHA-256 fingerprinting, time-based categorization.
              </div>
            </div>
            <span style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>Next Phase</span>
          </div>

          <div
            style={{
              padding: "12px 14px",
              borderRadius: "var(--radius-sm)",
              background: "var(--bg-elevated)",
              border: "1px solid var(--border-subtle)",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <div>
              <div style={{ fontWeight: 600, fontSize: "0.85rem", color: "var(--text-primary)" }}>
                Phase 2 — Document Extraction & OCR
              </div>
              <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "2px" }}>
                Docling / PaddleOCR for scanned PDFs, openpyxl for XLSX cell mapping, canonical population.
              </div>
            </div>
            <span style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>Upcoming</span>
          </div>

          <div
            style={{
              padding: "12px 14px",
              borderRadius: "var(--radius-sm)",
              background: "var(--bg-elevated)",
              border: "1px solid var(--border-subtle)",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <div>
              <div style={{ fontWeight: 600, fontSize: "0.85rem", color: "var(--text-primary)" }}>
                Phase 3 — Search & SQLite FTS5
              </div>
              <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "2px" }}>
                Hybrid lexical and temporal evidence ranking with coordinate provenance.
              </div>
            </div>
            <span style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>Upcoming</span>
          </div>
        </div>
      </div>

      {/* 5 Cols: Host Environment Diagnostics */}
      <SystemDiagnosticsWidget diagnostics={diagnostics} isLoading={isLoadingDiag} />
    </div>
  );
};
