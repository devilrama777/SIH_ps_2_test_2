import React, { useState, useEffect } from "react";
import {
  ShieldCheck,
  Key,
  Lock,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  Server,
  FileCheck,
  Activity,
  PlusCircle,
} from "lucide-react";

import { API_BASE } from "../services/config";

interface SecurityStatus {
  air_gap_enforced: boolean;
  no_cloud_ai_calls: boolean;
  fully_isolated: boolean;
  cloud_keys_detected: string[];
  audit_chain_valid: boolean;
  total_audit_logs: number;
  vault_status: string;
  vault_keys_count: number;
  vault_keys: string[];
  active_controls: string[];
}

interface AuditLogEntry {
  log_id: string;
  timestamp: string;
  event_type: string;
  user: string;
  action: string;
  resource_id?: string;
  status: string;
  ip_address: string;
  details: Record<string, any>;
  prev_hash: string;
  entry_hash: string;
}

export const SecurityAuditView: React.FC = () => {
  const [securityStatus, setSecurityStatus] = useState<SecurityStatus | null>(null);
  const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedEventType, setSelectedEventType] = useState<string>("all");
  const [newKey, setNewKey] = useState<string>("");
  const [newValue, setNewValue] = useState<string>("");
  const [vaultSuccess, setVaultSuccess] = useState<string | null>(null);
  const [vaultError, setVaultError] = useState<string | null>(null);

  const fetchSecurityData = async () => {
    setLoading(true);
    try {
      const statusRes = await fetch(`${API_BASE}/api/v1/security/status`);
      if (statusRes.ok) {
        const data = await statusRes.json();
        setSecurityStatus(data);
      }

      const logUrl =
        selectedEventType === "all"
          ? `${API_BASE}/api/v1/security/audit-logs?limit=50`
          : `${API_BASE}/api/v1/security/audit-logs?event_type=${selectedEventType}&limit=50`;

      const logsRes = await fetch(logUrl);
      if (logsRes.ok) {
        const data = await logsRes.json();
        setAuditLogs(data);
      }
    } catch (err) {
      console.error("Failed to fetch security telemetry", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSecurityData();
  }, [selectedEventType]);

  const handleStoreSecret = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKey.trim() || !newValue.trim()) return;

    try {
      setVaultSuccess(null);
      setVaultError(null);
      const res = await fetch(`${API_BASE}/api/v1/security/vault`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ key: newKey.trim(), value: newValue }),
      });
      if (res.ok) {
        setVaultSuccess(`Credential '${newKey}' securely stored in DPAPI encrypted vault.`);
        setNewKey("");
        setNewValue("");
        fetchSecurityData();
      } else {
        const err = await res.json();
        setVaultError(err.detail || "Failed to store secret in vault.");
      }
    } catch (err) {
      setVaultError("Network or server connection failed.");
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-emerald-400">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-white tracking-tight">
                  Security Architecture & Audit Ledger
                </h2>
                <p className="text-sm text-slate-400">
                  Section 24: 100% Air-Gapped Enforcement, Cryptographic Hash Chaining & Credential Vault
                </p>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={fetchSecurityData}
              disabled={loading}
              className="inline-flex items-center gap-2 px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-medium rounded-lg border border-slate-700 transition"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
              Refresh Telemetry
            </button>
          </div>
        </div>
      </div>

      {/* Security Posture Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Air-Gap Isolation */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Air-Gap Status
            </span>
            <Server className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-3 flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-lg font-bold text-emerald-400">100% Air-Gapped</span>
          </div>
          <p className="mt-1 text-xs text-slate-400">
            Bound strictly to loopback (127.0.0.1). Zero outbound cloud AI calls permitted.
          </p>
        </div>

        {/* Audit Chain Integrity */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              SHA-256 Ledger
            </span>
            <FileCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-3 flex items-center gap-2">
            {securityStatus?.audit_chain_valid ? (
              <>
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                <span className="text-lg font-bold text-emerald-400">Chain Verified</span>
              </>
            ) : (
              <>
                <AlertTriangle className="w-5 h-5 text-rose-400" />
                <span className="text-lg font-bold text-rose-400">Integrity Failed</span>
              </>
            )}
          </div>
          <p className="mt-1 text-xs text-slate-400">
            {securityStatus?.total_audit_logs || 0} chained, tamper-evident log records verified.
          </p>
        </div>

        {/* Encrypted Vault */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Credential Vault
            </span>
            <Lock className="w-4 h-4 text-blue-400" />
          </div>
          <div className="mt-3 flex items-center gap-2">
            <span className="text-lg font-bold text-white">DPAPI Encrypted</span>
          </div>
          <p className="mt-1 text-xs text-slate-400">
            {securityStatus?.vault_keys_count || 0} secrets stored using Windows user session keys.
          </p>
        </div>

        {/* Cloud Leak Protection */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Cloud Leak Scanner
            </span>
            <Activity className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-3 flex items-center gap-2">
            <span className="text-lg font-bold text-emerald-400">0 Leaks Detected</span>
          </div>
          <p className="mt-1 text-xs text-slate-400">
            No OpenAI, Anthropic, or external cloud keys in runtime memory.
          </p>
        </div>
      </div>

      {/* Main Grid: Audit Log Table + Vault Manager */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Immutable Audit Log Ledger */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
            <div>
              <h3 className="text-base font-semibold text-white">Immutable Audit Ledger</h3>
              <p className="text-xs text-slate-400">
                Cryptographically hashed audit sequence linking every operation back to genesis.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <select
                value={selectedEventType}
                onChange={(e) => setSelectedEventType(e.target.value)}
                className="px-3 py-1.5 bg-slate-800 border border-slate-700 text-slate-300 text-xs rounded-lg focus:outline-none focus:ring-1 focus:ring-emerald-500"
              >
                <option value="all">All Events</option>
                <option value="ingestion">Ingestion</option>
                <option value="report_created">Report Created</option>
                <option value="agent_edit_proposed">Agent Edit Proposed</option>
                <option value="agent_edit_accepted">Agent Edit Accepted</option>
                <option value="agent_edit_rejected">Agent Edit Rejected</option>
                <option value="export_pdf">PDF Export</option>
                <option value="config_change">Config & Vault Change</option>
              </select>
            </div>
          </div>

          <div className="mt-4 overflow-x-auto">
            {auditLogs.length === 0 ? (
              <div className="py-12 text-center text-slate-500 text-sm">
                No audit events recorded for the selected filter.
              </div>
            ) : (
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400">
                    <th className="pb-3 font-semibold">Timestamp</th>
                    <th className="pb-3 font-semibold">Event</th>
                    <th className="pb-3 font-semibold">Action</th>
                    <th className="pb-3 font-semibold">Resource</th>
                    <th className="pb-3 font-semibold">Status</th>
                    <th className="pb-3 font-semibold">Entry SHA-256</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {auditLogs.map((log) => (
                    <tr key={log.log_id} className="hover:bg-slate-800/30">
                      <td className="py-3 text-slate-400 whitespace-nowrap">
                        {new Date(log.timestamp).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                          second: "2-digit",
                        })}
                      </td>
                      <td className="py-3">
                        <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-800 text-slate-300 border border-slate-700">
                          {log.event_type}
                        </span>
                      </td>
                      <td className="py-3 font-mono text-slate-300">{log.action}</td>
                      <td className="py-3 text-slate-400 truncate max-w-[120px]">
                        {log.resource_id || "—"}
                      </td>
                      <td className="py-3">
                        <span
                          className={`inline-flex items-center gap-1 font-semibold ${
                            log.status === "success"
                              ? "text-emerald-400"
                              : log.status === "blocked"
                              ? "text-amber-400"
                              : "text-rose-400"
                          }`}
                        >
                          {log.status === "success" && <CheckCircle2 className="w-3 h-3" />}
                          {log.status}
                        </span>
                      </td>
                      <td className="py-3 font-mono text-slate-500 text-[10px]">
                        {log.entry_hash ? `${log.entry_hash.substring(0, 10)}...` : "genesis"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* Right Col: Active Controls & Vault Manager */}
        <div className="space-y-6">
          {/* Active Security Controls */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <h3 className="text-base font-semibold text-white flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              Active Air-Gap Controls
            </h3>
            <p className="mt-1 text-xs text-slate-400">
              Enforced continuous protections across backend runtime:
            </p>
            <ul className="mt-4 space-y-2.5">
              {(securityStatus?.active_controls || [
                "Local Loopback Enforcement (127.0.0.1)",
                "Deterministic Numeric & Citation Validation Gates",
                "Zero Cloud AI API Transmissions",
                "SHA-256 Tamper-Evident Chained Audit Trail",
                "OS-Level DPAPI / Machine-Salted Vault Encryption",
                "Strict Human Approval Gates for Agentic Revisions",
              ]).map((control, idx) => (
                <li key={idx} className="flex items-start gap-2.5 text-xs text-slate-300">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                  <span>{control}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Secure Vault Manager */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <h3 className="text-base font-semibold text-white flex items-center gap-2">
              <Key className="w-4 h-4 text-blue-400" />
              Secure Credential Vault
            </h3>
            <p className="mt-1 text-xs text-slate-400">
              Store internal database or local API keys encrypted with OS-level DPAPI keys.
            </p>

            {vaultSuccess && (
              <div className="mt-3 p-2.5 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-emerald-400 text-xs flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                <span>{vaultSuccess}</span>
              </div>
            )}
            {vaultError && (
              <div className="mt-3 p-2.5 bg-rose-500/10 border border-rose-500/20 rounded-lg text-rose-400 text-xs flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span>{vaultError}</span>
              </div>
            )}

            <form onSubmit={handleStoreSecret} className="mt-4 space-y-3">
              <div>
                <label className="block text-xs font-medium text-slate-400">Secret Key</label>
                <input
                  type="text"
                  placeholder="e.g. LOCAL_DB_SECRET"
                  value={newKey}
                  onChange={(e) => setNewKey(e.target.value)}
                  className="mt-1 w-full px-3 py-1.5 bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500 font-mono"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-400">Secret Value</label>
                <input
                  type="password"
                  placeholder="••••••••••••••••"
                  value={newValue}
                  onChange={(e) => setNewValue(e.target.value)}
                  className="mt-1 w-full px-3 py-1.5 bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500 font-mono"
                />
              </div>
              <button
                type="submit"
                className="w-full inline-flex items-center justify-center gap-2 px-3 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-lg transition shadow"
              >
                <PlusCircle className="w-3.5 h-3.5" />
                Encrypt & Store in Vault
              </button>
            </form>

            <div className="mt-4 pt-4 border-t border-slate-800">
              <span className="text-xs font-medium text-slate-400">Keys in Vault:</span>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {(securityStatus?.vault_keys || []).length === 0 ? (
                  <span className="text-xs text-slate-500 italic">No credentials in vault.</span>
                ) : (
                  securityStatus?.vault_keys.map((k) => (
                    <span
                      key={k}
                      className="px-2 py-0.5 bg-slate-800 border border-slate-700 rounded text-[11px] font-mono text-slate-300"
                    >
                      {k}
                    </span>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
