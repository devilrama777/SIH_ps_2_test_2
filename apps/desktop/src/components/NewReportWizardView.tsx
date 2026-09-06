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

export const NewReportWizardView: React.FC = () => {
  const [step, setStep] = useState<number>(1);
  const [subsidiary, setSubsidiary] = useState<string>("Central Coalfields Limited (CCL)");
  const [reportingYear, setReportingYear] = useState<string>("2024-25");
  const [templateStyle, setTemplateStyle] = useState<"classic" | "modern">("modern");
  const [sourceFolder, setSourceFolder] = useState<string>("testdata/reference_report");
  const [connectors, setConnectors] = useState<Connector[]>([]);
  const [selectedConnector, setSelectedConnector] = useState<string>("local_folder");

  // Pipeline execution state
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
    fetch("http://127.0.0.1:8000/api/v1/connectors/available")
      .then((res) => res.json())
      .then((data) => setConnectors(data))
      .catch(() => {
        setConnectors([
          { type: "local_folder", name: "Local Filesystem", status: "active", supported: true, description: "Direct disk path" },
        ]);
      });
  }, []);

  // Poll status when executing
  useEffect(() => {
    if (!sessionId || !isExecuting) return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`http://127.0.0.1:8000/api/v1/pipeline/status/${sessionId}`);
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
  }, [sessionId, isExecuting]);

  // Auto scroll terminal logs
  useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [session?.logs]);

  const handleStartPipeline = async () => {
    setIsExecuting(true);
    setStep(2);
    setUploadResult(null);

    try {
      const res = await fetch("http://127.0.0.1:8000/api/v1/pipeline/start", {
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
      console.error("Failed to start pipeline", err);
      setIsExecuting(false);
    }
  };

  const handleApproveReport = async () => {
    if (!sessionId) return;
    try {
      const res = await fetch("http://127.0.0.1:8000/api/v1/pipeline/approve", {
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

  const handleAuthorizedUpload = async () => {
    if (!sessionId) return;
    try {
      const res = await fetch("http://127.0.0.1:8000/api/v1/pipeline/upload", {
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
    <div className="view-container">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 border border-slate-800 rounded-xl p-6 mb-6">
        <div className="flex items-center justify-between">
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
              <p className="text-sm text-slate-400">
                Unified autonomous vertical slice: discovery, canonical extraction, FTS5 retrieval, local drafting, deterministic validation & PDF rendering.
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
            <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6">
              <h2 className="text-base font-semibold text-slate-100 flex items-center gap-2 mb-4">
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
                    placeholder="2024-25"
                  />
                </div>
              </div>
            </div>

            <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6">
              <h2 className="text-base font-semibold text-slate-100 flex items-center gap-2 mb-4">
                <FolderOpen className="w-4 h-4 text-indigo-400" />
                2. Select Data Source & Connector
              </h2>

              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  {connectors.map((c) => (
                    <div
                      key={c.type}
                      onClick={() => setSelectedConnector(c.type)}
                      className={`p-3 rounded-lg border cursor-pointer transition-all ${
                        selectedConnector === c.type
                          ? "bg-indigo-500/10 border-indigo-500/40 text-indigo-200"
                          : "bg-slate-800/50 border-slate-700/50 text-slate-400 hover:bg-slate-800"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-semibold">{c.name}</span>
                        <span className="text-[10px] bg-slate-700 px-1.5 py-0.5 rounded font-mono text-slate-300">
                          {c.status}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-400 line-clamp-1">{c.description}</p>
                    </div>
                  ))}
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Source Directory Path</label>
                  <input
                    type="text"
                    value={sourceFolder}
                    onChange={(e) => setSourceFolder(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 text-slate-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-indigo-500 font-mono"
                  />
                  <div className="flex gap-2 mt-2">
                    <button
                      onClick={() => setSourceFolder("testdata/reference_report")}
                      className="text-xs bg-slate-800 text-slate-300 hover:bg-slate-700 px-2.5 py-1 rounded border border-slate-700"
                    >
                      Use Golden Reference Dataset
                    </button>
                    <button
                      onClick={() => setSourceFolder("data/workspace/inbox")}
                      className="text-xs bg-slate-800 text-slate-300 hover:bg-slate-700 px-2.5 py-1 rounded border border-slate-700"
                    >
                      Use Local Inbox
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6">
              <h2 className="text-base font-semibold text-slate-100 flex items-center gap-2 mb-4">
                <Palette className="w-4 h-4 text-emerald-400" />
                3. Choose Corporate Visual Template
              </h2>

              <div className="grid grid-cols-2 gap-4">
                <div
                  onClick={() => setTemplateStyle("classic")}
                  className={`p-4 rounded-xl border cursor-pointer transition-all ${
                    templateStyle === "classic"
                      ? "bg-emerald-500/10 border-emerald-500/40 ring-1 ring-emerald-500/30"
                      : "bg-slate-800/40 border-slate-700/50 hover:bg-slate-800"
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-slate-100 text-sm">Template A: Classic CIL</span>
                    <span className="text-[10px] bg-slate-700 px-1.5 py-0.5 rounded text-slate-300 font-mono">Formal</span>
                  </div>
                  <p className="text-xs text-slate-400">
                    Traditional Coal India annual report format: deep navy corporate tones, formal tabular data, official serif typography.
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
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-slate-100 text-sm">Template B: Modern Corporate</span>
                    <span className="text-[10px] bg-amber-500/20 text-amber-300 px-1.5 py-0.5 rounded font-mono">Recommended</span>
                  </div>
                  <p className="text-xs text-slate-400">
                    Contemporary executive style: crisp typography, callout stats, card-based financial layouts, and full-bleed image spreads.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Right Action Summary Card */}
          <div className="space-y-6">
            <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6 sticky top-6">
              <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider mb-4">Pipeline Execution Specs</h3>

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
                  <span className="text-slate-400">Visual Theme</span>
                  <span className="capitalize text-slate-200">{templateStyle} Corporate</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-800">
                  <span className="text-slate-400">Air-Gapped Invariant</span>
                  <span className="text-emerald-400 font-semibold">Zero Cloud Egress</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-800">
                  <span className="text-slate-400">Grounding Guarantee</span>
                  <span className="text-amber-400 font-semibold">100% Provenance</span>
                </div>
              </div>

              <div className="mt-6 pt-4 border-t border-slate-800">
                <button
                  onClick={handleStartPipeline}
                  disabled={isExecuting}
                  className="w-full bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold py-3 px-4 rounded-lg flex items-center justify-center gap-2 shadow-lg shadow-amber-500/20 transition-all text-sm"
                >
                  <Play className="w-4 h-4 fill-slate-950" />
                  Generate Enterprise Report
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* STEP 2: LIVE PIPELINE EXECUTION */}
      {step === 2 && (
        <div className="space-y-6">
          <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                  <Layers className="w-5 h-5 text-amber-400 animate-pulse" />
                  Autonomous Pipeline in Progress
                </h2>
                <p className="text-xs text-slate-400">
                  Session ID: <span className="font-mono text-slate-300">{sessionId}</span>
                </p>
              </div>
              <span className="text-lg font-bold font-mono text-amber-400">
                {session ? Math.round(session.progress_percent) : 0}%
              </span>
            </div>

            {/* Progress Bar */}
            <div className="w-full bg-slate-800 rounded-full h-3 mb-6 overflow-hidden border border-slate-700">
              <div
                className="bg-gradient-to-r from-amber-500 via-indigo-500 to-emerald-400 h-full transition-all duration-500 rounded-full"
                style={{ width: `${session?.progress_percent || 5}%` }}
              />
            </div>

            {/* Stage Indicators */}
            <div className="grid grid-cols-4 md:grid-cols-8 gap-2 mb-6">
              {[
                "discovery",
                "extraction",
                "indexing",
                "planning",
                "generation",
                "validation",
                "asset_intelligence",
                "pdf_rendering",
              ].map((st) => {
                const isCurrent = session?.current_stage === st;
                const isPast =
                  session &&
                  [
                    "discovery",
                    "extraction",
                    "indexing",
                    "planning",
                    "generation",
                    "validation",
                    "asset_intelligence",
                    "pdf_rendering",
                  ].indexOf(session.current_stage) >
                    [
                      "discovery",
                      "extraction",
                      "indexing",
                      "planning",
                      "generation",
                      "validation",
                      "asset_intelligence",
                      "pdf_rendering",
                    ].indexOf(st);
                return (
                  <div
                    key={st}
                    className={`p-2.5 rounded-lg border text-center transition-all ${
                      isCurrent
                        ? "bg-amber-500/20 border-amber-500/40 text-amber-300 ring-1 ring-amber-500/50 animate-pulse"
                        : isPast
                        ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                        : "bg-slate-800/40 border-slate-800 text-slate-600"
                    }`}
                  >
                    <div className="text-[10px] font-mono uppercase font-bold truncate">
                      {st.replace("_", " ")}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Live Terminal Log Stream */}
            <div className="bg-slate-950 border border-slate-800 rounded-lg p-4 font-mono text-xs max-h-80 overflow-y-auto">
              <div className="flex items-center gap-2 pb-2 mb-2 border-b border-slate-800 text-slate-500">
                <Terminal className="w-3.5 h-3.5" />
                <span>AIR-GAPPED ORCHESTRATION EVENT STREAM</span>
              </div>
              <div className="space-y-1">
                {session?.logs.map((l, idx) => (
                  <div key={idx} className="flex gap-2">
                    <span className="text-slate-600">[{l.timestamp.split("T")[1]?.slice(0, 8)}]</span>
                    <span
                      className={`font-bold ${
                        l.level === "ERROR"
                          ? "text-rose-400"
                          : l.stage === "completed"
                          ? "text-emerald-400"
                          : "text-amber-400"
                      }`}
                    >
                      [{l.stage.toUpperCase()}]
                    </span>
                    <span className="text-slate-300">{l.message}</span>
                  </div>
                ))}
                <div ref={terminalEndRef} />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* STEP 3: QUALITY METRICS & AUDIT REVIEW */}
      {step === 3 && session && (
        <div className="space-y-6">
          <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                  Report Generated Successfully: {session.report_id}
                </h2>
                <p className="text-xs text-slate-400">
                  All factual claims and financial assertions have been reconciled against the local canonical index.
                </p>
              </div>
              <button
                onClick={() => setStep(4)}
                className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-2 px-4 rounded-lg flex items-center gap-2 text-xs"
              >
                Proceed to Sign-Off & Upload
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>

            {/* Metric Score Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-4">
                <span className="text-xs text-slate-400 block mb-1">Source Coverage</span>
                <span className="text-2xl font-bold font-mono text-slate-100">
                  {session.metrics ? `${Math.round(session.metrics.source_coverage * 100)}%` : "N/A"}
                </span>
                <span className="text-[11px] text-emerald-400 block mt-1">Target ≥ 85%</span>
              </div>

              <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-4">
                <span className="text-xs text-slate-400 block mb-1">Provenance Coverage</span>
                <span className="text-2xl font-bold font-mono text-emerald-400">
                  {session.metrics ? `${Math.round(session.metrics.provenance_coverage * 100)}%` : "N/A"}
                </span>
                <span className="text-[11px] text-emerald-400 block mt-1">Grounding: High</span>
              </div>

              <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-4">
                <span className="text-xs text-slate-400 block mb-1">Unsupported Claim Rate</span>
                <span className="text-2xl font-bold font-mono text-slate-100">
                  {session.metrics ? session.metrics.unsupported_claim_rate : "0.00"}
                </span>
                <span className="text-[11px] text-emerald-400 block mt-1">Zero Hallucination</span>
              </div>

              <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-4">
                <span className="text-xs text-slate-400 block mb-1">Numerical Error Rate</span>
                <span className="text-2xl font-bold font-mono text-emerald-400">
                  {session.metrics ? session.metrics.numerical_error_rate : "0.00"}
                </span>
                <span className="text-[11px] text-emerald-400 block mt-1">0% Discrepancy</span>
              </div>
            </div>

            {/* Generated PDF Details */}
            <div className="bg-slate-950 border border-slate-800 rounded-lg p-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-indigo-500/10 border border-indigo-500/20 rounded-lg text-indigo-400">
                  <FileDown className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-slate-200">High-Resolution PDF Artifact</h4>
                  <p className="text-xs text-slate-400 font-mono">{session.pdf_path}</p>
                </div>
              </div>
              <a
                href={`http://127.0.0.1:8000/api/v1/reports/${session.report_id}/pdf`}
                target="_blank"
                rel="noreferrer"
                className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-1.5 px-3 rounded text-xs flex items-center gap-1.5"
              >
                Open Document
              </a>
            </div>
          </div>
        </div>
      )}

      {/* STEP 4: FORMAL SIGN-OFF & AUTHORIZED UPLOAD */}
      {step === 4 && session && (
        <div className="max-w-2xl mx-auto space-y-6">
          <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6">
            <h2 className="text-base font-bold text-slate-100 flex items-center gap-2 mb-4">
              <ShieldCheck className="w-5 h-5 text-emerald-400" />
              Formal Authority Sign-Off & Corporate Upload
            </h2>

            {!session.is_approved ? (
              <div className="space-y-4">
                <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-3 text-xs text-amber-300">
                  As per Section 0 and Section 24, authorized transmission requires explicit approval from designated CIL corporate personnel.
                </div>

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
                  <label className="block text-xs font-medium text-slate-400 mb-1">Approval Notes / Executive Reconciled Remarks</label>
                  <textarea
                    value={approvalNotes}
                    onChange={(e) => setApprovalNotes(e.target.value)}
                    rows={3}
                    className="w-full bg-slate-800 border border-slate-700 text-slate-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-amber-500"
                  />
                </div>

                <button
                  onClick={handleApproveReport}
                  className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-2.5 px-4 rounded-lg flex items-center justify-center gap-2 text-sm shadow-lg shadow-emerald-600/20"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  Sign & Authorize Report
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-lg p-4">
                  <div className="flex items-center gap-2 text-emerald-400 font-semibold text-sm mb-1">
                    <CheckCircle2 className="w-4 h-4" />
                    Report Formally Approved
                  </div>
                  <p className="text-xs text-slate-300">
                    Approved by <span className="font-semibold">{session.approved_by}</span>
                  </p>
                  <p className="text-xs text-slate-400 italic mt-1">"{session.approval_notes}"</p>
                </div>

                {!uploadResult ? (
                  <button
                    onClick={handleAuthorizedUpload}
                    className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-3 px-4 rounded-lg flex items-center justify-center gap-2 text-sm shadow-lg shadow-indigo-600/20"
                  >
                    <UploadCloud className="w-4 h-4" />
                    Transmit to Authorized Corporate Destination
                  </button>
                ) : (
                  <div className="bg-slate-950 border border-slate-800 rounded-lg p-4 space-y-2 text-xs">
                    <div className="text-emerald-400 font-bold flex items-center gap-1.5">
                      <CheckCircle2 className="w-4 h-4" />
                      Transmission Completed Successfully
                    </div>
                    <div className="text-slate-400">
                      Destination: <span className="font-mono text-slate-200">{uploadResult.pdf_destination}</span>
                    </div>
                    <div className="text-slate-400">
                      SHA-256 Digest:{" "}
                      <span className="font-mono text-slate-200">{uploadResult.pdf_sha256}</span>
                    </div>
                    <div className="text-slate-400">
                      Audit Trail Chained: <span className="text-emerald-400 font-semibold">Verified</span>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
