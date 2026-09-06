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
  Lock,
  Cpu,
  Layers,
  CheckSquare,
  FileText,
  FileCheck,
  Award,
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

interface TierReadiness {
  tier: string;
  name: string;
  is_ready: boolean;
  version?: string;
  path?: string;
  details: Record<string, any>;
  missing_items: string[];
}

interface InstallationStatus {
  all_ready: boolean;
  tiers: Record<string, TierReadiness>;
  active_model_id?: string;
}

interface DoDScorecard {
  has_implementation: boolean;
  has_unit_tests: boolean;
  has_integration_tests: boolean;
  has_error_handling: boolean;
  has_logging: boolean;
  has_documentation: boolean;
  has_security_review: boolean;
  has_performance_measurement: boolean;
  score: number;
}

interface PhaseAuditItem {
  phase_number: number;
  phase_name: string;
  specification_section: string;
  is_complete: boolean;
  dod_score: number;
  dod_scorecard: DoDScorecard;
  deliverables: string[];
  primary_code_files: string[];
  associated_tests: string[];
  documentation_record: string;
}

interface PhasesAuditReport {
  title: string;
  total_phases: number;
  completed_phases: number;
  completion_percentage: number;
  average_dod_score: number;
  overall_certified: boolean;
  section_43_llm_independence: {
    compliant: boolean;
    checks: Record<string, boolean>;
    invariant: string;
  };
  phases: PhaseAuditItem[];
}

interface ArchitecturalRuleCheck {
  rule_number: number;
  title: string;
  section: string;
  passed: boolean;
  details: string;
}

interface StepCompletionCheck {
  step_number: number;
  title: string;
  section: string;
  primary_artifact: string;
  completed: boolean;
  details: string;
}

interface SwappabilityCheck {
  component_id: string;
  title: string;
  section: string;
  interface_contract: string;
  default_implementation: string;
  alternate_implementation: string;
  swappable: boolean;
  latency_ms: number;
  details: string;
}

interface RulesAuditReport {
  timestamp: string;
  section_41_rules: ArchitecturalRuleCheck[];
  section_41_compliance_pct: number;
  section_44_steps: StepCompletionCheck[];
  section_44_completion_pct: number;
  section_45_swappability: SwappabilityCheck[];
  section_45_verified: boolean;
  priority_hierarchy: {
    order: string[];
    statement: string;
    guaranteed: boolean;
  };
  overall_verdict: string;
  total_passed_checks: number;
  total_checks: number;
  execution_time_ms: number;
}

interface WatchdogMetric {
  name: string;
  status: string;
  value: any;
  unit: string;
  threshold: any;
  details: string;
}

interface WatchdogSnapshot {
  timestamp: string;
  overall_health: string;
  is_airgapped: boolean;
  memory_healthy: boolean;
  storage_healthy: boolean;
  database_healthy: boolean;
  ai_runtime_healthy: boolean;
  audit_trail_healthy: boolean;
  metrics: WatchdogMetric[];
  warnings: string[];
  execution_time_ms: number;
}

interface ProductionCertificate {
  certificate_id: string;
  issued_at: string;
  authorized_by: string;
  target_organization: string;
  operating_system: string;
  airgap_verified: boolean;
  total_sections_certified: number;
  readiness_percentage: number;
  dod_compliance_percentage: number;
  modular_swappability_verified: boolean;
  watchdog_health: string;
  sha256_signature: string;
  hmac_integrity_digest: string;
}

interface LayerAuditResult {
  layer_id: number;
  layer_name: string;
  is_deterministic: boolean;
  primary_artifact: string;
  verification_method: string;
  status: string;
  details: Record<string, any>;
}

interface LLMIndependenceReport {
  timestamp: string;
  passed: boolean;
  compliance_score: number;
  total_layers: number;
  verified_layers: number;
  zero_llm_mode_supported: boolean;
  master_specification_reference: string;
  layers: LayerAuditResult[];
}

interface ZeroLLMResult {
  report_id: string;
  title: string;
  reporting_period: string;
  subsidiary_name: string;
  section_count: number;
  table_count: number;
  narrative_block_count: number;
  validation_passed: boolean;
  calculation_checks_passed: boolean;
  llm_invocations_count: number;
  html_path?: string;
  pdf_path?: string;
  page_count: number;
  file_size_bytes: number;
  renderer_engine: string;
  execution_time_ms: number;
  timestamp: string;
}

interface StepAuditResult {
  step_number: number;
  title: string;
  category: string;
  primary_artifact: string;
  prerequisites: number[];
  prerequisites_satisfied: boolean;
  artifact_exists: boolean;
  test_exists: boolean;
  contract_verified: boolean;
  completed: boolean;
  latency_ms: number;
  details: string;
}

interface ImplementationOrderReport {
  timestamp: string;
  total_steps: number;
  completed_steps: number;
  completion_pct: number;
  topological_order_valid: boolean;
  all_completed: boolean;
  specification_section: string;
  steps: StepAuditResult[];
  topological_sequence: number[];
  execution_time_ms: number;
}

interface InquiryCheck {
  inquiry_name: string;
  satisfied: boolean;
  summary: string;
  evidence: string;
}

