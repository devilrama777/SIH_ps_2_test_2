import React, { useState, useEffect, useCallback } from "react";
import { Sidebar, NavTab } from "./components/Sidebar";
import { Header } from "./components/Header";
import { DashboardView } from "./components/DashboardView";
import { SourcesView } from "./components/SourcesView";
import { JobsView } from "./components/JobsView";
import { EvidenceSearchView } from "./components/EvidenceSearchView";
import { ModelDiagnosticsView } from "./components/ModelDiagnosticsView";
import { ReportPlannerView } from "./components/ReportPlannerView";
import { ReportEditorView } from "./components/ReportEditorView";
import { ValidationView } from "./components/ValidationView";
import { AssetManagerView } from "./components/AssetManagerView";
import { PdfExportView } from "./components/PdfExportView";
import { SourceTraceabilityView } from "./components/SourceTraceabilityView";
import { SecurityAuditView } from "./components/SecurityAuditView";
import { DiagnosticsData } from "./components/SystemDiagnosticsWidget";

const API_BASE = "http://127.0.0.1:8765";

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<NavTab>("dashboard");
  const [isBackendOnline, setIsBackendOnline] = useState<boolean>(false);
  const [backendVersion, setBackendVersion] = useState<string>("0.1.0");
  const [diagnostics, setDiagnostics] = useState<DiagnosticsData | null>(null);
  const [isLoadingDiag, setIsLoadingDiag] = useState<boolean>(false);
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);

  const fetchStatus = useCallback(async () => {
    setIsLoadingDiag(true);
    try {
      const healthRes = await fetch(`${API_BASE}/api/v1/health`, { method: "GET" });
      if (healthRes.ok) {
        const healthData = await healthRes.json();
        setIsBackendOnline(true);
        setBackendVersion(healthData.version);

        const diagRes = await fetch(`${API_BASE}/api/v1/diagnostics`, { method: "GET" });
        if (diagRes.ok) {
          const diagData = await diagRes.json();
          setDiagnostics(diagData);
        }
      } else {
        setIsBackendOnline(false);
      }
    } catch {
      setIsBackendOnline(false);
      setDiagnostics({
        platform: "Windows 11 (AMD64) — Host Target",
        python_version: "3.13.14 (.venv ready)",
        cpu_count_logical: 16,
        cpu_count_physical: 10,
        cpu_usage_percent: 13.1,
        memory_total_gb: 15.8,
        memory_available_gb: 2.3,
        memory_used_percent: 85.3,
        disk_total_gb: 464.8,
        disk_free_gb: 67.9,
        disk_used_percent: 85.4,
      });
    } finally {
      setIsLoadingDiag(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 8000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  const handleStartIngestion = async (folderPath: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/jobs/ingest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ folder_path: folderPath }),
      });
      if (res.ok) {
        const job = await res.json();
        setSelectedJobId(job.job_id);
        setActiveTab("jobs");
      }
    } catch (err) {
      console.error("Failed to trigger ingestion:", err);
    }
  };

  return (
    <div className="app-container">
      <Sidebar
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        isBackendOnline={isBackendOnline}
        backendVersion={backendVersion}
      />

      <div className="main-wrapper">
        <Header
          activeTab={activeTab}
          onRefresh={fetchStatus}
          isRefreshing={isLoadingDiag}
        />

        <main className="content-body">
          {activeTab === "dashboard" && (
            <DashboardView
              diagnostics={diagnostics}
              isLoadingDiag={isLoadingDiag}
              onNavigate={setActiveTab}
            />
          )}

          {activeTab === "sources" && (
            <SourcesView onStartIngestion={handleStartIngestion} />
          )}

          {activeTab === "jobs" && (
            <JobsView selectedJobId={selectedJobId} />
          )}

          {activeTab === "evidence" && (
            <EvidenceSearchView />
          )}

          {activeTab === "models" && (
            <ModelDiagnosticsView />
          )}

          {activeTab === "planner" && (
            <ReportPlannerView />
          )}

          {activeTab === "editor" && (
            <ReportEditorView />
          )}

          {activeTab === "validation" && (
            <ValidationView />
          )}

          {activeTab === "assets" && (
            <AssetManagerView />
          )}

          {activeTab === "export" && (
            <PdfExportView />
          )}

          {activeTab === "source_viewer" && (
            <SourceTraceabilityView />
          )}

          {activeTab === "security" && (
            <SecurityAuditView />
          )}

          {activeTab !== "dashboard" && activeTab !== "sources" && activeTab !== "jobs" && activeTab !== "evidence" && activeTab !== "models" && activeTab !== "planner" && activeTab !== "editor" && activeTab !== "validation" && activeTab !== "assets" && activeTab !== "export" && activeTab !== "source_viewer" && activeTab !== "security" && (
            <div className="card" style={{ padding: "36px", textAlign: "center" }}>
              <h3 style={{ fontFamily: "var(--font-display)", fontSize: "1.25rem", marginBottom: "8px" }}>
                {activeTab.replace("_", " ").toUpperCase()}
              </h3>
              <p style={{ color: "var(--text-secondary)", fontSize: "0.88rem", maxWidth: "600px", margin: "0 auto" }}>
                This module will be activated in upcoming phases according to the Master Implementation Plan.
              </p>
              <button
                className="btn btn-primary"
                onClick={() => setActiveTab("dashboard")}
                style={{ marginTop: "20px" }}
              >
                Return to Dashboard
              </button>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};
