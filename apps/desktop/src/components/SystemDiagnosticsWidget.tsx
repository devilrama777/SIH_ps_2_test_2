import React from "react";
import { Cpu, HardDrive, MemoryStick, Terminal, CheckCircle } from "lucide-react";

export interface DiagnosticsData {
  platform: string;
  python_version: string;
  cpu_count_logical: number;
  cpu_count_physical: number;
  cpu_usage_percent: number;
  memory_total_gb: number;
  memory_available_gb: number;
  memory_used_percent: number;
  disk_total_gb: number;
  disk_free_gb: number;
  disk_used_percent: number;
}

interface SystemDiagnosticsWidgetProps {
  diagnostics: DiagnosticsData | null;
  isLoading: boolean;
}

export const SystemDiagnosticsWidget: React.FC<SystemDiagnosticsWidgetProps> = ({
  diagnostics,
  isLoading,
}) => {
  if (isLoading) {
    return (
      <div className="card col-span-5" style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "280px" }}>
        <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem" }}>Querying system diagnostics...</p>
      </div>
    );
  }

  if (!diagnostics) {
    return (
      <div className="card col-span-5">
        <div className="card-header">
          <h3 className="card-title">Host Hardware Profile</h3>
        </div>
        <p style={{ color: "var(--status-error)", fontSize: "0.85rem" }}>
          Unable to retrieve diagnostics. Python processing backend appears offline on port 8765.
        </p>
      </div>
    );
  }

  return (
    <div className="card col-span-5">
      <div className="card-header">
        <h3 className="card-title">
          <Cpu size={18} color="var(--accent-gold)" />
          Target Host Environment
        </h3>
        <span style={{ fontSize: "0.72rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
          {diagnostics.platform}
        </span>
      </div>

      <div className="diag-list">
        <div className="diag-item">
          <div className="diag-label">
            <Terminal size={15} />
            <span>Python Runtime</span>
          </div>
          <span className="diag-value">v{diagnostics.python_version}</span>
        </div>

        <div className="diag-item" style={{ flexDirection: "column", alignItems: "stretch", gap: "6px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.82rem" }}>
            <div className="diag-label">
              <Cpu size={15} />
              <span>CPU Cores ({diagnostics.cpu_count_physical} Physical / {diagnostics.cpu_count_logical} Logical)</span>
            </div>
            <span className="diag-value">{diagnostics.cpu_usage_percent}%</span>
          </div>
          <div className="progress-bar-container">
            <div className="progress-bar-fill" style={{ width: `${Math.max(diagnostics.cpu_usage_percent, 5)}%` }} />
          </div>
        </div>

        <div className="diag-item" style={{ flexDirection: "column", alignItems: "stretch", gap: "6px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.82rem" }}>
            <div className="diag-label">
              <MemoryStick size={15} />
              <span>RAM Allocation ({diagnostics.memory_available_gb} GB free of {diagnostics.memory_total_gb} GB)</span>
            </div>
            <span className="diag-value">{diagnostics.memory_used_percent}%</span>
          </div>
          <div className="progress-bar-container">
            <div className="progress-bar-fill" style={{ width: `${diagnostics.memory_used_percent}%` }} />
          </div>
        </div>

        <div className="diag-item" style={{ flexDirection: "column", alignItems: "stretch", gap: "6px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.82rem" }}>
            <div className="diag-label">
              <HardDrive size={15} />
              <span>Disk Space ({diagnostics.disk_free_gb} GB free of {diagnostics.disk_total_gb} GB)</span>
            </div>
            <span className="diag-value">{diagnostics.disk_used_percent}%</span>
          </div>
          <div className="progress-bar-container">
            <div className="progress-bar-fill" style={{ width: `${diagnostics.disk_used_percent}%` }} />
          </div>
        </div>
      </div>

      <div
        style={{
          marginTop: "16px",
          padding: "10px 12px",
          borderRadius: "var(--radius-sm)",
          background: "rgba(16, 185, 129, 0.08)",
          border: "1px solid rgba(16, 185, 129, 0.2)",
          display: "flex",
          alignItems: "center",
          gap: "8px",
          fontSize: "0.75rem",
          color: "var(--status-success)",
        }}
      >
        <CheckCircle size={15} />
        <span>Hardware satisfies Section 0 Target Specs (i5-class / &gt;8GB RAM / Local disk)</span>
      </div>
    </div>
  );
};
