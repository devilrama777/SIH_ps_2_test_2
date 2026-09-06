import React, { useState, useEffect, useCallback } from "react";
import { Sidebar, NavTab } from "./components/Sidebar";
import { Header } from "./components/Header";
import { DashboardView } from "./components/DashboardView";
import { DiagnosticsData } from "./components/SystemDiagnosticsWidget";

const API_BASE = "http://127.0.0.1:8765";

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<NavTab>("dashboard");
  const [isBackendOnline, setIsBackendOnline] = useState<boolean>(false);
  const [backendVersion, setBackendVersion] = useState<string>("0.1.0");
  const [diagnostics, setDiagnostics] = useState<DiagnosticsData | null>(null);
  const [isLoadingDiag, setIsLoadingDiag] = useState<boolean>(false);

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
      // Fallback mock diagnostics in browser-only mode before backend process starts
      setDiagnostics({
        platform: "Windows 11 (AMD64) — Host Target",
        python_version: "3.13.14 (.venv ready)",
        cpu_count_logical: 8,
        cpu_count_physical: 4,
        cpu_usage_percent: 12.5,
        memory_total_gb: 16.0,
        memory_available_gb: 9.8,
        memory_used_percent: 38.7,
        disk_total_gb: 512.0,
        disk_free_gb: 284.5,
        disk_used_percent: 44.4,
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
          {activeTab === "dashboard" ? (
            <DashboardView
              diagnostics={diagnostics}
              isLoadingDiag={isLoadingDiag}
              onNavigate={setActiveTab}
            />
          ) : (
            <div className="card" style={{ padding: "32px", textAlign: "center" }}>
              <h3 style={{ fontFamily: "var(--font-display)", fontSize: "1.2rem", marginBottom: "8px" }}>
                {activeTab.replace("_", " ").toUpperCase()} Workspace
              </h3>
              <p style={{ color: "var(--text-secondary)", fontSize: "0.88rem", maxWidth: "600px", margin: "0 auto" }}>
                This module will be activated incrementally according to the Master Plan phases.
                Currently in <strong>Phase 0 (Architecture and Workspace Foundation)</strong>.
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
