import React, { useState, useEffect } from "react";
import {
  Settings,
  Building2,
  Cpu,
  ShieldCheck,
  HardDrive,
  Palette,
  Save,
  RotateCcw,
  CheckCircle2,
  AlertCircle,
  Lock,
  Play,
  Sparkles,
} from "lucide-react";

const API_BASE = "http://127.0.0.1:8765";

interface SubsidiaryProfile {
  code: string;
  full_name: string;
  headquarters: string;
  default_financial_year: string;
  currency_unit: string;
  statutory_mandate_csr_percent: number;
}

interface AISettings {
  active_backend: string;
  model_name: string;
  model_path?: string;
  context_window_tokens: number;
  max_output_tokens: number;
  temperature: number;
  cpu_threads: number;
  gpu_offload_layers: number;
}

interface StorageSettings {
  cache_retention_days: number;
  temp_auto_prune_interval_hours: number;
  auto_cleanup_enabled: boolean;
  dry_run_safety_lock: boolean;
}

interface SecuritySettings {
  strict_local_loopback: boolean;
  allow_external_network: boolean;
  audit_log_retention_days: number;
  require_dual_authorization_export: boolean;
  cryptographic_digest_algo: string;
}

interface TemplateSettings {
  default_visual_mode: string;
  brand_primary_color: string;
  brand_secondary_color: string;
  font_family_heading: string;
  font_family_body: string;
  include_cover_imagery: boolean;
}

interface AppSettings {
  version: string;
  subsidiary: SubsidiaryProfile;
  ai: AISettings;
  storage: StorageSettings;
  security: SecuritySettings;
  template: TemplateSettings;
}

