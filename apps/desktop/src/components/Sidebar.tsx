import React from "react";
import {
  LayoutDashboard,
  FolderOpen,
  Cpu,
  Search,
  Bot,
  FileSpreadsheet,
  FileEdit,
  Eye,
  Image,
  CheckCircle2,
  FileDown,
  Settings,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

export type NavTab =
  | "dashboard"
  | "wizard"
  | "sources"
  | "jobs"
  | "evidence"
  | "models"
  | "planner"
  | "editor"
  | "source_viewer"
  | "assets"
  | "validation"
  | "export"
  | "settings"
  | "security";

interface SidebarProps {
  activeTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  isBackendOnline: boolean;
  backendVersion: string;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onSelectTab,
  isBackendOnline,
  backendVersion,
}) => {
  const mainNavItems = [
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "wizard", label: "New Report Wizard", icon: Sparkles, badge: "Master" },
    { id: "sources", label: "Data Sources", icon: FolderOpen, badge: "Local" },
    { id: "jobs", label: "Processing Jobs", icon: Cpu },
    { id: "evidence", label: "Evidence Search", icon: Search },
    { id: "models", label: "Local AI & Models", icon: Bot, badge: "Air-gap" },
    { id: "planner", label: "Report Planner", icon: FileSpreadsheet },
    { id: "editor", label: "Report Editor", icon: FileEdit },
    { id: "source_viewer", label: "Source Viewer", icon: Eye },
    { id: "assets", label: "Asset Manager", icon: Image },
    { id: "validation", label: "Validation Engine", icon: CheckCircle2 },
    { id: "export", label: "PDF Export", icon: FileDown },
  ];

  const bottomNavItems = [
    { id: "security", label: "Security & Audit", icon: ShieldCheck },
    { id: "settings", label: "Settings", icon: Settings },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="brand-badge">CIL</div>
        <div className="brand-info">
          <h1>Report AI</h1>
          <p>Local Document Intel</p>
        </div>
      </div>

      <nav className="sidebar-nav">
        <div className="nav-section-title">Workflow Operations</div>
        {mainNavItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              className={`nav-item ${isActive ? "active" : ""}`}
              onClick={() => onSelectTab(item.id as NavTab)}
              style={{ width: "100%", textAlign: "left", background: "none", border: "none", font: "inherit" }}
            >
              <Icon size={18} />
              <span>{item.label}</span>
              {item.badge && <span className="nav-item-badge">{item.badge}</span>}
            </button>
          );
        })}

        <div className="nav-section-title" style={{ marginTop: "16px" }}>Administration</div>
        {bottomNavItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              className={`nav-item ${isActive ? "active" : ""}`}
              onClick={() => onSelectTab(item.id as NavTab)}
              style={{ width: "100%", textAlign: "left", background: "none", border: "none", font: "inherit" }}
            >
              <Icon size={18} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div className="connection-status">
          <div className="status-indicator">
            <div className={`status-dot ${isBackendOnline ? "online" : ""}`} />
            <span>Python Service v{backendVersion || "0.1.0"}</span>
          </div>
          <span style={{ color: isBackendOnline ? "var(--status-success)" : "var(--status-error)", fontWeight: 600 }}>
            {isBackendOnline ? "Connected" : "Offline"}
          </span>
        </div>
      </div>
    </aside>
  );
};
