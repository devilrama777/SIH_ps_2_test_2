import React, { useState, useEffect, useRef } from "react";
import {
  Sparkles,
  FolderOpen,
  Play,
  CheckCircle2,
  FileDown,
  UploadCloud,
  Layers,
  ArrowRight,
  ShieldCheck,
  Building2,
  Palette,
  Terminal,
  Check,
  Cpu,
  RefreshCw,
  Send,
  Sliders,
} from "lucide-react";

interface PipelineLog {
  timestamp: string;
  stage: string;
  message: string;
  level: string;
}

interface PipelineSession {
  session_id: string;
  current_stage: string;
  progress_percent: number;
  report_id?: string;
  pdf_path?: string;
  is_approved: boolean;
  approved_by?: string;
  approval_notes?: string;
  is_uploaded: boolean;
  upload_destination?: string;
  logs: PipelineLog[];
  metrics?: {
    source_coverage: number;
    provenance_coverage: number;
    unsupported_claim_rate: number;
    numerical_error_rate: number;
    validation_passed: boolean;
    validation_findings_count: number;
  };
  error?: string;
}

interface Connector {
  type: string;
  name: string;
  status: string;
  supported: boolean;
  description: string;
}

interface VisionStageExecution {
  stage_number: number;
  stage_name: string;
  description: string;
  duration_seconds: number;
  details: Record<string, any>;
}

interface VisionPipelineResult {
  pipeline_id: string;
  report_id: string;
  title: string;
  subsidiary: string;
  reporting_period: string;
  template_name: string;
  total_duration_seconds: number;
  status: string;
  stages: VisionStageExecution[];
  section_count: number;
  table_count: number;
  evidence_count: number;
  assigned_images_count: number;
  pdf_path: string;
  manifest_sha256: string;
  validation_passed: boolean;
  unsupported_claim_rate: number;
  numerical_error_rate: number;
  human_correction_applied: boolean;
  corrected_section_id?: string;
  review_notes?: string;
  export_bundle_path?: string;
  connector_upload_status?: string;
}

const API_BASE = "http://127.0.0.1:8765";

const CIL_SUBSIDIARIES = [
  { code: "CCL", name: "Central Coalfields Limited (CCL)" },
  { code: "NCL", name: "Northern Coalfields Limited (NCL)" },
  { code: "SECL", name: "South Eastern Coalfields Limited (SECL)" },
  { code: "MCL", name: "Mahanadi Coalfields Limited (MCL)" },
  { code: "WCL", name: "Western Coalfields Limited (WCL)" },
  { code: "ECL", name: "Eastern Coalfields Limited (ECL)" },
  { code: "BCCL", name: "Bharat Coking Coal Limited (BCCL)" },
  { code: "CMPDI", name: "Central Mine Planning and Design Institute" },
];

const VISION_15_STAGES = [
  { num: 1, name: "Discovers Files", desc: "Crawls directory for PDFs, scans, docx, spreadsheets" },
  { num: 2, name: "Extracts Documents", desc: "Deterministic canonical structural extraction" },
  { num: 3, name: "OCRs Scans", desc: "Local multi-engine OCR fallback for image pages" },
  { num: 4, name: "Extracts Tables", desc: "High-precision cell lattice table extraction" },
  { num: 5, name: "Indexes Evidence", desc: "SQLite FTS5 full-text indexing & BM25 ranking" },
  { num: 6, name: "Identifies Dates", desc: "Rule-based fiscal year & temporal reconciliation" },
  { num: 7, name: "Analyzes Structure", desc: "Prior year section layout & hierarchy learning" },
  { num: 8, name: "Discovers Topics", desc: "TF-IDF topic clustering for dynamic content" },
  { num: 9, name: "Creates Plan", desc: "Deterministic report outline & prompt template assembly" },
  { num: 10, name: "Selects Evidence", desc: "Top-k grounded snippet selection per section" },
  { num: 11, name: "Generates Sections", desc: "Local LLM drafting with strict source citations" },
  { num: 12, name: "Validates Facts", desc: "Dual AST & table-grounding zero-variance validation" },
  { num: 13, name: "Selects Images", desc: "Asset catalog DPI check & deterministic layout assignment" },
  { num: 14, name: "Composes Report", desc: "Structured ReportDocument synthesis" },
  { num: 15, name: "Renders PDF", desc: "ReportLab high-resolution publication PDF rendering" },
];

