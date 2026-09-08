import React, { useState } from "react";
import {
  FolderOpen,
  Search,
  FileText,
  Play,
  Calendar,
  Layers,
  CheckCircle,
  AlertCircle,
} from "lucide-react";

interface DiscoveredFileItem {
  filename: string;
  relative_path: string;
  extension: string;
  file_size_bytes: number;
  format: string;
  temporal: {
    financial_year?: string;
    reporting_quarter?: string;
    reporting_month?: string;
    reporting_period?: string;
  };
}

interface ScanData {
  folder_path: string;
  total_files: number;
  total_size_mb: number;
  format_distribution: Record<string, number>;
  financial_years: string[];
  files: DiscoveredFileItem[];
}

interface SourcesViewProps {
  onStartIngestion: (folderPath: string) => void;
}

import { API_BASE } from "../services/config";

export const SourcesView: React.FC<SourcesViewProps> = ({ onStartIngestion }) => {
  const [folderPath, setFolderPath] = useState<string>("c:/Rama/SIH_hackathon");
  const [isScanning, setIsScanning] = useState<boolean>(false);
  const [scanResult, setScanResult] = useState<ScanData | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState<string>("");

  const handleScan = async (pathOverride?: string) => {
    const target = pathOverride || folderPath;
    if (!target.trim()) return;

    setIsScanning(true);
    setErrorMsg(null);

    try {
      const res = await fetch(`${API_BASE}/api/v1/sources/scan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ folder_path: target }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Failed to scan specified directory");
      }

      const data: ScanData = await res.json();
      setScanResult(data);
    } catch (err: any) {
      setErrorMsg(err.message || "Could not connect to processing backend");
      setScanResult(null);
    } finally {
      setIsScanning(false);
    }
  };

  const filteredFiles = scanResult?.files.filter((f) =>
    f.filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
    f.relative_path.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      {/* Folder Selection Card */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">
            <FolderOpen size={18} color="var(--accent-gold)" />
            Local Data Source Selection (Section 4)
          </h3>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
            Prototype uses local PC filesystem connector
          </span>
        </div>

        <p style={{ fontSize: "0.84rem", color: "var(--text-secondary)", marginBottom: "16px" }}>
          Select a directory containing subsidiary PDFs (digital & scanned), monthly Excel workbooks,
          Word documents, and operational CSV files.
        </p>

        <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
          <input
            type="text"
            value={folderPath}
            onChange={(e) => setFolderPath(e.target.value)}
            placeholder="Enter local absolute folder path..."
            style={{
              flex: 1,
              padding: "10px 14px",
              borderRadius: "var(--radius-sm)",
              border: "1px solid var(--border-medium)",
              background: "var(--bg-elevated)",
              color: "var(--text-primary)",
              fontSize: "0.85rem",
              fontFamily: "var(--font-mono)",
            }}
          />
          <button
            className="btn btn-primary"
            onClick={() => handleScan()}
            disabled={isScanning}
          >
            <Search size={16} />
            <span>{isScanning ? "Scanning..." : "Scan Directory"}</span>
          </button>
        </div>

        {/* Quick Presets */}
        <div style={{ display: "flex", gap: "8px", marginTop: "12px", alignItems: "center" }}>
          <span style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>Quick Paths:</span>
          <button
            className="btn btn-secondary"
            style={{ padding: "4px 10px", fontSize: "0.72rem" }}
            onClick={() => {
              setFolderPath("c:/Rama/SIH_hackathon");
              handleScan("c:/Rama/SIH_hackathon");
            }}
          >
            SIH Parent Folder
          </button>
          <button
            className="btn btn-secondary"
            style={{ padding: "4px 10px", fontSize: "0.72rem" }}
            onClick={() => {
              setFolderPath("c:/Rama/SIH_hackathon/SIH_MINE_INTEL");
              handleScan("c:/Rama/SIH_hackathon/SIH_MINE_INTEL");
            }}
          >
            Current Workspace
          </button>
        </div>

        {errorMsg && (
          <div
            style={{
              marginTop: "16px",
              padding: "10px 14px",
              borderRadius: "var(--radius-sm)",
              background: "rgba(239, 68, 68, 0.1)",
              border: "1px solid rgba(239, 68, 68, 0.25)",
              color: "var(--status-error)",
              fontSize: "0.82rem",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            <AlertCircle size={16} />
            <span>{errorMsg}</span>
          </div>
        )}
      </div>

      {/* Scan Results */}
      {scanResult && (
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          {/* Metrics summary bar */}
          <div className="dashboard-grid">
            <div className="card col-span-3 stat-card">
              <div className="stat-icon">
                <FileText size={22} />
              </div>
              <div className="stat-info">
                <span className="stat-label">Discovered Files</span>
                <span className="stat-value">{scanResult.total_files}</span>
                <span className="stat-hint">{scanResult.total_size_mb} MB total volume</span>
              </div>
            </div>

            <div className="card col-span-5">
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "8px" }}>
                Format Breakdown (Section 3 Spec)
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
                {Object.entries(scanResult.format_distribution).map(([fmt, count]) => (
                  <span
                    key={fmt}
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "6px",
                      padding: "4px 10px",
                      borderRadius: "var(--radius-sm)",
                      background: "var(--bg-elevated)",
                      border: "1px solid var(--border-subtle)",
                      fontSize: "0.78rem",
                      fontFamily: "var(--font-mono)",
                    }}
                  >
                    <span style={{ textTransform: "uppercase", color: "var(--accent-cyan)", fontWeight: 600 }}>{fmt}:</span>
                    <span style={{ color: "var(--text-primary)", fontWeight: 700 }}>{count}</span>
                  </span>
                ))}
              </div>
            </div>

            <div className="card col-span-4">
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "8px" }}>
                Detected Financial Periods
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                {scanResult.financial_years.length > 0 ? (
                  scanResult.financial_years.map((fy) => (
                    <span
                      key={fy}
                      style={{
                        padding: "3px 8px",
                        borderRadius: "var(--radius-sm)",
                        background: "rgba(245, 158, 11, 0.15)",
                        border: "1px solid rgba(245, 158, 11, 0.3)",
                        color: "var(--accent-gold)",
                        fontSize: "0.75rem",
                        fontWeight: 600,
                      }}
                    >
                      FY {fy}
                    </span>
                  ))
                ) : (
                  <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>Case B: Embedded in content</span>
                )}
              </div>
            </div>
          </div>

          {/* Action Callout */}
          <div
            className="card"
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              background: "linear-gradient(90deg, rgba(16, 185, 129, 0.1) 0%, rgba(18, 23, 33, 0.8) 100%)",
              border: "1px solid rgba(16, 185, 129, 0.25)",
            }}
          >
            <div>
              <div style={{ fontWeight: 700, fontSize: "0.95rem", color: "var(--status-success)", display: "flex", alignItems: "center", gap: "8px" }}>
                <CheckCircle size={18} />
                <span>Ready to Ingest {scanResult.total_files} Validated Source Documents</span>
              </div>
              <div style={{ fontSize: "0.78rem", color: "var(--text-secondary)", marginTop: "2px" }}>
                Spawns observable, resumable background job with SHA-256 fingerprinting and temporal indexing.
              </div>
            </div>

            <button
              className="btn btn-primary"
              onClick={() => onStartIngestion(scanResult.folder_path)}
              style={{ background: "linear-gradient(135deg, #10b981, #047857)", color: "#fff" }}
            >
              <Play size={16} />
              <span>Start Ingestion Job</span>
            </button>
          </div>

          {/* Files List Table */}
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">
                <Layers size={18} color="var(--accent-gold)" />
                Discovered Documents ({scanResult.files.length} previewed)
              </h3>
              <input
                type="text"
                placeholder="Filter files by name or path..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                style={{
                  padding: "6px 12px",
                  borderRadius: "var(--radius-sm)",
                  background: "var(--bg-elevated)",
                  border: "1px solid var(--border-subtle)",
                  color: "var(--text-primary)",
                  fontSize: "0.78rem",
                  width: "240px",
                }}
              />
            </div>

            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8rem" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid var(--border-subtle)", color: "var(--text-muted)", textAlign: "left" }}>
                    <th style={{ padding: "10px" }}>Filename</th>
                    <th style={{ padding: "10px" }}>Format</th>
                    <th style={{ padding: "10px" }}>Size</th>
                    <th style={{ padding: "10px" }}>Temporal Period</th>
                    <th style={{ padding: "10px" }}>Path</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredFiles.map((f, idx) => (
                    <tr
                      key={idx}
                      style={{
                        borderBottom: "1px solid rgba(255, 255, 255, 0.04)",
                        transition: "background var(--transition-fast)",
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.03)")}
                      onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
                    >
                      <td style={{ padding: "10px", fontWeight: 600, color: "var(--text-primary)" }}>
                        {f.filename}
                      </td>
                      <td style={{ padding: "10px" }}>
                        <span
                          style={{
                            padding: "2px 6px",
                            borderRadius: "4px",
                            background: "rgba(255, 255, 255, 0.06)",
                            fontFamily: "var(--font-mono)",
                            fontSize: "0.72rem",
                            textTransform: "uppercase",
                          }}
                        >
                          {f.format}
                        </span>
                      </td>
                      <td style={{ padding: "10px", color: "var(--text-secondary)", fontFamily: "var(--font-mono)" }}>
                        {f.file_size_bytes > 1024 * 1024
                          ? `${(f.file_size_bytes / (1024 * 1024)).toFixed(1)} MB`
                          : `${Math.round(f.file_size_bytes / 1024)} KB`}
                      </td>
                      <td style={{ padding: "10px" }}>
                        {f.temporal?.reporting_period ? (
                          <span
                            style={{
                              display: "inline-flex",
                              alignItems: "center",
                              gap: "4px",
                              color: "var(--accent-gold)",
                              fontSize: "0.75rem",
                              fontWeight: 500,
                            }}
                          >
                            <Calendar size={12} />
                            <span>{f.temporal.reporting_period}</span>
                          </span>
                        ) : (
                          <span style={{ color: "var(--text-muted)", fontSize: "0.72rem" }}>—</span>
                        )}
                      </td>
                      <td style={{ padding: "10px", color: "var(--text-muted)", fontFamily: "var(--font-mono)", fontSize: "0.72rem" }}>
                        {f.relative_path}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