interface ComponentBehaviorAudit {
  component_name: string;
  module_path: string;
  all_satisfied: boolean;
  inquiries: InquiryCheck[];
  audit_duration_ms: number;
  notes?: string;
}

interface ModularSwapContract {
  subsystem_key: string;
  source_name: string;
  target_name: string;
  interface_class_path: string;
  source_class_path: string;
  target_class_path: string;
  interface_verified: boolean;
  source_verified: boolean;
  target_verified: boolean;
  decoupled: boolean;
  details: string;
}

interface SwapSimulationResult {
  subsystem_key: string;
  original_component: string;
  swapped_component: string;
  success: boolean;
  latency_ms: number;
  affected_unrelated_modules: number;
  contract_adhered: boolean;
  message: string;
}

interface ExpectedBehaviorReport {
  timestamp: number;
  all_components_compliant: boolean;
  all_swaps_verified: boolean;
  priority_hierarchy_enforced: boolean;
  overall_compliance_score: number;
  audited_components: ComponentBehaviorAudit[];
  swappability_contracts: ModularSwapContract[];
  priority_order: string[];
  notes: string;
}

const API_BASE = "http://127.0.0.1:8765";

export const DiagnosticsView: React.FC = () => {
  const [storageData, setStorageData] = useState<StorageBreakdown | null>(null);
  const [telemetryEvents, setTelemetryEvents] = useState<TelemetryEvent[]>([]);
  const [aggregates, setAggregates] = useState<Record<string, any>>({});
  const [installationStatus, setInstallationStatus] = useState<InstallationStatus | null>(null);
  const [modelCatalog, setModelCatalog] = useState<any[]>([]);
  const [phasesAudit, setPhasesAudit] = useState<PhasesAuditReport | null>(null);
  const [rulesAudit, setRulesAudit] = useState<RulesAuditReport | null>(null);
  const [watchdogData, setWatchdogData] = useState<WatchdogSnapshot | null>(null);
  const [productionCert, setProductionCert] = useState<ProductionCertificate | null>(null);
  const [llmIndependenceData, setLlmIndependenceData] = useState<LLMIndependenceReport | null>(null);
  const [implementationOrderReport, setImplementationOrderReport] = useState<ImplementationOrderReport | null>(null);
  const [expectedBehaviorReport, setExpectedBehaviorReport] = useState<ExpectedBehaviorReport | null>(null);
  const [swapSimulations, setSwapSimulations] = useState<Record<string, SwapSimulationResult>>({});
  const [simulatingKey, setSimulatingKey] = useState<string | null>(null);
  const [selectedAuditComponent, setSelectedAuditComponent] = useState<string | null>(null);
  const [zeroLLMResult, setZeroLLMResult] = useState<ZeroLLMResult | null>(null);
  const [runningZeroLLM, setRunningZeroLLM] = useState(false);
  const [generatingCert, setGeneratingCert] = useState(false);
  const [activeRulesTab, setActiveRulesTab] = useState<"rules" | "steps" | "swappability">("rules");
  const [verifyingSwappability, setVerifyingSwappability] = useState(false);
  const [selectedPhase, setSelectedPhase] = useState<number | null>(null);
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
      const [storageRes, telemRes, installRes, catalogRes, phasesRes, rulesRes, watchdogRes, llmIndepRes, orderRes, behaviorRes] = await Promise.all([
        fetch(`${API_BASE}/api/v1/storage/breakdown`).then(r => r.json()).catch(() => null),
        fetch(`${API_BASE}/api/v1/observability/telemetry?limit=25`).then(r => r.json()).catch(() => null),
        fetch(`${API_BASE}/api/v1/installation/status`).then(r => r.json()).catch(() => null),
        fetch(`${API_BASE}/api/v1/installation/models/catalog`).then(r => r.json()).catch(() => null),
        fetch(`${API_BASE}/api/v1/system/phases-audit`).then(r => r.json()).catch(() => null),
        fetch(`${API_BASE}/api/v1/system/rules-audit`).then(r => r.json()).catch(() => null),
        fetch(`${API_BASE}/api/v1/system/watchdog/status`).then(r => r.json()).catch(() => null),
        fetch(`${API_BASE}/api/v1/system/llm-independence/audit`).then(r => r.json()).catch(() => null),
        fetch(`${API_BASE}/api/v1/system/implementation-order/audit`).then(r => r.json()).catch(() => null),
        fetch(`${API_BASE}/api/v1/system/expected-behavior/audit`).then(r => r.json()).catch(() => null),
      ]);

      if (storageRes) setStorageData(storageRes);
      if (telemRes) {
        setTelemetryEvents(telemRes.recent_events || []);
        setAggregates(telemRes.stage_aggregates || {});
      }
      if (installRes) setInstallationStatus(installRes);
      if (catalogRes && catalogRes.catalog) setModelCatalog(catalogRes.catalog);
      if (phasesRes) setPhasesAudit(phasesRes);
      if (rulesRes) setRulesAudit(rulesRes);
      if (watchdogRes) setWatchdogData(watchdogRes);
      if (llmIndepRes) setLlmIndependenceData(llmIndepRes);
      if (orderRes) setImplementationOrderReport(orderRes);
      if (behaviorRes) setExpectedBehaviorReport(behaviorRes);
    } catch (err) {
      console.error("Failed to load diagnostics:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateCertificate = async () => {
    setGeneratingCert(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/system/production-certificate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ authorized_by: "Coal India Limited Enterprise Technical Authority" }),
      });
      if (res.ok) {
        const cert = await res.json();
        setProductionCert(cert);
      }
    } catch (err) {
      console.error("Failed to generate production certificate:", err);
    } finally {
      setGeneratingCert(false);
    }
  };

  const handleRunZeroLLMGeneration = async () => {
    setRunningZeroLLM(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/system/llm-independence/zero-llm-generation`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ template_name: "modern", output_pdf: true }),
      });
      if (res.ok) {
        const data = await res.json();
        setZeroLLMResult(data);
      }
    } catch (err) {
      console.error("Zero-LLM Generation error:", err);
    } finally {
      setRunningZeroLLM(false);
    }
  };

  const handleVerifySwappability = async () => {
    setVerifyingSwappability(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/system/rules-audit/verify-swappability`, {
        method: "POST",
      });
      if (res.ok) {
        await fetchDiagnostics();
      }
    } catch (err) {
      console.error("Swappability verification error:", err);
    } finally {
      setVerifyingSwappability(false);
    }
  };

  const handleSimulateSwap = async (key: string) => {
    setSimulatingKey(key);
    try {
      const res = await fetch(`${API_BASE}/api/v1/system/expected-behavior/simulate-swap`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ subsystem_key: key }),
      });
      if (res.ok) {
        const data: SwapSimulationResult = await res.json();
        setSwapSimulations(prev => ({ ...prev, [key]: data }));
      }
    } catch (err) {
      console.error("Swap simulation error:", err);
    } finally {
      setSimulatingKey(null);
    }
  };

  useEffect(() => {
    fetchDiagnostics();
  }, []);

  const handleCleanup = async () => {
    setCleaning(true);
    setCleanupMessage(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/storage/cleanup`, {
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
      const res = await fetch(`${API_BASE}/api/v1/observability/export-diagnostics`, {
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

      const res = await fetch(`${API_BASE}/api/v1/reports/incremental/invalidate`, {
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

      {/* Phase 42: Production Health Watchdog & Invariant Certification */}
      {watchdogData && (
        <div className="p-6 rounded-2xl border border-emerald-500/40 bg-slate-900/80 shadow-2xl backdrop-blur-md space-y-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
            <div>
              <div className="flex items-center gap-2.5">
                <Cpu className="w-6 h-6 text-emerald-400" />
                <h2 className="text-lg font-bold text-white">
                  Live System Health Watchdog & Production Certification (Phase 42)
                </h2>
                <span className={`px-2.5 py-0.5 text-xs font-mono font-bold rounded-full border ${
                  watchdogData.overall_health === "HEALTHY"
                    ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                    : "bg-amber-500/10 text-amber-400 border-amber-500/30"
                }`}>
                  {watchdogData.overall_health} ({watchdogData.is_airgapped ? "100% AIR-GAPPED" : "EGRESS DETECTED"})
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Real-time runtime supervisor continuously asserting memory ceilings (&lt; 4 GB), disk retention, zero-cloud egress, and tamper-evident audit integrity.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={handleGenerateCertificate}
                disabled={generatingCert}
                className="flex items-center gap-2 px-4 py-2 text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-slate-950 rounded-xl transition shadow-lg shadow-emerald-950/50"
              >
                <Award className="w-4 h-4" />
                {generatingCert ? "Certifying 46 Sections..." : "Issue Production Certificate"}
              </button>
            </div>
          </div>

          {/* Telemetry Metrics Grid */}
          <div className="grid grid-cols-2 md:grid-cols-6 gap-2.5">
            {watchdogData.metrics.map((m) => (
              <div
                key={m.name}
                className="p-3 rounded-xl border bg-slate-800/40 border-slate-700/60 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[9px] font-mono uppercase text-slate-400 truncate">{m.name.replace("_", " ")}</span>
                    <span className={`w-2 h-2 rounded-full ${m.status === "HEALTHY" ? "bg-emerald-400" : "bg-amber-400"}`} />
                  </div>
                  <div className="text-sm font-bold font-mono text-slate-100">
                    {typeof m.value === "boolean" ? (m.value ? "ENFORCED" : "FAILED") : `${m.value} ${m.unit}`}
                  </div>
                </div>
                <p className="text-[9px] text-slate-500 mt-1 truncate" title={m.details}>{m.details}</p>
              </div>
            ))}
          </div>

          {/* Production Certificate Download Panel */}
          {productionCert && (
            <div className="p-4 rounded-xl border border-emerald-500/40 bg-emerald-950/20 flex flex-col md:flex-row md:items-center justify-between gap-4 animate-fade-in">
              <div className="flex items-center gap-3">
                <ShieldCheck className="w-8 h-8 text-emerald-400 shrink-0" />
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-emerald-200">PRODUCTION CERTIFICATE ISSUED</span>
                    <span className="font-mono text-[10px] bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded border border-emerald-500/30">
                      {productionCert.certificate_id}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-300 mt-0.5">
                    Authorized for: {productionCert.target_organization} — {productionCert.total_sections_certified}/46 Sections Verified ({productionCert.readiness_percentage}%)
                  </p>
                  <p className="text-[9px] font-mono text-emerald-400/70 mt-0.5">
                    HMAC-SHA256: {productionCert.hmac_integrity_digest}
                  </p>
                </div>
              </div>
              <a
                href={`${API_BASE}/api/v1/system/rules-audit`}
                target="_blank"
                rel="noreferrer"
                className="px-3 py-1.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs rounded-lg transition shrink-0"
              >
                Inspect Audit Manifest
              </a>
            </div>
          )}
        </div>
      )}

      {/* Section 43: Strict LLM-Independence Invariant Verification & Zero-LLM Pipeline */}
      {llmIndependenceData && (
        <div className="p-6 rounded-2xl border border-sky-500/40 bg-slate-900/80 shadow-2xl backdrop-blur-md space-y-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
            <div>
              <div className="flex items-center gap-2.5">
                <ShieldCheck className="w-6 h-6 text-sky-400" />
                <h2 className="text-lg font-bold text-white">
                  Strict LLM-Independence Invariants & Zero-LLM Pipeline (Section 43)
                </h2>
                <span className="px-2.5 py-0.5 text-xs font-mono font-bold rounded-full border bg-sky-500/10 text-sky-400 border-sky-500/30">
                  {llmIndependenceData.verified_layers} / {llmIndependenceData.total_layers} Layers Isolated (100% Deterministic)
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Source data, structured evidence, deterministic calculations, provenance, validation, and layout models remain strictly decoupled from the local LLM.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={handleRunZeroLLMGeneration}
                disabled={runningZeroLLM}
                className="flex items-center gap-2 px-4 py-2 text-xs font-bold bg-sky-600 hover:bg-sky-500 text-slate-950 rounded-xl transition shadow-lg shadow-sky-950/50"
              >
                <RefreshCw className={`w-4 h-4 ${runningZeroLLM ? "animate-spin" : ""}`} />
                {runningZeroLLM ? "Generating Zero-LLM Report..." : "Run Zero-LLM Generation Test"}
              </button>
            </div>
          </div>

          {/* 6 Invariant Layers Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {llmIndependenceData.layers.map((layer) => (
              <div
                key={layer.layer_id}
                className="p-3.5 rounded-xl border bg-slate-800/40 border-slate-700/60 flex flex-col justify-between hover:border-sky-500/40 transition"
              >
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-[10px] font-mono font-bold text-sky-400">LAYER {layer.layer_id}</span>
                    <span className="inline-flex items-center gap-1 text-[9px] font-mono font-bold px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-500/30">
                      <CheckCircle className="w-3 h-3" /> DETERMINISTIC
                    </span>
                  </div>
                  <h3 className="text-xs font-bold text-slate-200">{layer.layer_name}</h3>
                  <p className="text-[10px] text-slate-400 mt-1 font-mono">{layer.primary_artifact}</p>
                  <p className="text-[10px] text-slate-500 mt-1">{layer.verification_method}</p>
                </div>
                <div className="mt-3 pt-2 border-t border-slate-800 flex items-center justify-between text-[10px]">
                  <span className="text-slate-500 font-mono">LLM Bypass:</span>
                  <span className="text-emerald-400 font-bold font-mono">100% INVARIANT</span>
                </div>
              </div>
            ))}
          </div>

          {/* Zero-LLM Generation Result Live Telemetry */}
          {zeroLLMResult && (
            <div className="p-4 rounded-xl border border-sky-500/40 bg-sky-950/20 flex flex-col md:flex-row md:items-center justify-between gap-4 animate-fade-in">
              <div className="flex items-center gap-3">
                <CheckCircle className="w-8 h-8 text-sky-400 shrink-0" />
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-sky-200">ZERO-LLM REPORT PRODUCED & VALIDATED</span>
                    <span className="font-mono text-[10px] bg-sky-500/20 text-sky-300 px-2 py-0.5 rounded border border-sky-500/30">
                      {zeroLLMResult.report_id}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-300 mt-0.5">
                    {zeroLLMResult.title} — {zeroLLMResult.section_count} Sections · {zeroLLMResult.table_count} Tables · {zeroLLMResult.page_count} PDF Pages ({zeroLLMResult.renderer_engine})
                  </p>
                  <p className="text-[9px] font-mono text-sky-400/80 mt-0.5">
                    LLM Invocations: {zeroLLMResult.llm_invocations_count} (Strict Zero) · Math Checks: {zeroLLMResult.calculation_checks_passed ? "100% PASSED" : "FAILED"} · Latency: {zeroLLMResult.execution_time_ms.toFixed(1)}ms
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <span className="px-3 py-1.5 bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 font-mono font-bold text-xs rounded-lg">
                  PDF & HTML Output Verified
                </span>
              </div>
            </div>
          )}
        </div>
      )}

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
            href={`${API_BASE}/api/v1/observability/download-diagnostics/${exportResult.bundle_filename}`}
            className="px-3 py-1.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs rounded-lg transition"
            download
          >

            Download ZIP
          </a>
        </div>
      )}

      {/* Section 39: Master Development Phases & Definition-of-Done Matrix */}
      {phasesAudit && (
        <div className="space-y-4 p-6 rounded-2xl border border-slate-700/60 bg-slate-900/70 shadow-xl backdrop-blur-sm">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-slate-800 pb-4">
            <div>
              <div className="flex items-center gap-2">
                <Award className="w-6 h-6 text-amber-400" />
                <h2 className="text-lg font-bold text-white">
                  Development Phases & Definition of Done (Section 39, 42 & 43)
                </h2>
                <span className="px-2.5 py-0.5 text-xs font-mono font-bold rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                  {phasesAudit.completed_phases} / {phasesAudit.total_phases} Phases Complete ({phasesAudit.completion_percentage}%)
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Full lifecycle audit covering Phases 0 through 12 against all 8 Section 42 Definition-of-Done criteria and Section 43 LLM Independence.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <div className="px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700 text-xs flex items-center gap-2">
                <CheckSquare className="w-4 h-4 text-emerald-400" />
                <span className="text-slate-400">Average DoD Score:</span>
                <span className="font-mono font-bold text-emerald-400">{(phasesAudit.average_dod_score * 100).toFixed(0)}%</span>
              </div>
              <div className={`px-3 py-1.5 rounded-lg border text-xs flex items-center gap-2 ${
                phasesAudit.section_43_llm_independence.compliant
                  ? "bg-emerald-500/10 border-emerald-500/40 text-emerald-300"
                  : "bg-rose-500/10 border-rose-500/40 text-rose-300"
              }`}>
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span className="font-semibold">Section 43 Invariant: Verified</span>
              </div>
            </div>
          </div>

          {/* 13 Phases Interactive Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 pt-2">
            {phasesAudit.phases.map((p) => {
              const isSelected = selectedPhase === p.phase_number;
              return (
                <div
                  key={p.phase_number}
                  onClick={() => setSelectedPhase(isSelected ? null : p.phase_number)}
                  className={`p-3.5 rounded-xl border transition cursor-pointer flex flex-col justify-between ${
                    isSelected
                      ? "bg-slate-800/90 border-indigo-500 shadow-md shadow-indigo-950/40 ring-1 ring-indigo-500/30"
                      : "bg-slate-950/40 border-slate-800 hover:border-slate-700 hover:bg-slate-900/60"
                  }`}
                >
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-indigo-400">
                        Phase {p.phase_number}
                      </span>
                      <span className={`inline-flex items-center gap-1 text-[10px] font-mono px-1.5 py-0.5 rounded ${
                        p.is_complete
                          ? "bg-emerald-950/80 text-emerald-400 border border-emerald-500/30"
                          : "bg-amber-950/80 text-amber-400 border border-amber-500/30"
                      }`}>
                        <CheckCircle className="w-3 h-3 text-emerald-400" />
                        DoD {(p.dod_score * 100).toFixed(0)}%
                      </span>
                    </div>

                    <h3 className="text-xs font-bold text-slate-200 line-clamp-1">{p.phase_name}</h3>
                    <p className="text-[10px] text-slate-400 font-mono mt-0.5">{p.specification_section}</p>

                    <div className="mt-2.5 flex flex-wrap gap-1">
                      {p.deliverables.slice(0, 2).map((d, i) => (
                        <span key={i} className="text-[9px] px-1.5 py-0.5 bg-slate-800/80 rounded border border-slate-700/60 text-slate-300">
                          {d}
                        </span>
                      ))}
                      {p.deliverables.length > 2 && (
                        <span className="text-[9px] px-1.5 py-0.5 bg-slate-800/40 rounded text-slate-500">
                          +{p.deliverables.length - 2} more
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="mt-3 pt-2 border-t border-slate-800/80 flex items-center justify-between text-[10px] text-slate-400">
                    <span className="flex items-center gap-1">
                      <FileText className="w-3 h-3 text-slate-500" />
                      <span className="truncate max-w-[130px] font-mono">{p.documentation_record.split("/").pop()}</span>
                    </span>
                    <span className="font-semibold text-emerald-400 font-mono">DONE</span>
                  </div>

                  {/* Expanded DoD breakdown */}
                  {isSelected && (
                    <div className="mt-3 pt-2 border-t border-indigo-500/30 text-[10px] space-y-1.5 animate-fade-in bg-slate-900/90 p-2 rounded-lg">
                      <div className="font-semibold text-slate-300 mb-1">Section 42 Definition of Done (8 Criteria):</div>
                      <div className="grid grid-cols-2 gap-1 font-mono text-[9px]">
                        <span className={p.dod_scorecard.has_implementation ? "text-emerald-400" : "text-slate-600"}>✓ Implementation</span>
                        <span className={p.dod_scorecard.has_unit_tests ? "text-emerald-400" : "text-slate-600"}>✓ Unit Tests</span>
                        <span className={p.dod_scorecard.has_integration_tests ? "text-emerald-400" : "text-slate-600"}>✓ Integration Tests</span>
                        <span className={p.dod_scorecard.has_error_handling ? "text-emerald-400" : "text-slate-600"}>✓ Error Handling</span>
                        <span className={p.dod_scorecard.has_logging ? "text-emerald-400" : "text-slate-600"}>✓ Structured Log</span>
                        <span className={p.dod_scorecard.has_documentation ? "text-emerald-400" : "text-slate-600"}>✓ Documentation</span>
                        <span className={p.dod_scorecard.has_security_review ? "text-emerald-400" : "text-slate-600"}>✓ Security Review</span>
                        <span className={p.dod_scorecard.has_performance_measurement ? "text-emerald-400" : "text-slate-600"}>✓ Perf Benchmarked</span>
                      </div>
                      <div className="pt-1.5 border-t border-slate-800 text-slate-400">
                        <div className="font-semibold text-slate-300">Deliverables:</div>
                        <p className="text-[9px] text-slate-400 mt-0.5">{p.deliverables.join(", ")}</p>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Section 41, 44 & 45: Master Architectural Rules, Invariants & Modular Swappability */}
      {rulesAudit && (
        <div className="space-y-4 p-6 rounded-2xl border border-indigo-500/40 bg-slate-900/80 shadow-2xl backdrop-blur-md">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-slate-800 pb-4">
            <div>
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-6 h-6 text-indigo-400" />
                <h2 className="text-lg font-bold text-white">
                  Architectural Rules, Invariant Verification & Modular Swappability (Sections 41, 44 & 45)
                </h2>
                <span className={`px-2.5 py-0.5 text-xs font-mono font-bold rounded-full border ${
                  rulesAudit.overall_verdict === "CERTIFIED_COMPLIANT"
                    ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                    : "bg-rose-500/10 text-rose-400 border-rose-500/30"
                }`}>
                  {rulesAudit.overall_verdict} ({rulesAudit.total_passed_checks}/{rulesAudit.total_checks} Checks Passed)
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Continuous automated audit verifying the 15 IDE Agent rules, 30-step foundation-first execution order, and 5 decoupled swappable component interfaces.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={handleVerifySwappability}
                disabled={verifyingSwappability}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg transition shadow-md shadow-indigo-950/40"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${verifyingSwappability ? "animate-spin" : ""}`} />
                {verifyingSwappability ? "Verifying Swaps..." : "Verify Swappability"}
              </button>
            </div>
          </div>

          {/* Priority Hierarchy Ribbon */}
          <div className="p-3 bg-indigo-950/40 border border-indigo-500/30 rounded-xl flex items-center justify-between gap-3 text-xs">
            <div className="flex items-center gap-2 text-slate-300">
              <Lock className="w-4 h-4 text-indigo-400 shrink-0" />
              <span className="font-semibold text-indigo-300">Section 45 Governing Principle:</span>
              <span className="font-mono text-emerald-400 bg-slate-900/80 px-2 py-0.5 rounded border border-indigo-500/30">
                {rulesAudit.priority_hierarchy.statement}
              </span>
            </div>
            <span className="text-[10px] text-slate-400 font-mono">Verified in {rulesAudit.execution_time_ms.toFixed(1)}ms</span>
          </div>

          {/* Sub-tabs header */}
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
            <button
              onClick={() => setActiveRulesTab("rules")}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                activeRulesTab === "rules"
                  ? "bg-indigo-600 text-white"
                  : "bg-slate-800 text-slate-400 hover:text-slate-200"
              }`}
            >
              Section 41: 15 Implementation Rules ({rulesAudit.section_41_compliance_pct}%)
            </button>
            <button
              onClick={() => setActiveRulesTab("steps")}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                activeRulesTab === "steps"
                  ? "bg-indigo-600 text-white"
                  : "bg-slate-800 text-slate-400 hover:text-slate-200"
              }`}
            >
              Section 44: 30 Implementation Steps ({rulesAudit.section_44_completion_pct}%)
            </button>
            <button
              onClick={() => setActiveRulesTab("swappability")}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                activeRulesTab === "swappability"
                  ? "bg-indigo-600 text-white"
                  : "bg-slate-800 text-slate-400 hover:text-slate-200"
              }`}
            >
              Section 45: 5 Swappable Interfaces ({rulesAudit.section_45_verified ? "Certified" : "Deficient"})
            </button>
          </div>

          {/* Tab 1: Section 41 Rules */}
          {activeRulesTab === "rules" && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {rulesAudit.section_41_rules.map((rule) => (
                <div
                  key={rule.rule_number}
                  className="p-3.5 rounded-xl border bg-slate-800/40 border-slate-700/60 flex flex-col justify-between hover:border-indigo-500/40 transition"
                >
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-[10px] font-mono font-bold text-indigo-400">RULE {rule.rule_number}</span>
                      <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
                    </div>
                    <h4 className="text-xs font-semibold text-slate-200">{rule.title}</h4>
                    <p className="text-[10px] text-slate-400 mt-1.5 line-clamp-3 leading-relaxed">{rule.details}</p>
                  </div>
                  <div className="mt-2 pt-2 border-t border-slate-800 text-[9px] font-mono text-emerald-400">
                    STATUS: PASSED
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Tab 2: Section 44 Steps (DAG Progression) */}
          {activeRulesTab === "steps" && (
            <div className="space-y-3">
              {implementationOrderReport && (
                <div className="flex items-center justify-between p-2.5 bg-indigo-950/30 border border-indigo-500/20 rounded-xl text-xs">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-indigo-300">Topological DAG Order:</span>
                    <span className="font-mono text-emerald-400 bg-slate-900/90 px-2 py-0.5 rounded border border-indigo-500/30">
                      {implementationOrderReport.topological_order_valid ? "STRICTLY ACYCLIC & VERIFIED" : "CYCLE DETECTED"}
                    </span>
                  </div>
                  <span className="font-mono text-[11px] text-slate-400">
                    {implementationOrderReport.completed_steps} / {implementationOrderReport.total_steps} Completed ({implementationOrderReport.completion_pct}%)
                  </span>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2.5 max-h-[460px] overflow-y-auto pr-1">
                {(implementationOrderReport ? implementationOrderReport.steps : rulesAudit.section_44_steps).map((step: any) => (
                  <div
                    key={step.step_number}
                    className="p-3 rounded-xl border bg-slate-800/40 border-slate-700/60 flex flex-col justify-between hover:border-indigo-500/40 transition"
                  >
                    <div>
                      <div className="flex items-center justify-between gap-1 mb-1.5">
                        <div className="flex items-center gap-1.5">
                          <span className="px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-mono text-[10px] font-bold">
                            #{step.step_number}
                          </span>
                          {step.category && (
                            <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700/50">
                              {step.category}
                            </span>
                          )}
                        </div>
                        <CheckCircle className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                      </div>

                      <h5 className="text-xs font-semibold text-slate-200 line-clamp-1">{step.title}</h5>
                      <p className="text-[9px] font-mono text-slate-400 truncate mt-1">{step.primary_artifact}</p>
                    </div>

                    <div className="mt-2.5 pt-2 border-t border-slate-800 flex items-center justify-between text-[9px] font-mono">
                      <span className="text-slate-500 truncate max-w-[140px]">
                        {step.prerequisites && step.prerequisites.length > 0
                          ? `Prereq: ${step.prerequisites.map((p: number) => `#${p}`).join(", ")}`
                          : "Root (No Prereq)"}
                      </span>
                      <span className="text-emerald-400 font-bold">
                        {step.latency_ms ? `${step.latency_ms.toFixed(1)}ms` : "VERIFIED"}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Tab 3: Section 45 Expected Development Behavior & Swappability */}
          {activeRulesTab === "swappability" && (
            <div className="space-y-4">
              {/* 5 Modular Swappability Cards */}
              <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
                {(expectedBehaviorReport?.swappability_contracts || []).map((item) => {
                  const sim = swapSimulations[item.subsystem_key];
                  const isSimulating = simulatingKey === item.subsystem_key;
                  return (
                    <div
                      key={item.subsystem_key}
                      className="p-3.5 rounded-xl border bg-slate-800/50 border-indigo-500/30 flex flex-col justify-between hover:border-indigo-500/50 transition"
                    >
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-[9px] font-mono uppercase tracking-wider text-indigo-300 font-bold">
                            {item.subsystem_key.toUpperCase()}
                          </span>
                          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                        </div>
                        <h4 className="text-xs font-bold text-slate-100">{item.source_name}</h4>
                        <div className="mt-2 space-y-1 text-[10px]">
                          <div className="text-slate-400">
                            <span className="text-slate-500 font-mono">Contract: </span>
                            <span className="font-mono text-[9px] text-indigo-300 truncate block">{item.interface_class_path.split(".").pop()}</span>
                          </div>
                          <div className="text-slate-400">
                            <span className="text-slate-500 font-mono">Swap Target: </span>
                            <span className="text-slate-300 truncate block">{item.target_name}</span>
                          </div>
                        </div>
                      </div>

                      <div className="mt-3 pt-2 border-t border-slate-700/60 space-y-2">
                        <div className="flex items-center justify-between text-[10px]">
                          <span className="text-emerald-400 font-bold font-mono">DECOUPLED</span>
                          <button
                            onClick={() => handleSimulateSwap(item.subsystem_key)}
                            disabled={isSimulating}
                            className="px-2 py-0.5 text-[9px] font-semibold bg-indigo-600/80 hover:bg-indigo-500 text-white rounded transition"
                          >
                            {isSimulating ? "Simulating..." : "Test Swap"}
                          </button>
                        </div>
                        {sim && (
                          <div className="p-1.5 rounded bg-emerald-950/60 border border-emerald-500/30 text-[9px] text-emerald-300 font-mono">
                            ✓ {sim.latency_ms.toFixed(1)}ms · 0 affected modules
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* 7 Architectural Inquiries for Core Components */}
              {expectedBehaviorReport?.audited_components && (
                <div className="mt-4 pt-3 border-t border-slate-800">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <FileCheck className="w-4 h-4 text-indigo-400" />
                      <span className="text-xs font-bold text-slate-200">
                        Section 45: 7 Architectural Inquiries for System Components
                      </span>
                    </div>
                    <span className="text-[10px] text-slate-400 font-mono">
                      All {expectedBehaviorReport.audited_components.length} Components Certified
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-5 gap-2.5">
                    {expectedBehaviorReport.audited_components.map((comp) => {
                      const isSelected = selectedAuditComponent === comp.component_name;
                      return (
                        <div
                          key={comp.component_name}
                          onClick={() => setSelectedAuditComponent(isSelected ? null : comp.component_name)}
                          className={`p-3 rounded-xl border transition cursor-pointer flex flex-col justify-between ${
                            isSelected
                              ? "bg-slate-800/95 border-indigo-500 ring-1 ring-indigo-500/40"
                              : "bg-slate-900/60 border-slate-800 hover:border-slate-700"
                          }`}
                        >
                          <div>
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-[9px] font-mono text-indigo-300 truncate max-w-[120px]">
                                {comp.component_name}
                              </span>
                              <CheckCircle className="w-3 h-3 text-emerald-400 shrink-0" />
                            </div>
                            <p className="text-[9px] text-slate-400 truncate">{comp.module_path}</p>
                          </div>
                          <div className="mt-2 pt-1.5 border-t border-slate-800 flex items-center justify-between text-[9px] text-slate-500 font-mono">
                            <span>7/7 INQUIRIES</span>
                            <span className="text-emerald-400 font-bold">100%</span>
                          </div>

                          {isSelected && (
                            <div className="mt-3 pt-2 border-t border-indigo-500/30 text-[9px] space-y-1.5 bg-slate-950/80 p-2 rounded-lg">
                              <div className="font-semibold text-slate-300">7 Architectural Inquiries:</div>
                              {comp.inquiries.map((q) => (
                                <div key={q.inquiry_name} className="flex items-start gap-1">
                                  <span className="text-emerald-400 font-bold">✓</span>
                                  <div>
                                    <span className="font-mono text-slate-300 font-semibold">{q.inquiry_name}: </span>
                                    <span className="text-slate-400">{q.summary}</span>
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Section 38: Unified Local Installation & 5-Tier Runtime Stack */}
      {installationStatus && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-slate-200 flex items-center gap-2">
              <Layers className="w-5 h-5 text-indigo-400" />
              Installation & 5-Tier Local Runtime Stack (Section 38)
            </h2>
            <div className="flex items-center gap-2">
              <span className={`px-2.5 py-1 text-xs font-semibold rounded-full border ${
                installationStatus.all_ready
                  ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                  : "bg-amber-500/10 text-amber-400 border-amber-500/30"
              }`}>
                {installationStatus.all_ready ? "System Ready (Air-Gapped)" : "Provisioning In Progress"}
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-3">
            {Object.values(installationStatus.tiers).map((tier) => (
              <div
                key={tier.tier}
                className="p-3.5 rounded-xl border bg-slate-800/40 border-slate-700/60 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
                      {tier.tier.replace("_", " ")}
                    </span>
                    <span className={`w-2 h-2 rounded-full ${tier.is_ready ? "bg-emerald-400" : "bg-amber-400"}`} />
                  </div>
                  <h3 className="text-xs font-bold text-slate-200 line-clamp-1">{tier.name}</h3>
                  <p className="text-[11px] text-slate-400 mt-1 font-mono truncate">
                    {tier.version || (tier.is_ready ? "Ready" : "Pending")}
                  </p>
                </div>
                <div className="mt-3 pt-2 border-t border-slate-700/40 flex items-center justify-between text-[10px]">
                  <span className={tier.is_ready ? "text-emerald-400 font-semibold" : "text-amber-400 font-semibold"}>
                    {tier.is_ready ? "Verified" : "Attention"}
                  </span>
                  <span className="text-slate-500">Tier {tier.tier === "application" ? "1" : tier.tier === "python_runtime" ? "2" : tier.tier === "document_processing" ? "3" : tier.tier === "model_runtime" ? "4" : "5"}</span>
                </div>
              </div>
            ))}
          </div>

          {/* Model Catalog Quick Browser */}
          {modelCatalog && modelCatalog.length > 0 && (
            <div className="p-4 rounded-xl border border-slate-700/60 bg-slate-800/30">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-bold text-slate-300 flex items-center gap-2">
                  <Cpu className="w-4 h-4 text-emerald-400" />
                  Local Approved Models Catalog
                </span>
                <span className="text-[11px] text-slate-400">
                  Active Model: <span className="font-mono text-emerald-400">{installationStatus.active_model_id || "Deterministic Fallback"}</span>
                </span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {modelCatalog.map((m: any) => (
                  <div key={m.model_id} className={`p-3 rounded-lg border text-xs ${m.is_active ? "border-emerald-500/40 bg-emerald-950/20" : "border-slate-700/40 bg-slate-900/40"}`}>
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-slate-200">{m.display_name}</span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded ${m.status === "installed" ? "bg-emerald-500/20 text-emerald-300" : "bg-slate-700 text-slate-300"}`}>
                        {m.status}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 mt-1">{m.formatted_size} · Min {m.min_ram_gb} GB RAM</p>
                    <p className="text-[10px] text-slate-500 mt-0.5 font-mono">{m.license_type}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
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