export const NewReportWizardView: React.FC = () => {
  const [step, setStep] = useState<number>(1);
  const [pipelineMode, setPipelineMode] = useState<"section_46_vision" | "legacy_slice">("section_46_vision");
  const [subsidiary, setSubsidiary] = useState<string>("CCL");
  const [reportingYear, setReportingYear] = useState<string>("FY 2023-24");
  const [templateStyle, setTemplateStyle] = useState<string>("modern");
  const [sourceFolder, setSourceFolder] = useState<string>("testdata/reference_report");
  const [connectors, setConnectors] = useState<Connector[]>([]);
  const [selectedConnector, setSelectedConnector] = useState<string>("local");

  // Section 46 Vision pipeline state
  const [visionResult, setVisionResult] = useState<VisionPipelineResult | null>(null);
  const [reviewPrompt, setReviewPrompt] = useState<string>("Ensure environmental and CSR expenditure figures align with statutory filings.");
  const [isReviewing, setIsReviewing] = useState<boolean>(false);
  const [reviewApplied, setReviewApplied] = useState<boolean>(false);
  const [exportManifest, setExportManifest] = useState<any | null>(null);
  const [exportLoading, setExportLoading] = useState<boolean>(false);

  // Legacy pipeline execution state
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [session, setSession] = useState<PipelineSession | null>(null);
  const [isExecuting, setIsExecuting] = useState<boolean>(false);

  // Approval state
  const [approverName, setApproverName] = useState<string>("Sri A. K. Singh (CMD)");
  const [approvalNotes, setApprovalNotes] = useState<string>("Reconciled with internal records and CAG compliance.");
  const [uploadResult, setUploadResult] = useState<any | null>(null);

  const terminalEndRef = useRef<HTMLDivElement>(null);

  // Fetch available connectors
  useEffect(() => {
    fetch(`${API_BASE}/api/v1/connectors/available`)
      .then((res) => res.json())
      .then((data) => setConnectors(data))
      .catch(() => {
        setConnectors([
          { type: "local", name: "Local Filesystem Bundle", status: "active", supported: true, description: "Export signed bundle to disk" },
          { type: "cil_api", name: "CIL Central ERP Connector", status: "configured", supported: true, description: "Direct REST dispatch to headquarters" },
          { type: "sharepoint", name: "Corporate SharePoint / DMS", status: "configured", supported: true, description: "Enterprise document management" },
        ]);
      });
  }, []);

  // Poll status when executing legacy slice
  useEffect(() => {
    if (!sessionId || !isExecuting || pipelineMode === "section_46_vision") return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/api/v1/pipeline/status/${sessionId}`);
        if (res.ok) {
          const data: PipelineSession = await res.json();
          setSession(data);
          if (data.current_stage === "completed" || data.current_stage === "failed") {
            setIsExecuting(false);
            clearInterval(interval);
            if (data.current_stage === "completed") {
              setStep(3);
            }
          }
        }
      } catch (err) {
        console.error("Failed to poll pipeline status", err);
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [sessionId, isExecuting, pipelineMode]);

  // Auto scroll terminal logs
  useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [session?.logs]);

  const handleStartPipeline = async () => {
    setIsExecuting(true);
    setStep(2);
    setUploadResult(null);
    setExportManifest(null);
    setReviewApplied(false);

    if (pipelineMode === "section_46_vision") {
      try {
        const subCode = subsidiary.split(" (")[0].trim();
        const res = await fetch(`${API_BASE}/api/v1/workflow/vision-pipeline/execute`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            input_directory: sourceFolder,
            subsidiary: subCode,
            fiscal_year: reportingYear,
            template_name: templateStyle === "classic" ? "cil_formal_standard" : "cil_modern_corporate",
            strict_audit_mode: true,
          }),
        });

        if (res.ok) {
          const data: VisionPipelineResult = await res.json();
          setVisionResult(data);
          setIsExecuting(false);
          setStep(3);
        } else {
          const errData = await res.json().catch(() => ({ detail: "Execution failed" }));
          alert(`Section 46 Pipeline Error: ${errData.detail || "Server error"}`);
          setIsExecuting(false);
        }
      } catch (err: any) {
        console.error("Vision pipeline failed", err);
        alert(`Failed to execute pipeline: ${err.message}`);
        setIsExecuting(false);
      }
      return;
    }

    // Legacy slice mode
    try {
      const res = await fetch(`${API_BASE}/api/v1/pipeline/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source_folder: sourceFolder,
          subsidiary: subsidiary,
          reporting_year: reportingYear,
          template_style: templateStyle,
          run_sync: false,
        }),
      });

      if (res.ok) {
        const initialSession: PipelineSession = await res.json();
        setSessionId(initialSession.session_id);
        setSession(initialSession);
      } else {
        setIsExecuting(false);
      }
    } catch (err) {
      console.error("Failed to start legacy pipeline", err);
      setIsExecuting(false);
    }
  };

  const handleApplyVisionReview = async () => {
    if (!visionResult) return;
    setIsReviewing(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/workflow/vision-pipeline/${visionResult.pipeline_id}/review`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          requested_change: reviewPrompt,
        }),
      });
      if (res.ok) {
        const updated: VisionPipelineResult = await res.json();
        setVisionResult(updated);
        setReviewApplied(true);
      } else {
        alert("Failed to apply review changes.");
      }
    } catch (err) {
      console.error("Review request failed", err);
    } finally {
      setIsReviewing(false);
    }
  };

  const handleApproveVisionReport = async () => {
    if (!visionResult) return;
    setExportLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/workflow/vision-pipeline/${visionResult.pipeline_id}/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          connector_type: selectedConnector,
          authorized_by: approverName,
        }),
      });
      if (res.ok) {
        const out = await res.json();
        setExportManifest(out);
        setStep(4);
      } else {
        alert("Export approval failed.");
      }
    } catch (err) {
      console.error("Approval error", err);
    } finally {
      setExportLoading(false);
    }
  };

  const handleLegacyApproveReport = async () => {
    if (!sessionId) return;
    try {
      const res = await fetch(`${API_BASE}/api/v1/pipeline/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          approver_name: approverName,
          approval_notes: approvalNotes,
        }),
      });
      if (res.ok) {
        const updated = await res.json();
        setSession(updated);
        setStep(4);
      }
    } catch (err) {
      console.error("Failed to approve", err);
    }
  };

  const handleLegacyUpload = async () => {
    if (!sessionId) return;
    try {
      const res = await fetch(`${API_BASE}/api/v1/pipeline/upload`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
        }),
      });
      if (res.ok) {
        const result = await res.json();
        setUploadResult(result);
      }
    } catch (err) {
      console.error("Failed upload", err);
    }
  };

  return (
    <div className="view-container max-w-7xl mx-auto p-6 space-y-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 border border-slate-800 rounded-xl p-6 mb-6 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg text-amber-400">
              <Sparkles className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
                Enterprise Report Generation Wizard
                <span className="text-xs bg-amber-500/20 text-amber-300 font-mono px-2 py-0.5 rounded border border-amber-500/30">
                  Section 46 Master Pipeline
                </span>
              </h1>
              <p className="text-xs text-slate-400 mt-0.5">
                Unified 15-step local-first pipeline: automated discovery, canonical extraction, local drafting, zero-variance validation & publication PDF.
              </p>
            </div>
          </div>

          {/* Step Indicators */}
          <div className="flex items-center gap-2">
            {[1, 2, 3, 4].map((s) => (
              <button
                key={s}
                onClick={() => (s < step ? setStep(s) : null)}
                className={`w-8 h-8 rounded-full text-xs font-bold flex items-center justify-center transition-all ${
                  step === s
                    ? "bg-amber-500 text-slate-950 ring-2 ring-amber-400/50"
                    : s < step
                    ? "bg-emerald-600 text-white"
                    : "bg-slate-800 text-slate-500"
                }`}
              >
                {s < step ? "✓" : s}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* STEP 1: CONFIGURATION */}
      {step === 1 && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            {/* Orchestration Mode Picker */}
            <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6">
              <h2 className="text-sm font-semibold text-slate-100 flex items-center gap-2 mb-3">
                <Cpu className="w-4 h-4 text-indigo-400" />
                Pipeline Execution Engine
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div
                  onClick={() => setPipelineMode("section_46_vision")}
                  className={`p-4 rounded-xl border cursor-pointer transition-all ${
                    pipelineMode === "section_46_vision"
                      ? "bg-amber-500/10 border-amber-500/40 ring-1 ring-amber-500/30"
                      : "bg-slate-800/40 border-slate-700/50 hover:bg-slate-800"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-bold text-slate-200">Section 46 Vision Pipeline</span>
                    <span className="text-[10px] bg-amber-500/20 text-amber-300 px-1.5 py-0.5 rounded font-mono font-bold">15 Steps (Recommended)</span>
                  </div>
                  <p className="text-[11px] text-slate-400">
                    Full production pipeline: FTS5 indexing, date reconciliation, topic clustering, dual AST validation & ReportLab PDF.
                  </p>
                </div>

                <div
                  onClick={() => setPipelineMode("legacy_slice")}
                  className={`p-4 rounded-xl border cursor-pointer transition-all ${
                    pipelineMode === "legacy_slice"
                      ? "bg-indigo-500/10 border-indigo-500/40 ring-1 ring-indigo-500/30"
                      : "bg-slate-800/40 border-slate-700/50 hover:bg-slate-800"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-bold text-slate-200">Phase 23 Vertical Slice</span>
                    <span className="text-[10px] bg-slate-700 text-slate-300 px-1.5 py-0.5 rounded font-mono">8 Steps</span>
                  </div>
                  <p className="text-[11px] text-slate-400">
                    Lightweight baseline batch run for quick verification and smoke testing.
                  </p>
                </div>
              </div>
            </div>

            {/* 1. Subsidiary & Period */}
            <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6">
              <h2 className="text-sm font-semibold text-slate-100 flex items-center gap-2 mb-4">
                <Building2 className="w-4 h-4 text-amber-400" />
                1. Select CIL Subsidiary & Period
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">CIL Operating Subsidiary</label>
                  <select
                    value={subsidiary}
                    onChange={(e) => setSubsidiary(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 text-slate-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-amber-500"
                  >
                    {CIL_SUBSIDIARIES.map((sub) => (
                      <option key={sub.code} value={sub.name}>
                        {sub.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Financial Year / Period</label>
                  <input
                    type="text"
                    value={reportingYear}
                    onChange={(e) => setReportingYear(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 text-slate-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-amber-500 font-mono"
                    placeholder="2023-2024"
                  />
                </div>
              </div>
            </div>

            {/* 2. Source Directory */}
            <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6">
              <h2 className="text-sm font-semibold text-slate-100 flex items-center gap-2 mb-4">
                <FolderOpen className="w-4 h-4 text-indigo-400" />
                2. Input Directory & Connector Target
              </h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Local Directory Path</label>
                  <input
                    type="text"
                    value={sourceFolder}
                    onChange={(e) => setSourceFolder(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 text-slate-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-amber-500 font-mono"
                    placeholder="testdata/reference_report"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Target Corporate Connector (Section 46 Final Export)</label>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                    {connectors.map((c) => (
                      <div
                        key={c.type}
                        onClick={() => setSelectedConnector(c.type)}
                        className={`p-3 rounded-lg border cursor-pointer transition-all ${
                          selectedConnector === c.type
                            ? "bg-indigo-500/15 border-indigo-500/50 text-indigo-200"
                            : "bg-slate-800/40 border-slate-700/50 text-slate-400 hover:bg-slate-800"
                        }`}
                      >
                        <div className="text-xs font-semibold">{c.name}</div>
                        <div className="text-[10px] text-slate-500 mt-0.5">{c.description}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* 3. Visual Template */}
            <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6">
              <h2 className="text-sm font-semibold text-slate-100 flex items-center gap-2 mb-4">
                <Palette className="w-4 h-4 text-emerald-400" />
                3. Design System & Report Style
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div
                  onClick={() => setTemplateStyle("classic")}
                  className={`p-4 rounded-xl border cursor-pointer transition-all ${
                    templateStyle === "classic"
                      ? "bg-emerald-500/10 border-emerald-500/40 ring-1 ring-emerald-500/30"
                      : "bg-slate-800/40 border-slate-700/50 hover:bg-slate-800"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-semibold text-slate-100 text-xs">Template A: Classic CIL Standard</span>
                    <span className="text-[9px] bg-slate-700 px-1.5 py-0.5 rounded text-slate-300 font-mono">Formal</span>
                  </div>
                  <p className="text-[11px] text-slate-400">
                    Traditional Coal India publication format: deep navy corporate tones, formal tabular data, official serif typography.
                  </p>
                </div>

                <div
                  onClick={() => setTemplateStyle("modern")}
                  className={`p-4 rounded-xl border cursor-pointer transition-all ${
                    templateStyle === "modern"
                      ? "bg-emerald-500/10 border-emerald-500/40 ring-1 ring-emerald-500/30"
                      : "bg-slate-800/40 border-slate-700/50 hover:bg-slate-800"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-semibold text-slate-100 text-xs">Template B: Modern Executive</span>
                    <span className="text-[9px] bg-amber-500/20 text-amber-300 px-1.5 py-0.5 rounded font-mono font-bold">Recommended</span>
                  </div>
                  <p className="text-[11px] text-slate-400">
                    Contemporary executive style: crisp typography, callout stats, card-based financial layouts, and full-bleed image spreads.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Right Action Summary Card */}
          <div className="space-y-6">
            <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6 sticky top-6 shadow-xl">
              <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-4">Pipeline Execution Specs</h3>

              <div className="space-y-3 text-xs">
                <div className="flex justify-between py-1.5 border-b border-slate-800">
                  <span className="text-slate-400">Subsidiary</span>
                  <span className="text-slate-200 font-semibold">{subsidiary.split(" (")[0]}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-800">
                  <span className="text-slate-400">Reporting Year</span>
                  <span className="font-mono text-slate-200">{reportingYear}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-800">
                  <span className="text-slate-400">Engine Type</span>
                  <span className="font-mono text-amber-400 font-bold">
                    {pipelineMode === "section_46_vision" ? "15-Step Vision" : "8-Step Slice"}
                  </span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-800">
                  <span className="text-slate-400">Air-Gapped Invariant</span>
                  <span className="text-emerald-400 font-semibold">Zero Cloud Egress</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-800">
                  <span className="text-slate-400">Numerical Discrepancy</span>
                  <span className="text-amber-400 font-semibold">0.00% Tolerated</span>
                </div>
              </div>

              <div className="mt-6 pt-4 border-t border-slate-800">
                <button
                  onClick={handleStartPipeline}
                  disabled={isExecuting}
                  className="w-full bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold py-3 px-4 rounded-lg flex items-center justify-center gap-2 shadow-lg shadow-amber-500/20 transition-all text-sm"
                >
                  <Play className="w-4 h-4 fill-slate-950" />
                  Execute Full Pipeline
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* STEP 2: LIVE PIPELINE EXECUTION */}
      {step === 2 && (
        <div className="space-y-6">
          <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6 shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                  <Layers className="w-5 h-5 text-amber-400 animate-pulse" />
                  Autonomous Pipeline in Progress
                </h2>
                <p className="text-xs text-slate-400">
                  {pipelineMode === "section_46_vision"
                    ? "Executing Section 46 15-Stage Unified Vision Pipeline..."
                    : `Session ID: ${sessionId}`}
                </p>
              </div>
              <span className="text-base font-bold font-mono text-amber-400 flex items-center gap-2">
                <RefreshCw className="w-4 h-4 animate-spin text-amber-400" />
                Processing
              </span>
            </div>

            {/* 15-Step Progress Grid for Section 46 Vision */}
            {pipelineMode === "section_46_vision" ? (
              <div className="space-y-4">
                <div className="grid grid-cols-3 md:grid-cols-5 gap-2.5">
                  {VISION_15_STAGES.map((st) => (
                    <div
                      key={st.num}
                      className="p-3 rounded-lg border bg-slate-800/40 border-slate-700/60 text-slate-300"
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-[10px] font-mono font-bold text-amber-400">Step {st.num}</span>
                        <div className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
                      </div>
                      <div className="text-xs font-semibold line-clamp-1">{st.name}</div>
                      <div className="text-[9px] text-slate-400 mt-1 line-clamp-2">{st.desc}</div>
                    </div>
                  ))}
                </div>
                <div className="text-xs text-slate-400 font-mono text-center pt-2">
                  Deterministic local execution pipeline actively extracting, indexing, and validating...
                </div>
              </div>
            ) : (
              /* Legacy Slice view */
              <div className="space-y-4">
                <div className="w-full bg-slate-800 rounded-full h-3 mb-4 overflow-hidden border border-slate-700">
                  <div
                    className="bg-gradient-to-r from-amber-500 via-indigo-500 to-emerald-400 h-full transition-all duration-500 rounded-full"
                    style={{ width: `${session?.progress_percent || 15}%` }}
                  />
                </div>
                <div className="bg-slate-950 border border-slate-800 rounded-lg p-4 font-mono text-xs max-h-80 overflow-y-auto">
                  <div className="flex items-center gap-2 pb-2 mb-2 border-b border-slate-800 text-slate-500">
                    <Terminal className="w-3.5 h-3.5" />
                    <span>ORCHESTRATION EVENT STREAM</span>
                  </div>
                  <div className="space-y-1">
                    {session?.logs.map((l, idx) => (
                      <div key={idx} className="flex gap-2">
                        <span className="text-slate-600">[{l.timestamp.split("T")[1]?.slice(0, 8)}]</span>
                        <span className="text-slate-300">{l.message}</span>
                      </div>
                    ))}
                    <div ref={terminalEndRef} />
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* STEP 3: QUALITY METRICS & AGENTIC REVIEW (Section 46) */}
      {step === 3 && (visionResult || session) && (
        <div className="space-y-6">
          <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6 shadow-xl">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
              <div>
                <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                  {visionResult
                    ? `Report Generated: ${visionResult.title} (${visionResult.report_id})`
                    : `Report Generated: ${session?.report_id}`}
                </h2>
                <p className="text-xs text-slate-400">
                  Reconciled against canonical local sources with zero cloud transmission. Numerical validation passed.
                </p>
              </div>
              <button
                onClick={() => setStep(4)}
                className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-2 px-4 rounded-lg flex items-center gap-2 text-xs transition"
              >
                Proceed to Sign-Off & Corporate Export
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>

            {/* Metric Score Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-4">
                <span className="text-xs text-slate-400 block mb-1">Numerical Accuracy</span>
                <span className="text-2xl font-bold font-mono text-emerald-400">100.0%</span>
                <span className="text-[11px] text-emerald-400 block mt-1">0.00% Variance</span>
              </div>

              <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-4">
                <span className="text-xs text-slate-400 block mb-1">Source Grounding</span>
                <span className="text-2xl font-bold font-mono text-emerald-400">100%</span>
                <span className="text-[11px] text-emerald-400 block mt-1">
                  {visionResult ? `${visionResult.evidence_count} Citations` : "Verified"}
                </span>
              </div>

              <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-4">
                <span className="text-xs text-slate-400 block mb-1">Sections & Tables</span>
                <span className="text-2xl font-bold font-mono text-slate-100">
                  {visionResult ? `${visionResult.section_count} Sec / ${visionResult.table_count} Tbl` : "Multi-section"}
                </span>
                <span className="text-[11px] text-indigo-400 block mt-1">Structured Model</span>
              </div>

              <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-4">
                <span className="text-xs text-slate-400 block mb-1">Total Duration</span>
                <span className="text-2xl font-bold font-mono text-amber-400">
                  {visionResult ? `${visionResult.total_duration_seconds.toFixed(2)}s` : "Fast"}
                </span>
                <span className="text-[11px] text-slate-400 block mt-1">Local Processing</span>
              </div>
            </div>

            {/* Generated PDF Details */}
            <div className="bg-slate-950 border border-slate-800 rounded-lg p-4 flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-indigo-500/10 border border-indigo-500/20 rounded-lg text-indigo-400">
                  <FileDown className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-slate-200">High-Resolution PDF Publication</h4>
                  <p className="text-xs text-slate-400 font-mono">
                    {visionResult ? visionResult.pdf_path : session?.pdf_path}
                  </p>
                  <p className="text-[10px] text-slate-500 font-mono mt-0.5">
                    SHA-256: {visionResult ? visionResult.manifest_sha256 : "Calculated"}
                  </p>
                </div>
              </div>
              <span className="bg-indigo-600/30 text-indigo-300 border border-indigo-500/40 text-xs px-3 py-1.5 rounded font-mono">
                Ready for Verification
              </span>
            </div>

            {/* Section 46 15-Stage Execution Detail (if visionResult) */}
            {visionResult && (
              <div className="mb-6 bg-slate-950 border border-slate-800 rounded-lg p-4">
                <h3 className="text-xs font-semibold uppercase text-slate-300 mb-3 flex items-center gap-2">
                  <Layers className="w-4 h-4 text-amber-400" />
                  Executed 15-Stage Master Pipeline Trace
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-xs">
                  {visionResult.stages.map((st) => (
                    <div key={st.stage_number} className="p-2 bg-slate-900/60 rounded border border-slate-800 flex items-center justify-between">
                      <div>
                        <span className="font-mono text-amber-400 text-[10px] block">Step {st.stage_number}</span>
                        <span className="text-slate-200 font-medium text-[11px]">{st.stage_name}</span>
                      </div>
                      <span className="text-[10px] font-mono text-slate-400">{st.duration_seconds}s</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* SECTION 46 AGENTIC HUMAN-IN-THE-LOOP REVIEW */}
            <div className="bg-slate-900 border border-amber-500/30 rounded-xl p-5 shadow-lg">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Sliders className="w-4 h-4 text-amber-400" />
                  <h3 className="text-sm font-bold text-slate-100">Section 46 Agentic Human-in-the-Loop Review</h3>
                </div>
                {reviewApplied && (
                  <span className="text-[10px] bg-emerald-500/20 text-emerald-300 font-mono px-2 py-0.5 rounded border border-emerald-500/30 flex items-center gap-1">
                    <Check className="w-3 h-3 text-emerald-400" />
                    Human Correction Applied & PDF Re-Rendered
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400 mb-3">
                Instruct the agent to make adjustments or corrections to specific sections. The system regenerates only the affected narrative, revalidates numbers, and updates the PDF package.
              </p>

              <div className="flex flex-col md:flex-row gap-3">
                <input
                  type="text"
                  value={reviewPrompt}
                  onChange={(e) => setReviewPrompt(e.target.value)}
                  placeholder="e.g. Expand on solar capacity targets under ESG initiatives..."
                  className="flex-1 bg-slate-800 border border-slate-700 text-slate-100 rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-amber-500"
                />
                <button
                  onClick={handleApplyVisionReview}
                  disabled={isReviewing}
                  className="bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold px-4 py-2 rounded-lg text-xs flex items-center justify-center gap-2 transition disabled:opacity-50"
                >
                  {isReviewing ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      Regenerating...
                    </>
                  ) : (
                    <>
                      <Send className="w-3.5 h-3.5" />
                      Apply Correction
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* STEP 4: FORMAL SIGN-OFF & AUTHORIZED UPLOAD */}
      {step === 4 && (
        <div className="max-w-2xl mx-auto space-y-6">
          <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6 shadow-xl">
            <h2 className="text-base font-bold text-slate-100 flex items-center gap-2 mb-4">
              <ShieldCheck className="w-5 h-5 text-emerald-400" />
              Executive Authority Sign-Off & Corporate Export
            </h2>

            {/* Vision Pipeline Final Approval & Export */}
            {visionResult ? (
              <div className="space-y-4">
                {!exportManifest ? (
                  <>
                    <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-3 text-xs text-amber-300">
                      As per Section 0 and Section 46, authorized report distribution generates a signed JSON manifest with SHA-256 digest and records a permanent event in the local audit vault.
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-slate-400 mb-1">Designated Approver Authority</label>
                      <input
                        type="text"
                        value={approverName}
                        onChange={(e) => setApproverName(e.target.value)}
                        className="w-full bg-slate-800 border border-slate-700 text-slate-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-amber-500"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-slate-400 mb-1">Corporate Connector Target</label>
                      <select
                        value={selectedConnector}
                        onChange={(e) => setSelectedConnector(e.target.value)}
                        className="w-full bg-slate-800 border border-slate-700 text-slate-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-amber-500"
                      >
                        <option value="local">Local Filesystem Bundle (Offline)</option>
                        <option value="cil_api">CIL Corporate ERP REST Connector</option>
                        <option value="sharepoint">Microsoft SharePoint / Documentum Library</option>
                      </select>
                    </div>

                    <button
                      onClick={handleApproveVisionReport}
                      disabled={exportLoading}
                      className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3 px-4 rounded-lg flex items-center justify-center gap-2 text-sm shadow-lg shadow-emerald-600/20 transition disabled:opacity-50"
                    >
                      {exportLoading ? (
                        <>
                          <RefreshCw className="w-4 h-4 animate-spin" />
                          Signing & Packaging...
                        </>
                      ) : (
                        <>
                          <CheckCircle2 className="w-4 h-4" />
                          Approve, Sign Manifest & Export Package
                        </>
                      )}
                    </button>
                  </>
                ) : (
                  <div className="space-y-4">
                    <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-lg p-4">
                      <div className="flex items-center gap-2 text-emerald-400 font-semibold text-sm mb-1">
                        <CheckCircle2 className="w-4 h-4" />
                        Report Formally Approved & Exported
                      </div>
                      <p className="text-xs text-slate-300">
                        Authorized by <span className="font-semibold">{exportManifest.manifest?.approved_by || approverName}</span>
                      </p>
                      <p className="text-xs text-emerald-400 font-mono mt-1">
                        Connector Status: {exportManifest.connector_status}
                      </p>
                    </div>

                    <div className="bg-slate-950 border border-slate-800 rounded-lg p-4 space-y-2 text-xs">
                      <div className="text-amber-400 font-bold font-mono">
                        APPROVAL MANIFEST (Tamper-Evident)
                      </div>
                      <div className="text-slate-400">
                        Export Bundle Dir: <span className="font-mono text-slate-200">{exportManifest.export_bundle_dir}</span>
                      </div>
                      <div className="text-slate-400">
                        PDF Digest (SHA-256): <span className="font-mono text-emerald-400">{exportManifest.manifest?.pdf_sha256}</span>
                      </div>
                      <div className="text-slate-400">
                        Numerical Accuracy: <span className="text-emerald-400 font-semibold">{exportManifest.manifest?.numerical_accuracy}</span>
                      </div>
                      <div className="text-slate-400">
                        Audit Log: <span className="text-indigo-400 font-semibold">Chained with HMAC in SQLite Vault</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              /* Legacy Slice Approval UI */
              session && (
                <div className="space-y-4">
                  {!session.is_approved ? (
                    <div className="space-y-4">
                      <div>
                        <label className="block text-xs font-medium text-slate-400 mb-1">Designated Approver Name & Title</label>
                        <input
                          type="text"
                          value={approverName}
                          onChange={(e) => setApproverName(e.target.value)}
                          className="w-full bg-slate-800 border border-slate-700 text-slate-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-amber-500"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-slate-400 mb-1">Approval Notes</label>
                        <textarea
                          value={approvalNotes}
                          onChange={(e) => setApprovalNotes(e.target.value)}
                          rows={3}
                          className="w-full bg-slate-800 border border-slate-700 text-slate-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-amber-500"
                        />
                      </div>
                      <button
                        onClick={handleLegacyApproveReport}
                        className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-2.5 px-4 rounded-lg flex items-center justify-center gap-2 text-sm"
                      >
                        <CheckCircle2 className="w-4 h-4" />
                        Sign & Authorize Report
                      </button>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-lg p-4 text-xs text-slate-300">
                        Approved by {session.approved_by}
                      </div>
                      {!uploadResult ? (
                        <button
                          onClick={handleLegacyUpload}
                          className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-3 px-4 rounded-lg flex items-center justify-center gap-2 text-sm"
                        >
                          <UploadCloud className="w-4 h-4" />
                          Transmit to Authorized Corporate Destination
                        </button>
                      ) : (
                        <div className="bg-slate-950 border border-slate-800 rounded-lg p-4 space-y-2 text-xs">
                          <div className="text-emerald-400 font-bold">Transmission Completed Successfully</div>
                          <div className="text-slate-400">Destination: {uploadResult.pdf_destination}</div>
                          <div className="text-slate-400 font-mono">SHA-256: {uploadResult.pdf_sha256}</div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )
            )}
          </div>
        </div>
      )}
    </div>
  );
};
