import React, { useState, useEffect } from "react";
import {
  Activity,
  HardDrive,
  Trash2,
  Download,
  ShieldCheck,
  RefreshCw,
  Clock,
  Server,
  CheckCircle,
  AlertTriangle,
  Lock
} from "lucide-react";

interface CategorySummary {
  category: string;
  description: string;
  path: string;
  file_count: number;
  total_bytes: number;
  formatted_size: string;
  is_safe_to_clean: boolean;
}

interface StorageBreakdown {
  categories: Record<string, CategorySummary>;
  total_workspace_bytes: number;
}

interface TelemetryEvent {
  stage_name: string;
  duration_sec: number;
  status: string;
  start_time: string;
  metrics: Record<string, any>;
}

export const DiagnosticsView: React.FC = () => {
  const [storageData, setStorageData] = useState<StorageBreakdown | null>(null);
  const [telemetryEvents, setTelemetryEvents] = useState<TelemetryEvent[]>([]);
  const [aggregates, setAggregates] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(true);
  const [cleanupMessage, setCleanupMessage] = useState<string | null>(null);
  const [exportResult, setExportResult] = useState<any | null>(null);
  const [exporting, setExporting] = useState(false);
  const [cleaning, setCleaning] = useState(false);

  // Invalidation test state
  const [testSource, setTestSource] = useState("CCL_Production_Offtake_FY24.xlsx");
  const [invalidationResult, setInvalidationResult] = useState<any | null>(null);

  const fetchDiagnostics = async () => {
    setLoading(true);
    try {
      const [storageRes, telemRes] = await Promise.all([
        fetch("http://127.0.0.1:8000/api/v1/storage/breakdown").then(r => r.json()).catch(() => null),
        fetch("http://127.0.0.1:8000/api/v1/observability/telemetry?limit=25").then(r => r.json()).catch(() => null),
      ]);

      if (storageRes) setStorageData(storageRes);
      if (telemRes) {
        setTelemetryEvents(telemRes.recent_events || []);
        setAggregates(telemRes.stage_aggregates || {});
      }
    } catch (err) {
      console.error("Failed to load diagnostics:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDiagnostics();
  }, []);

  const handleCleanup = async () => {
    setCleaning(true);
    setCleanupMessage(null);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/v1/storage/cleanup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ max_age_seconds: 0.0, dry_run: false }),
      });
      const data = await res.json();
      setCleanupMessage(`Cleaned ${data.deleted_file_count} temporary files, freed ${data.formatted_freed}. Original sources remain 100% protected.`);
      fetchDiagnostics();
    } catch (err: any) {
      setCleanupMessage(`Cleanup failed: ${err.message}`);
    } finally {
      setCleaning(false);
    }
  };

  const handleExportDiagnostics = async () => {
    setExporting(true);
    setExportResult(null);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/v1/observability/export-diagnostics", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      const data = await res.json();
      setExportResult(data);
    } catch (err: any) {
      alert(`Export failed: ${err.message}`);
    } finally {
      setExporting(false);
    }
  };

  const handleTestInvalidate = async () => {
    try {
      const dummyReport = {
        report_id: "rep_mock",
        sections: [
          {
            section_id: "sec_exec",
            title: "Executive Summary & Key Highlights",
            source_refs: ["CCL_Production_Offtake_FY24.xlsx", "CCL_Annual_Report_FY24_Highlights.txt"]
          },
          {
            section_id: "sec_prod",
            title: "Production and Operational Performance",
            source_refs: ["CCL_Production_Offtake_FY24.xlsx"]
          },
          {
            section_id: "sec_csr",
            title: "CSR and Community Development",
            source_refs: ["CSR_Community_Development_FY24.docx"]
          },
          {
            section_id: "sec_audit",
            title: "CAG Audit Compliance",
            source_refs: ["CAG_Audit_Compliance_FY24.txt"]
          }
        ]
      };

      const res = await fetch("http://127.0.0.1:8000/api/v1/reports/incremental/invalidate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          report_data: dummyReport,
          changed_sources: [testSource],
        }),
      });
      const data = await res.json();
      setInvalidationResult(data);
    } catch (err: any) {
      alert(`Invalidation test failed: ${err.message}`);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 animate-fade-in text-slate-100">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-700/60 pb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-3">
            <Activity className="w-7 h-7 text-emerald-400" />
            System Observability & Storage Lifecycle
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Section 28 incremental dependency graph, Section 35 sanitized diagnostics, and Section 37 storage retention.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchDiagnostics}
            disabled={loading}
            className="flex items-center gap-2 px-3 py-2 text-xs font-semibold bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 rounded-lg transition"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            Refresh Metrics
          </button>
          <button
            onClick={handleExportDiagnostics}
            disabled={exporting}
            className="flex items-center gap-2 px-4 py-2 text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg transition shadow-md shadow-emerald-950/40"
          >
            <Download className="w-4 h-4" />
            {exporting ? "Generating..." : "Export Sanitized Diagnostics (.zip)"}
          </button>
        </div>
      </div>

      {/* Export Result Notice */}
      {exportResult && (
        <div className="p-4 bg-emerald-950/40 border border-emerald-500/40 rounded-xl flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <ShieldCheck className="w-6 h-6 text-emerald-400 shrink-0" />
            <div>
              <p className="text-sm font-semibold text-emerald-200">
                Diagnostic Bundle Generated: {exportResult.bundle_filename}
              </p>
              <p className="text-xs text-emerald-400/80 font-mono mt-0.5">
                SHA-256: {exportResult.sha256_hash} ({(exportResult.file_size_bytes / 1024).toFixed(1)} KB)
              </p>
            </div>
          </div>
          <a
            href={`http://127.0.0.1:8000/api/v1/observability/download-diagnostics/${exportResult.bundle_filename}`}
            className="px-3 py-1.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs rounded-lg transition"
            download
          >
            Download ZIP
          </a>
        </div>
      )}

      {/* Storage Breakdown Cards */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-slate-200 flex items-center gap-2">
            <HardDrive className="w-5 h-5 text-sky-400" />
            Workspace Storage Allocation (Section 37)
          </h2>
          <button
            onClick={handleCleanup}
            disabled={cleaning}
            className="flex items-center gap-2 px-3 py-1.5 text-xs font-semibold bg-rose-950/50 hover:bg-rose-900/60 border border-rose-600/40 text-rose-200 rounded-lg transition"
          >
            <Trash2 className="w-3.5 h-3.5 text-rose-400" />
            {cleaning ? "Cleaning Cache..." : "Purge Temporary Render Cache"}
          </button>
        </div>

        {cleanupMessage && (
          <div className="p-3 bg-slate-800/80 border border-slate-700 text-xs text-slate-300 rounded-lg flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
            {cleanupMessage}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {storageData && Object.values(storageData.categories).map((cat) => {
            const isProtected = cat.category === "original_source";
            const isTemp = cat.category === "render_temp";

            return (
              <div
                key={cat.category}
                className={`p-4 rounded-xl border transition flex flex-col justify-between ${
                  isProtected
                    ? "bg-amber-950/20 border-amber-500/30"
                    : isTemp
                    ? "bg-slate-800/60 border-slate-700/80"
                    : "bg-slate-900/60 border-slate-800"
                }`}
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                      {cat.category.replace("_", " ")}
                    </span>
                    {isProtected ? (
                      <span className="flex items-center gap-1 text-[10px] font-semibold text-amber-400 bg-amber-900/40 px-2 py-0.5 rounded-full border border-amber-600/30">
                        <Lock className="w-3 h-3" /> Protected
                      </span>
                    ) : isTemp ? (
                      <span className="text-[10px] font-semibold text-sky-400 bg-sky-950 px-2 py-0.5 rounded-full border border-sky-800/40">
                        Ephemeral
                      </span>
                    ) : null}
                  </div>
                  <div className="text-xl font-extrabold text-white">
                    {cat.formatted_size}
                  </div>
                  <div className="text-xs text-slate-400 mt-1">
                    {cat.file_count} tracked files
                  </div>
                </div>
                <p className="text-[11px] text-slate-400 mt-3 pt-3 border-t border-slate-800 line-clamp-2">
                  {cat.description}
                </p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Section 28 Incremental Invalidation Engine */}
      <div className="p-6 bg-slate-900/80 border border-slate-800 rounded-2xl space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <RefreshCw className="w-4 h-4 text-indigo-400" />
              Incremental Section Invalidation Engine (Section 28)
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Simulate updating an upstream source to compute the minimal transitive closure of dirty sections.
            </p>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-3">
          <input
            type="text"
            value={testSource}
            onChange={(e) => setTestSource(e.target.value)}
            placeholder="e.g. CCL_Production_Offtake_FY24.xlsx"
            className="flex-1 bg-slate-800/80 border border-slate-700 px-3.5 py-2 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
          />
          <button
            onClick={handleTestInvalidate}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs rounded-lg transition"
          >
            Compute Affected Sections
          </button>
        </div>

        {invalidationResult && (
          <div className="p-4 bg-slate-950/60 rounded-xl border border-slate-800 space-y-3">
            <div className="flex items-center gap-4 text-xs">
              <span className="text-slate-400">Total Sections: <strong>{invalidationResult.total_sections}</strong></span>
              <span className="text-amber-400 font-semibold">Dirty Sections: <strong>{invalidationResult.dirty_sections.length}</strong></span>
              <span className="text-emerald-400 font-semibold">Clean (Preserved): <strong>{invalidationResult.clean_sections.length}</strong></span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              <div className="space-y-1">
                <span className="text-xs font-bold text-rose-400 uppercase tracking-wider flex items-center gap-1.5">
                  <AlertTriangle className="w-3.5 h-3.5" /> Requires Surgical Regeneration:
                </span>
                <ul className="text-xs font-mono text-slate-300 space-y-1 pl-4 list-disc">
                  {invalidationResult.dirty_sections.map((id: string) => (
                    <li key={id} className="text-rose-300">{id}</li>
                  ))}
                </ul>
              </div>

              <div className="space-y-1">
                <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                  <CheckCircle className="w-3.5 h-3.5" /> Preserved Intact (Cached):
                </span>
                <ul className="text-xs font-mono text-slate-300 space-y-1 pl-4 list-disc">
                  {invalidationResult.clean_sections.map((id: string) => (
                    <li key={id} className="text-emerald-300">{id}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Operational Stage Aggregates & Recent Telemetry */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="p-5 bg-slate-900/80 border border-slate-800 rounded-xl space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Clock className="w-4 h-4 text-teal-400" />
            Stage Execution Benchmarks
          </h3>
          <div className="space-y-2">
            {Object.entries(aggregates).length === 0 ? (
              <p className="text-xs text-slate-400">No stage runs recorded yet.</p>
            ) : (
              Object.entries(aggregates).map(([stage, data]: [string, any]) => (
                <div key={stage} className="p-2.5 bg-slate-950/40 rounded-lg border border-slate-800/80 flex items-center justify-between text-xs">
                  <div>
                    <span className="font-semibold text-slate-200">{stage}</span>
                    <p className="text-[10px] text-slate-400">{data.count} executions</p>
                  </div>
                  <div className="text-right">
                    <span className="font-mono text-emerald-400">{data.avg_duration}s avg</span>
                    {data.failures > 0 && (
                      <p className="text-[10px] text-rose-400">{data.failures} errors</p>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="lg:col-span-2 p-5 bg-slate-900/80 border border-slate-800 rounded-xl space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Server className="w-4 h-4 text-sky-400" />
            Recent Telemetry Events (Section 35)
          </h3>
          <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
            {telemetryEvents.length === 0 ? (
              <p className="text-xs text-slate-400">No telemetry logged in current session.</p>
            ) : (
              telemetryEvents.slice().reverse().map((ev, idx) => (
                <div key={idx} className="p-2.5 bg-slate-950/60 rounded-lg border border-slate-800/80 flex items-center justify-between text-xs font-mono">
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${ev.status === "SUCCESS" ? "bg-emerald-400" : "bg-rose-400"}`} />
                    <span className="text-slate-200 font-semibold">{ev.stage_name}</span>
                  </div>
                  <div className="flex items-center gap-4 text-slate-400 text-[11px]">
                    <span>{ev.duration_sec}s</span>
                    <span className="text-slate-400">{new Date(ev.start_time).toLocaleTimeString()}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
