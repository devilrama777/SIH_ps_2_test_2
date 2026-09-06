import React from "react";
import { RefreshCw, Shield, HelpCircle } from "lucide-react";
import { NavTab } from "./Sidebar";

interface HeaderProps {
  activeTab: NavTab;
  onRefresh: () => void;
  isRefreshing: boolean;
}

const titles: Record<NavTab, { title: string; subtitle: string }> = {
  dashboard: {
    title: "System Dashboard",
    subtitle: "Local intelligence metrics, pipeline status, and host diagnostics",
  },
  wizard: {
    title: "Enterprise Report Wizard",
    subtitle: "End-to-end autonomous report generation, verification, and authorized upload",
  },
  sources: {
    title: "Data Sources & Folder Connectors",
    subtitle: "Local directories, annual reports, spreadsheets, and scanned PDFs",
  },
  jobs: {
    title: "Background Processing Jobs",
    subtitle: "Observable ingestion, OCR, extraction, and generation tasks",
  },
  evidence: {
    title: "Evidence Search & Hybrid Retrieval",
    subtitle: "Query source documents via lexical FTS5 and temporal indexing",
  },
  models: {
    title: "Local AI Gateway & Model Evaluation",
    subtitle: "Air-gapped model backends, citation grounding, and 8-task benchmark harness",
  },
  planner: {
    title: "Report Structure Planner",
    subtitle: "Dynamic chapter organization, mandatory/discovered sections",
  },
  editor: {
    title: "Report Editor & Narrative Workspace",
    subtitle: "Section-by-section generation with full evidence traceability",
  },
  source_viewer: {
    title: "Source Provenance Inspector",
    subtitle: "Inspect exact source pages, bounding boxes, and spreadsheet cells",
  },
  assets: {
    title: "Image & Chart Asset Manager",
    subtitle: "Analyze photographs, duplicate detection, and layout placement",
  },
  validation: {
    title: "Deterministic Validation Engine",
    subtitle: "Mathematical, temporal, provenance, and structural consistency checks",
  },
  export: {
    title: "PDF Composition & Rendering",
    subtitle: "Classic Reference and Modern Corporate templates",
  },
  security: {
    title: "Security Baseline & Audit Logs",
    subtitle: "Air-gapped operation, credential isolation, and audit trail",
  },
  settings: {
    title: "Application Settings",
    subtitle: "Model inference paths, storage quotas, and runtime configurations",
  },
};

export const Header: React.FC<HeaderProps> = ({ activeTab, onRefresh, isRefreshing }) => {
  const current = titles[activeTab] || titles.dashboard;

  return (
    <header className="top-header">
      <div className="header-title">
        <h2>{current.title}</h2>
        <span>{current.subtitle}</span>
      </div>

      <div className="header-actions">
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "6px",
            fontSize: "0.75rem",
            background: "rgba(16, 185, 129, 0.12)",
            color: "var(--status-success)",
            padding: "4px 10px",
            borderRadius: "9999px",
            border: "1px solid rgba(16, 185, 129, 0.25)",
          }}
        >
          <Shield size={14} />
          <span>Local-Only Airgap</span>
        </div>

        <button
          className="btn-icon"
          onClick={onRefresh}
          title="Refresh Diagnostics"
          disabled={isRefreshing}
        >
          <RefreshCw size={16} className={isRefreshing ? "animate-spin" : ""} />
        </button>

        <button className="btn-icon" title="Documentation">
          <HelpCircle size={16} />
        </button>
      </div>
    </header>
  );
};