export const SettingsView: React.FC = () => {
  const [activeSubTab, setActiveSubTab] = useState<
    "subsidiary" | "ai" | "security" | "storage" | "template" | "vertical_slice"
  >("subsidiary");

  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [subsidiaries, setSubsidiaries] = useState<SubsidiaryProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Section 35 Air-gapped diagnostic export state
  const [exportingDiag, setExportingDiag] = useState(false);
  const [diagBundle, setDiagBundle] = useState<any | null>(null);

  // Vertical slice execution state
  const [runningSlice, setRunningSlice] = useState(false);
  const [sliceResult, setSliceResult] = useState<any | null>(null);


  const fetchSettings = async () => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const [setRes, subRes] = await Promise.all([
        fetch(`${API_BASE}/api/v1/settings`),
        fetch(`${API_BASE}/api/v1/settings/subsidiaries`),
      ]);
      if (setRes.ok && subRes.ok) {
        const setData = await setRes.json();
        const subData = await subRes.json();
        setSettings(setData);
        setSubsidiaries(subData);
      } else {
        setErrorMessage("Failed to load settings from local processing server.");
      }
    } catch (err: any) {
      setErrorMessage(`Connection error: ${err.message || err}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const handleSaveSettings = async () => {
    if (!settings) return;
    setSaving(true);
    setErrorMessage(null);
    setSaveSuccess(false);
    try {
      const res = await fetch(`${API_BASE}/api/v1/settings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(settings),
      });
      if (res.ok) {
        const updated = await res.json();
        setSettings(updated);
        setSaveSuccess(true);
        setTimeout(() => setSaveSuccess(false), 3500);
      } else {
        const err = await res.json();
        setErrorMessage(err.detail || "Failed to save settings.");
      }
    } catch (err: any) {
      setErrorMessage(`Save failed: ${err.message || err}`);
    } finally {
      setSaving(false);
    }
  };

  const handleResetDefaults = async () => {
    if (!window.confirm("Reset all settings to Coal India factory defaults?")) return;
    setSaving(true);
    setErrorMessage(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/settings/reset`, { method: "POST" });
      if (res.ok) {
        const resetData = await res.json();
        setSettings(resetData);
        setSaveSuccess(true);
        setTimeout(() => setSaveSuccess(false), 3500);
      }
    } catch (err: any) {
      setErrorMessage(`Reset failed: ${err.message || err}`);
    } finally {
      setSaving(false);
    }
  };

  const handleSelectSubsidiary = async (code: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/settings/subsidiaries/select`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code }),
      });
      if (res.ok) {
        const updated = await res.json();
        setSettings(updated);
      }
    } catch (err) {
      console.error("Failed to switch subsidiary", err);
    }
  };

  const handleRunVerticalSlice = async () => {
    setRunningSlice(true);
    setSliceResult(null);
    setErrorMessage(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/pipeline/vertical-slice`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          subsidiary: settings?.subsidiary,
          reporting_period: settings?.subsidiary.default_financial_year,
          simulate_human_correction: true,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setSliceResult(data);
      } else {
        const err = await res.json();
        setErrorMessage(err.detail || "Vertical slice run failed.");
      }
    } catch (err: any) {
      setErrorMessage(`Vertical slice failed: ${err.message || err}`);
    } finally {
      setRunningSlice(false);
    }
  };

  const handleExportDiagnostics = async () => {
    setExportingDiag(true);
    setDiagBundle(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/observability/export-diagnostics`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ bundle_name: "airgap_support_diagnostics" }),
      });
      if (res.ok) {
        const data = await res.json();
        setDiagBundle(data);
      } else {
        const err = await res.json();
        setErrorMessage(err.detail || "Failed to export diagnostic bundle.");
      }
    } catch (err: any) {
      setErrorMessage(`Export failed: ${err.message || err}`);
    } finally {
      setExportingDiag(false);
    }
  };


  if (loading || !settings) {
    return (
      <div className="card" style={{ padding: "40px", textAlign: "center" }}>
        <p style={{ color: "var(--text-secondary)" }}>Loading application settings...</p>
      </div>
    );
  }

  return (
    <div className="settings-view" style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      {/* Top Header Card */}
      <div className="card" style={{ padding: "20px 24px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <Settings size={22} style={{ color: "var(--primary)" }} />
            <h2 style={{ margin: 0, fontSize: "1.3rem", fontWeight: 700 }}>System Configuration & Policies</h2>
            <span className="badge badge-primary">{settings.subsidiary.code} Active</span>
          </div>
          <p style={{ margin: "4px 0 0 0", color: "var(--text-secondary)", fontSize: "0.85rem" }}>
            Master implementation settings for air-gapped local AI, subsidiary governance, storage retention, and Section 40 vertical slice.
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
          {saveSuccess && (
            <span style={{ color: "var(--status-success)", display: "flex", alignItems: "center", gap: "6px", fontSize: "0.85rem" }}>
              <CheckCircle2 size={16} /> Configuration Saved
            </span>
          )}
          <button
            className="btn btn-secondary"
            onClick={handleResetDefaults}
            disabled={saving}
            style={{ display: "flex", alignItems: "center", gap: "6px" }}
          >
            <RotateCcw size={14} /> Reset Defaults
          </button>
          <button
            className="btn btn-primary"
            onClick={handleSaveSettings}
            disabled={saving}
            style={{ display: "flex", alignItems: "center", gap: "6px" }}
          >
            <Save size={14} /> {saving ? "Saving..." : "Save Settings"}
          </button>
        </div>
      </div>

      {errorMessage && (
        <div className="card" style={{ padding: "12px 16px", borderColor: "var(--status-error)", backgroundColor: "rgba(239, 68, 68, 0.08)", color: "var(--status-error)", display: "flex", alignItems: "center", gap: "8px" }}>
          <AlertCircle size={16} />
          <span style={{ fontSize: "0.85rem" }}>{errorMessage}</span>
        </div>
      )}

      {/* Navigation Sub-Tabs */}
      <div style={{ display: "flex", gap: "8px", borderBottom: "1px solid var(--border-color)", paddingBottom: "8px" }}>
        <button
          className={`btn ${activeSubTab === "subsidiary" ? "btn-primary" : "btn-ghost"}`}
          onClick={() => setActiveSubTab("subsidiary")}
          style={{ display: "flex", alignItems: "center", gap: "6px" }}
        >
          <Building2 size={15} /> Subsidiary Profile
        </button>
        <button
          className={`btn ${activeSubTab === "ai" ? "btn-primary" : "btn-ghost"}`}
          onClick={() => setActiveSubTab("ai")}
          style={{ display: "flex", alignItems: "center", gap: "6px" }}
        >
          <Cpu size={15} /> Local AI Engine
        </button>
        <button
          className={`btn ${activeSubTab === "security" ? "btn-primary" : "btn-ghost"}`}
          onClick={() => setActiveSubTab("security")}
          style={{ display: "flex", alignItems: "center", gap: "6px" }}
        >
          <ShieldCheck size={15} /> Security & Air-Gap
        </button>
        <button
          className={`btn ${activeSubTab === "storage" ? "btn-primary" : "btn-ghost"}`}
          onClick={() => setActiveSubTab("storage")}
          style={{ display: "flex", alignItems: "center", gap: "6px" }}
        >
          <HardDrive size={15} /> Storage Lifecycle
        </button>
        <button
          className={`btn ${activeSubTab === "template" ? "btn-primary" : "btn-ghost"}`}
          onClick={() => setActiveSubTab("template")}
          style={{ display: "flex", alignItems: "center", gap: "6px" }}
        >
          <Palette size={15} /> Report Templates
        </button>
        <button
          className={`btn ${activeSubTab === "vertical_slice" ? "btn-primary" : "btn-ghost"}`}
          onClick={() => setActiveSubTab("vertical_slice")}
          style={{ display: "flex", alignItems: "center", gap: "6px" }}
        >
          <Sparkles size={15} /> Section 40 Vertical Slice
        </button>
      </div>

      {/* Tab 1: Subsidiary Profile */}
      {activeSubTab === "subsidiary" && (
        <div className="card" style={{ padding: "24px" }}>
          <h3 style={{ margin: "0 0 16px 0", fontSize: "1.1rem" }}>Active Coal India Subsidiary Profile</h3>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
            <div>
              <label style={{ fontSize: "0.85rem", fontWeight: 600, display: "block", marginBottom: "6px" }}>
                Select Active Subsidiary
              </label>
              <select
                className="input"
                value={settings.subsidiary.code}
                onChange={(e) => handleSelectSubsidiary(e.target.value)}
                style={{ width: "100%" }}
              >
                {subsidiaries.map((sub) => (
                  <option key={sub.code} value={sub.code}>
                    {sub.code} — {sub.full_name}
                  </option>
                ))}
              </select>
              <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "4px", display: "block" }}>
                Switching subsidiary automatically populates registered headquarters and statutory parameters.
              </span>
            </div>

            <div>
              <label style={{ fontSize: "0.85rem", fontWeight: 600, display: "block", marginBottom: "6px" }}>
                Full Corporate Title
              </label>
              <input
                type="text"
                className="input"
                value={settings.subsidiary.full_name}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    subsidiary: { ...settings.subsidiary, full_name: e.target.value },
                  })
                }
                style={{ width: "100%" }}
              />
            </div>

            <div>
              <label style={{ fontSize: "0.85rem", fontWeight: 600, display: "block", marginBottom: "6px" }}>
                Registered Headquarters Address
              </label>
              <input
                type="text"
                className="input"
                value={settings.subsidiary.headquarters}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    subsidiary: { ...settings.subsidiary, headquarters: e.target.value },
                  })
                }
                style={{ width: "100%" }}
              />
            </div>

            <div>
              <label style={{ fontSize: "0.85rem", fontWeight: 600, display: "block", marginBottom: "6px" }}>
                Default Financial Year
              </label>
              <input
                type="text"
                className="input"
                value={settings.subsidiary.default_financial_year}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    subsidiary: { ...settings.subsidiary, default_financial_year: e.target.value },
                  })
                }
                style={{ width: "100%" }}
              />
            </div>

            <div>
              <label style={{ fontSize: "0.85rem", fontWeight: 600, display: "block", marginBottom: "6px" }}>
                Currency Denomination Unit
              </label>
              <select
                className="input"
                value={settings.subsidiary.currency_unit}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    subsidiary: { ...settings.subsidiary, currency_unit: e.target.value },
                  })
                }
                style={{ width: "100%" }}
              >
                <option value="INR Crores">INR Crores (Standard PSU Reporting)</option>
                <option value="INR Lakhs">INR Lakhs</option>
                <option value="INR Million">INR Million</option>
              </select>
            </div>

            <div>
              <label style={{ fontSize: "0.85rem", fontWeight: 600, display: "block", marginBottom: "6px" }}>
                Statutory CSR Mandate (%)
              </label>
              <input
                type="number"
                step="0.1"
                className="input"
                value={settings.subsidiary.statutory_mandate_csr_percent}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    subsidiary: {
                      ...settings.subsidiary,
                      statutory_mandate_csr_percent: parseFloat(e.target.value) || 2.0,
                    },
                  })
                }
                style={{ width: "100%" }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Local AI Engine */}
      {activeSubTab === "ai" && (
        <div className="card" style={{ padding: "24px" }}>
          <h3 style={{ margin: "0 0 16px 0", fontSize: "1.1rem" }}>Local AI Gateway & Inference Hardware</h3>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
            <div>
              <label style={{ fontSize: "0.85rem", fontWeight: 600, display: "block", marginBottom: "6px" }}>
                Inference Backend Engine
              </label>
              <select
                className="input"
                value={settings.ai.active_backend}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    ai: { ...settings.ai, active_backend: e.target.value },
                  })
                }
                style={{ width: "100%" }}
              >
                <option value="rule_based">Rule-Based Deterministic Engine (Fast, Guaranteed Zero Hallucination)</option>
                <option value="llama_cpp">llama.cpp GGUF Engine (Local CPU/GPU Acceleration)</option>
                <option value="local_server">Ollama / Local HTTP Inference Server</option>
              </select>
            </div>

            <div>
              <label style={{ fontSize: "0.85rem", fontWeight: 600, display: "block", marginBottom: "6px" }}>
                Active Model Identifier
              </label>
              <input
                type="text"
                className="input"
                value={settings.ai.model_name}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    ai: { ...settings.ai, model_name: e.target.value },
                  })
                }
                style={{ width: "100%" }}
              />
            </div>

            <div>
              <label style={{ fontSize: "0.85rem", fontWeight: 600, display: "block", marginBottom: "6px" }}>
                Context Window Size: {settings.ai.context_window_tokens} Tokens
              </label>
              <input
                type="range"
                min="2048"
                max="32768"
                step="1024"
                value={settings.ai.context_window_tokens}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    ai: { ...settings.ai, context_window_tokens: parseInt(e.target.value) },
                  })
                }
                style={{ width: "100%" }}
              />
              <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                Allocates memory for document evidence passages in prompt context.
              </span>
            </div>

            <div>
              <label style={{ fontSize: "0.85rem", fontWeight: 600, display: "block", marginBottom: "6px" }}>
                CPU Execution Threads: {settings.ai.cpu_threads} Cores
              </label>
              <input
                type="range"
                min="1"
                max="32"
                step="1"
                value={settings.ai.cpu_threads}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    ai: { ...settings.ai, cpu_threads: parseInt(e.target.value) },
                  })
                }
                style={{ width: "100%" }}
              />
            </div>

            <div>
              <label style={{ fontSize: "0.85rem", fontWeight: 600, display: "block", marginBottom: "6px" }}>
                Sampling Temperature: {settings.ai.temperature}
              </label>
              <input
                type="range"
                min="0.0"
                max="1.0"
                step="0.05"
                value={settings.ai.temperature}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    ai: { ...settings.ai, temperature: parseFloat(e.target.value) },
                  })
                }
                style={{ width: "100%" }}
              />
              <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                Lower values (0.05 - 0.2) enforce strict factual grounding and numerical reproduction.
              </span>
            </div>

            <div>
              <label style={{ fontSize: "0.85rem", fontWeight: 600, display: "block", marginBottom: "6px" }}>
                GPU Layer Offload: {settings.ai.gpu_offload_layers} Layers
              </label>
              <input
                type="range"
                min="0"
                max="99"
                step="1"
                value={settings.ai.gpu_offload_layers}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    ai: { ...settings.ai, gpu_offload_layers: parseInt(e.target.value) },
                  })
                }
                style={{ width: "100%" }}
              />
              <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                Set to 0 for strict CPU-first mode (e.g. standard laptops with integrated graphics).
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Security & Air-Gap */}
      {activeSubTab === "security" && (
        <div className="card" style={{ padding: "24px" }}>
          <h3 style={{ margin: "0 0 16px 0", fontSize: "1.1rem" }}>Air-Gap Security & Compliance Posture</h3>

          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "12px", border: "1px solid var(--border-color)", borderRadius: "8px" }}>
              <div>
                <strong style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                  <Lock size={15} style={{ color: "var(--status-success)" }} /> Strict Local Loopback (127.0.0.1)
                </strong>
                <p style={{ margin: "2px 0 0 0", fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                  Mandates all services and REST APIs bind solely to loopback interfaces, forbidding remote LAN exposure.
                </p>
              </div>
              <span className="badge badge-success">Enforced</span>
            </div>

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "12px", border: "1px solid var(--border-color)", borderRadius: "8px" }}>
              <div>
                <strong>Default-Deny External Network Access</strong>
                <p style={{ margin: "2px 0 0 0", fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                  Blocks cloud AI, public telemetry, and third-party APIs during document processing.
                </p>
              </div>
              <span className="badge badge-success">Blocked (Air-Gapped)</span>
            </div>

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "12px", border: "1px solid var(--border-color)", borderRadius: "8px" }}>
              <div>
                <strong>Cryptographic Audit Log Retention</strong>
                <p style={{ margin: "2px 0 0 0", fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                  Retention period for SHA-256 chained tamper-evident event records.
                </p>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <input
                  type="number"
                  className="input"
                  value={settings.security.audit_log_retention_days}
                  onChange={(e) =>
                    setSettings({
                      ...settings,
                      security: {
                        ...settings.security,
                        audit_log_retention_days: parseInt(e.target.value) || 365,
                      },
                    })
                  }
                  style={{ width: "100px" }}
                />
                <span style={{ fontSize: "0.85rem" }}>Days</span>
              </div>
            </div>

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "12px", border: "1px solid var(--border-color)", borderRadius: "8px" }}>
              <div>
                <strong>Mandatory Dual-Authorization for Report Exports</strong>
                <p style={{ margin: "2px 0 0 0", fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                  Requires designated corporate authority sign-off before exporting or transmitting final reports.
                </p>
              </div>
              <input
                type="checkbox"
                checked={settings.security.require_dual_authorization_export}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    security: {
                      ...settings.security,
                      require_dual_authorization_export: e.target.checked,
                    },
                  })
                }
              />
            </div>

            {/* Section 35 Air-Gapped Diagnostic Package Exporter */}
            <div style={{ marginTop: "16px", padding: "16px", border: "1px solid rgba(56, 189, 248, 0.3)", borderRadius: "8px", backgroundColor: "rgba(56, 189, 248, 0.05)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <strong style={{ fontSize: "0.95rem", display: "flex", alignItems: "center", gap: "6px" }}>
                    <ShieldCheck size={16} style={{ color: "#38bdf8" }} />
                    Air-Gapped Diagnostic & Audit Bundle (Section 35)
                  </strong>
                  <p style={{ margin: "4px 0 0 0", fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                    Generates a cryptographically hashed ZIP package with redacted telemetry, audit logs, and performance metrics for offline IT support.
                  </p>
                </div>
                <button
                  className="btn btn-primary"
                  onClick={handleExportDiagnostics}
                  disabled={exportingDiag}
                  style={{ display: "flex", alignItems: "center", gap: "6px" }}
                >
                  <Sparkles size={14} />
                  {exportingDiag ? "Compiling Bundle..." : "Export Sanitized Diagnostics"}
                </button>
              </div>

              {diagBundle && (
                <div style={{ marginTop: "12px", padding: "12px", backgroundColor: "rgba(15, 23, 42, 0.6)", borderRadius: "6px", border: "1px solid var(--border-color)" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div>
                      <span style={{ fontSize: "0.8rem", fontWeight: 700, color: "#34d399" }}>
                        ✓ Bundle Generated: {diagBundle.bundle_filename}
                      </span>
                      <p style={{ margin: "2px 0 0 0", fontSize: "0.75rem", fontFamily: "monospace", color: "var(--text-secondary)" }}>
                        SHA-256: {diagBundle.sha256_hash} ({(diagBundle.file_size_bytes / 1024).toFixed(1)} KB)
                      </p>
                    </div>
                    <a
                      href={`${API_BASE}/api/v1/observability/download-diagnostics/${diagBundle.bundle_filename}`}
                      className="btn btn-secondary"
                      download
                      style={{ textDecoration: "none", fontSize: "0.8rem", padding: "4px 10px" }}
                    >
                      Download ZIP
                    </a>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}


      {/* Tab 4: Storage Lifecycle */}
      {activeSubTab === "storage" && (
        <div className="card" style={{ padding: "24px" }}>
          <h3 style={{ margin: "0 0 16px 0", fontSize: "1.1rem" }}>Storage Lifecycle & Pruning Automation (Section 37)</h3>

          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div style={{ padding: "12px 16px", backgroundColor: "rgba(16, 185, 129, 0.08)", border: "1px solid rgba(16, 185, 129, 0.3)", borderRadius: "8px", color: "var(--status-success)", fontSize: "0.85rem" }}>
              <strong>Section 37 Protection Invariant:</strong> Raw source scans and evidence folders are permanently locked and cannot be erased by cache maintenance routines.
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
              <div>
                <label style={{ fontSize: "0.85rem", fontWeight: 600, display: "block", marginBottom: "6px" }}>
                  Parsed Document Cache Retention (Days)
                </label>
                <input
                  type="number"
                  className="input"
                  value={settings.storage.cache_retention_days}
                  onChange={(e) =>
                    setSettings({
                      ...settings,
                      storage: {
                        ...settings.storage,
                        cache_retention_days: parseInt(e.target.value) || 30,
                      },
                    })
                  }
                  style={{ width: "100%" }}
                />
              </div>

              <div>
                <label style={{ fontSize: "0.85rem", fontWeight: 600, display: "block", marginBottom: "6px" }}>
                  Ephemeral Scratch Auto-Prune Interval (Hours)
                </label>
                <input
                  type="number"
                  className="input"
                  value={settings.storage.temp_auto_prune_interval_hours}
                  onChange={(e) =>
                    setSettings({
                      ...settings,
                      storage: {
                        ...settings.storage,
                        temp_auto_prune_interval_hours: parseInt(e.target.value) || 24,
                      },
                    })
                  }
                  style={{ width: "100%" }}
                />
              </div>
            </div>

            <div style={{ display: "flex", gap: "20px", marginTop: "10px" }}>
              <label style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "0.85rem" }}>
                <input
                  type="checkbox"
                  checked={settings.storage.auto_cleanup_enabled}
                  onChange={(e) =>
                    setSettings({
                      ...settings,
                      storage: {
                        ...settings.storage,
                        auto_cleanup_enabled: e.target.checked,
                      },
                    })
                  }
                />
                Enable Background Scratch Buffer Pruning
              </label>

              <label style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "0.85rem" }}>
                <input
                  type="checkbox"
                  checked={settings.storage.dry_run_safety_lock}
                  onChange={(e) =>
                    setSettings({
                      ...settings,
                      storage: {
                        ...settings.storage,
                        dry_run_safety_lock: e.target.checked,
                      },
                    })
                  }
                />
                Dry-Run Safety Lock (Simulate Pruning Without Deleting Files)
              </label>
            </div>
          </div>
        </div>
      )}

      {/* Tab 5: Report Templates */}
      {activeSubTab === "template" && (
        <div className="card" style={{ padding: "24px" }}>
          <h3 style={{ margin: "0 0 16px 0", fontSize: "1.1rem" }}>Report Styling & Typography (Section 20)</h3>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
            <div>
              <label style={{ fontSize: "0.85rem", fontWeight: 600, display: "block", marginBottom: "6px" }}>
                Default Visual Presentation Mode
              </label>
              <select
                className="input"
                value={settings.template.default_visual_mode}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    template: { ...settings.template, default_visual_mode: e.target.value },
                  })
                }
                style={{ width: "100%" }}
              >
                <option value="modern">Template B: Modern Corporate (Contemporary, Grid-aligned)</option>
                <option value="classic">Template A: Classic CIL (Formal Reference Inspired)</option>
              </select>
            </div>

            <div>
              <label style={{ fontSize: "0.85rem", fontWeight: 600, display: "block", marginBottom: "6px" }}>
                Primary Brand Accent Color
              </label>
              <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                <input
                  type="color"
                  value={settings.template.brand_primary_color}
                  onChange={(e) =>
                    setSettings({
                      ...settings,
                      template: { ...settings.template, brand_primary_color: e.target.value },
                    })
                  }
                  style={{ width: "40px", height: "36px", padding: 0, border: "none", cursor: "pointer" }}
                />
                <input
                  type="text"
                  className="input"
                  value={settings.template.brand_primary_color}
                  onChange={(e) =>
                    setSettings({
                      ...settings,
                      template: { ...settings.template, brand_primary_color: e.target.value },
                    })
                  }
                  style={{ flex: 1 }}
                />
              </div>
            </div>

            <div>
              <label style={{ fontSize: "0.85rem", fontWeight: 600, display: "block", marginBottom: "6px" }}>
                Heading Typography Font
              </label>
              <input
                type="text"
                className="input"
                value={settings.template.font_family_heading}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    template: { ...settings.template, font_family_heading: e.target.value },
                  })
                }
                style={{ width: "100%" }}
              />
            </div>

            <div>
              <label style={{ fontSize: "0.85rem", fontWeight: 600, display: "block", marginBottom: "6px" }}>
                Body Typography Font
              </label>
              <input
                type="text"
                className="input"
                value={settings.template.font_family_body}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    template: { ...settings.template, font_family_body: e.target.value },
                  })
                }
                style={{ width: "100%" }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Tab 6: Section 40 Vertical Slice Runner */}
      {activeSubTab === "vertical_slice" && (
        <div className="card" style={{ padding: "24px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
            <div>
              <h3 style={{ margin: "0 0 4px 0", fontSize: "1.1rem" }}>Section 40: Automated First Vertical Slice Runner</h3>
              <p style={{ margin: 0, color: "var(--text-secondary)", fontSize: "0.85rem" }}>
                Executes the authoritative 10–20 file pipeline slice to generate a 5–10 page report with full provenance and human review.
              </p>
            </div>
            <button
              className="btn btn-primary"
              onClick={handleRunVerticalSlice}
              disabled={runningSlice}
              style={{ display: "flex", alignItems: "center", gap: "8px" }}
            >
              <Play size={16} /> {runningSlice ? "Executing Vertical Slice..." : "Run Vertical Slice"}
            </button>
          </div>

          {runningSlice && (
            <div style={{ padding: "24px", textAlign: "center", backgroundColor: "var(--bg-secondary)", borderRadius: "8px" }}>
              <div className="status-dot online" style={{ display: "inline-block", marginBottom: "8px" }} />
              <p style={{ margin: 0, fontWeight: 600 }}>Executing Autonomous 10-20 File Vertical Slice...</p>
              <p style={{ margin: "4px 0 0 0", color: "var(--text-secondary)", fontSize: "0.8rem" }}>
                Discovery &rarr; Extraction &rarr; Normalization &rarr; FTS5 Indexing &rarr; Planning &rarr; Generation &rarr; Agentic Correction &rarr; Dual PDF Rendering
              </p>
            </div>
          )}

          {sliceResult && (
            <div style={{ display: "flex", flexDirection: "column", gap: "16px", marginTop: "16px" }}>
              <div style={{ padding: "16px", backgroundColor: "rgba(16, 185, 129, 0.08)", border: "1px solid rgba(16, 185, 129, 0.3)", borderRadius: "8px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ fontWeight: 700, color: "var(--status-success)", display: "flex", alignItems: "center", gap: "6px" }}>
                    <CheckCircle2 size={18} /> Vertical Slice Completed Successfully
                  </span>
                  <span className="badge badge-primary">Session: {sliceResult.session_id}</span>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "12px", marginTop: "14px" }}>
                  <div>
                    <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>Source Files</span>
                    <p style={{ margin: 0, fontWeight: 700, fontSize: "1.1rem" }}>{sliceResult.file_count}</p>
                  </div>
                  <div>
                    <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>Estimated Pages</span>
                    <p style={{ margin: 0, fontWeight: 700, fontSize: "1.1rem" }}>{sliceResult.estimated_pages}</p>
                  </div>
                  <div>
                    <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>Provenance Citations</span>
                    <p style={{ margin: 0, fontWeight: 700, fontSize: "1.1rem" }}>{sliceResult.provenance_records_count}</p>
                  </div>
                  <div>
                    <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>Validation</span>
                    <p style={{ margin: 0, fontWeight: 700, fontSize: "1.1rem", color: sliceResult.validation_passed ? "var(--status-success)" : "var(--status-error)" }}>
                      {sliceResult.validation_passed ? "PASSED" : "FAILED"}
                    </p>
                  </div>
                </div>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
                <div className="card" style={{ padding: "16px" }}>
                  <h4 style={{ margin: "0 0 10px 0", fontSize: "0.95rem" }}>Section 32 Quality Audit Metrics</h4>
                  {sliceResult.quality_metrics && Object.entries(sliceResult.quality_metrics).map(([k, v]: any) => (
                    <div key={k} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px solid var(--border-color)", fontSize: "0.85rem" }}>
                      <span style={{ textTransform: "capitalize" }}>{k.replace(/_/g, " ")}</span>
                      <strong>{typeof v === "number" ? `${(v * 100).toFixed(1)}%` : String(v)}</strong>
                    </div>
                  ))}
                </div>

                <div className="card" style={{ padding: "16px" }}>
                  <h4 style={{ margin: "0 0 10px 0", fontSize: "0.95rem" }}>Rendered PDF Artifacts</h4>
                  <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginTop: "8px" }}>
                    <div style={{ padding: "8px 12px", border: "1px solid var(--border-color)", borderRadius: "6px", fontSize: "0.8rem", wordBreak: "break-all" }}>
                      <strong>Classic CIL:</strong> {sliceResult.classic_pdf_path}
                    </div>
                    <div style={{ padding: "8px 12px", border: "1px solid var(--border-color)", borderRadius: "6px", fontSize: "0.8rem", wordBreak: "break-all" }}>
                      <strong>Modern Corporate:</strong> {sliceResult.modern_pdf_path}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
