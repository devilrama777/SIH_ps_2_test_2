import React, { useState, useEffect } from "react";

interface ModelInfo {
  model_id: string;
  display_name: string;
  backend: string;
  context_window: number;
  is_loaded: boolean;
  ram_usage_mb: number | null;
  gpu_accelerated: boolean;
}

interface BackendOption {
  type: string;
  name: string;
  status: string;
  description: string;
}

interface AggregateMetrics {
  model_name: string;
  backend: string;
  total_tasks: number;
  mean_accuracy: number;
  mean_grounding: number;
  mean_hallucination_rate: number;
  avg_latency_seconds: number;
  avg_tokens_per_second: number;
  peak_ram_mb: number;
  avg_cpu_percent: number;
  passed: boolean;
}

export const ModelDiagnosticsView: React.FC = () => {
  const [activeModel, setActiveModel] = useState<ModelInfo | null>(null);
  const [availableBackends, setAvailableBackends] = useState<BackendOption[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isBenchmarking, setIsBenchmarking] = useState<boolean>(false);
  const [latestBenchmark, setLatestBenchmark] = useState<AggregateMetrics | null>(null);
  const [promptInput, setPromptInput] = useState<string>("Summarize raw coal production from [DOC:Annual_Production_FY25.pdf:P12] achieving 773.60 MT.");
  const [generatedResult, setGeneratedResult] = useState<any | null>(null);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchModelInfo = async () => {
    try {
      setIsLoading(true);
      setErrorMsg(null);
      const res = await fetch("http://127.0.0.1:8765/api/v1/ai/models");
      if (!res.ok) throw new Error("Failed to load model diagnostics");
      const data = await res.json();
      setActiveModel(data.active_model);
      setAvailableBackends(data.available_backends || []);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to connect to backend service");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchModelInfo();
  }, []);

  const handleSelectBackend = async (backendType: string) => {
    try {
      setIsLoading(true);
      setErrorMsg(null);
      const res = await fetch("http://127.0.0.1:8765/api/v1/ai/backend/select", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ backend_type: backendType }),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Failed to switch backend");
      }
      await fetchModelInfo();
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRunBenchmark = async () => {
    try {
      setIsBenchmarking(true);
      setErrorMsg(null);
      const res = await fetch("http://127.0.0.1:8765/api/v1/ai/benchmark", {
        method: "POST",
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Benchmark run failed");
      }
      const data: AggregateMetrics = await res.json();
      setLatestBenchmark(data);
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setIsBenchmarking(false);
    }
  };

  const handleQuickGenerate = async () => {
    if (!promptInput.trim()) return;
    try {
      setIsGenerating(true);
      setErrorMsg(null);
      const res = await fetch("http://127.0.0.1:8765/api/v1/ai/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: promptInput, max_tokens: 256 }),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Generation failed");
      }
      const data = await res.json();
      setGeneratedResult(data);
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <div>
        <h2 style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--color-primary-light)" }}>
          Local AI Gateway & Model Evaluation
        </h2>
        <p style={{ color: "var(--color-text-dim)", fontSize: "0.875rem" }}>
          Strictly air-gapped, model-independent local inference engine & benchmark harness (Section 12 & 31).
        </p>
      </div>

      {errorMsg && (
        <div style={{ padding: "0.75rem 1rem", backgroundColor: "#3a1d1d", color: "#fca5a5", borderRadius: "8px", border: "1px solid #7f1d1d" }}>
          {errorMsg}
        </div>
      )}

      {/* Active Model Status Card */}
      <div style={{ backgroundColor: "var(--color-bg-card)", border: "1px solid var(--color-border)", borderRadius: "10px", padding: "1.25rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
          <h3 style={{ fontSize: "1.1rem", fontWeight: 600 }}>Active Local Model</h3>
          <button
            onClick={fetchModelInfo}
            disabled={isLoading}
            style={{
              padding: "0.4rem 0.8rem",
              fontSize: "0.8rem",
              borderRadius: "6px",
              backgroundColor: "var(--color-bg-alt)",
              border: "1px solid var(--color-border)",
              color: "var(--color-text)",
              cursor: "pointer",
            }}
          >
            Refresh Status
          </button>
        </div>

        {activeModel ? (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "1rem" }}>
            <div style={{ backgroundColor: "var(--color-bg-alt)", padding: "0.8rem", borderRadius: "8px" }}>
              <div style={{ fontSize: "0.75rem", color: "var(--color-text-dim)" }}>Model Identifier</div>
              <div style={{ fontWeight: 600, fontSize: "0.95rem", color: "var(--color-primary-light)", wordBreak: "break-all" }}>
                {activeModel.model_id}
              </div>
            </div>
            <div style={{ backgroundColor: "var(--color-bg-alt)", padding: "0.8rem", borderRadius: "8px" }}>
              <div style={{ fontSize: "0.75rem", color: "var(--color-text-dim)" }}>Backend Engine</div>
              <div style={{ fontWeight: 600, fontSize: "0.95rem" }}>{activeModel.backend}</div>
            </div>
            <div style={{ backgroundColor: "var(--color-bg-alt)", padding: "0.8rem", borderRadius: "8px" }}>
              <div style={{ fontSize: "0.75rem", color: "var(--color-text-dim)" }}>Context Window</div>
              <div style={{ fontWeight: 600, fontSize: "0.95rem" }}>{activeModel.context_window.toLocaleString()} tokens</div>
            </div>
            <div style={{ backgroundColor: "var(--color-bg-alt)", padding: "0.8rem", borderRadius: "8px" }}>
              <div style={{ fontSize: "0.75rem", color: "var(--color-text-dim)" }}>Memory Footprint</div>
              <div style={{ fontWeight: 600, fontSize: "0.95rem" }}>{activeModel.ram_usage_mb ? `${activeModel.ram_usage_mb} MB` : "0 MB"}</div>
            </div>
            <div style={{ backgroundColor: "var(--color-bg-alt)", padding: "0.8rem", borderRadius: "8px" }}>
              <div style={{ fontSize: "0.75rem", color: "var(--color-text-dim)" }}>Inference State</div>
              <div style={{ fontWeight: 600, fontSize: "0.95rem", color: activeModel.is_loaded ? "#4ade80" : "#f87171" }}>
                {activeModel.is_loaded ? "Ready & Operational" : "Standby"}
              </div>
            </div>
          </div>
        ) : (
          <div style={{ color: "var(--color-text-dim)" }}>Connecting to local AI Gateway...</div>
        )}
      </div>

      {/* Backend Selection Section */}
      <div style={{ backgroundColor: "var(--color-bg-card)", border: "1px solid var(--color-border)", borderRadius: "10px", padding: "1.25rem" }}>
        <h3 style={{ fontSize: "1.1rem", fontWeight: 600, marginBottom: "0.75rem" }}>Available Local Backends</h3>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "1rem" }}>
          {availableBackends.map((b) => (
            <div
              key={b.type}
              style={{
                backgroundColor: "var(--color-bg-alt)",
                border: b.status === "active" ? "2px solid var(--color-primary)" : "1px solid var(--color-border)",
                borderRadius: "8px",
                padding: "1rem",
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
                gap: "0.5rem",
              }}
            >
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ fontWeight: 600, fontSize: "0.95rem" }}>{b.name}</span>
                  <span
                    style={{
                      fontSize: "0.7rem",
                      padding: "0.2rem 0.5rem",
                      borderRadius: "4px",
                      backgroundColor: b.status === "active" ? "rgba(34, 197, 94, 0.2)" : "rgba(148, 163, 184, 0.2)",
                      color: b.status === "active" ? "#4ade80" : "#94a3b8",
                      fontWeight: 600,
                    }}
                  >
                    {b.status.toUpperCase()}
                  </span>
                </div>
                <p style={{ fontSize: "0.8rem", color: "var(--color-text-dim)", marginTop: "0.4rem" }}>
                  {b.description}
                </p>
              </div>

              {b.status !== "active" && (
                <button
                  onClick={() => handleSelectBackend(b.type)}
                  disabled={isLoading}
                  style={{
                    padding: "0.4rem 0.8rem",
                    borderRadius: "6px",
                    backgroundColor: "var(--color-primary)",
                    color: "white",
                    border: "none",
                    fontWeight: 600,
                    cursor: "pointer",
                    fontSize: "0.8rem",
                    alignSelf: "flex-start",
                  }}
                >
                  Activate Backend
                </button>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Model Benchmark Harness Section */}
      <div style={{ backgroundColor: "var(--color-bg-card)", border: "1px solid var(--color-border)", borderRadius: "10px", padding: "1.25rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
          <div>
            <h3 style={{ fontSize: "1.1rem", fontWeight: 600 }}>Standardized Benchmark Evaluation (Section 31)</h3>
            <p style={{ fontSize: "0.8rem", color: "var(--color-text-dim)" }}>
              Executes all 8 standardized tasks (summarize, evidence selection, sections, tables, contradictions, editing, provenance, report plan).
            </p>
          </div>
          <button
            onClick={handleRunBenchmark}
            disabled={isBenchmarking}
            style={{
              padding: "0.6rem 1.2rem",
              borderRadius: "6px",
              backgroundColor: isBenchmarking ? "var(--color-bg-alt)" : "var(--color-primary)",
              color: "white",
              border: "none",
              fontWeight: 600,
              cursor: isBenchmarking ? "not-allowed" : "pointer",
              fontSize: "0.85rem",
            }}
          >
            {isBenchmarking ? "Running 8 Benchmark Tasks..." : "Run Standard Benchmark"}
          </button>
        </div>

        {latestBenchmark && (
          <div style={{ backgroundColor: "var(--color-bg-alt)", borderRadius: "8px", padding: "1rem", marginTop: "1rem" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.75rem" }}>
              <span
                style={{
                  padding: "0.2rem 0.6rem",
                  borderRadius: "4px",
                  fontSize: "0.75rem",
                  fontWeight: 700,
                  backgroundColor: latestBenchmark.passed ? "rgba(34, 197, 94, 0.2)" : "rgba(239, 68, 68, 0.2)",
                  color: latestBenchmark.passed ? "#4ade80" : "#f87171",
                }}
              >
                {latestBenchmark.passed ? "BENCHMARK PASSED" : "BENCHMARK FAILED"}
              </span>
              <span style={{ fontSize: "0.85rem", color: "var(--color-text-dim)" }}>
                Model: <strong>{latestBenchmark.model_name}</strong> ({latestBenchmark.backend})
              </span>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: "0.75rem" }}>
              <div>
                <div style={{ fontSize: "0.7rem", color: "var(--color-text-dim)" }}>Mean Grounding</div>
                <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "#4ade80" }}>
                  {(latestBenchmark.mean_grounding * 100).toFixed(1)}%
                </div>
              </div>
              <div>
                <div style={{ fontSize: "0.7rem", color: "var(--color-text-dim)" }}>Mean Accuracy</div>
                <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--color-primary-light)" }}>
                  {(latestBenchmark.mean_accuracy * 100).toFixed(1)}%
                </div>
              </div>
              <div>
                <div style={{ fontSize: "0.7rem", color: "var(--color-text-dim)" }}>Hallucination Rate</div>
                <div style={{ fontSize: "1.1rem", fontWeight: 700, color: latestBenchmark.mean_hallucination_rate < 0.2 ? "#4ade80" : "#fbbf24" }}>
                  {(latestBenchmark.mean_hallucination_rate * 100).toFixed(1)}%
                </div>
              </div>
              <div>
                <div style={{ fontSize: "0.7rem", color: "var(--color-text-dim)" }}>Throughput</div>
                <div style={{ fontSize: "1.1rem", fontWeight: 700 }}>
                  {latestBenchmark.avg_tokens_per_second.toFixed(1)} tok/s
                </div>
              </div>
              <div>
                <div style={{ fontSize: "0.7rem", color: "var(--color-text-dim)" }}>Peak RAM</div>
                <div style={{ fontSize: "1.1rem", fontWeight: 700 }}>
                  {latestBenchmark.peak_ram_mb.toFixed(1)} MB
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Interactive AI Sandbox */}
      <div style={{ backgroundColor: "var(--color-bg-card)", border: "1px solid var(--color-border)", borderRadius: "10px", padding: "1.25rem" }}>
        <h3 style={{ fontSize: "1.1rem", fontWeight: 600, marginBottom: "0.5rem" }}>Interactive Grounding Sandbox</h3>
        <p style={{ fontSize: "0.8rem", color: "var(--color-text-dim)", marginBottom: "0.75rem" }}>
          Test prompt generation and verify automatic coordinate / document citation extraction.
        </p>

        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          <textarea
            value={promptInput}
            onChange={(e) => setPromptInput(e.target.value)}
            rows={3}
            style={{
              width: "100%",
              padding: "0.75rem",
              borderRadius: "6px",
              backgroundColor: "var(--color-bg-alt)",
              border: "1px solid var(--color-border)",
              color: "var(--color-text)",
              fontSize: "0.85rem",
              fontFamily: "inherit",
              resize: "vertical",
            }}
          />
          <button
            onClick={handleQuickGenerate}
            disabled={isGenerating}
            style={{
              padding: "0.5rem 1rem",
              borderRadius: "6px",
              backgroundColor: "var(--color-primary)",
              color: "white",
              border: "none",
              fontWeight: 600,
              cursor: isGenerating ? "not-allowed" : "pointer",
              fontSize: "0.85rem",
              alignSelf: "flex-start",
            }}
          >
            {isGenerating ? "Generating..." : "Generate Grounded Output"}
          </button>
        </div>

        {generatedResult && (
          <div style={{ marginTop: "1rem", backgroundColor: "var(--color-bg-alt)", padding: "1rem", borderRadius: "8px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.5rem" }}>
              <span style={{ fontSize: "0.75rem", color: "var(--color-text-dim)" }}>
                Model: <strong>{generatedResult.model_name}</strong> | Latency: {generatedResult.latency_seconds}s
              </span>
              <span
                style={{
                  fontSize: "0.7rem",
                  padding: "0.1rem 0.4rem",
                  borderRadius: "4px",
                  backgroundColor: generatedResult.grounding_metadata?.is_grounded ? "rgba(34, 197, 94, 0.2)" : "rgba(239, 68, 68, 0.2)",
                  color: generatedResult.grounding_metadata?.is_grounded ? "#4ade80" : "#f87171",
                  fontWeight: 600,
                }}
              >
                {generatedResult.grounding_metadata?.is_grounded ? "GROUNDED" : "UNVERIFIED"}
              </span>
            </div>
            <p style={{ fontSize: "0.9rem", lineHeight: 1.5, marginBottom: "0.75rem" }}>
              {generatedResult.content}
            </p>

            {generatedResult.grounding_metadata?.cited_references?.length > 0 && (
              <div>
                <span style={{ fontSize: "0.75rem", color: "var(--color-text-dim)", display: "block", marginBottom: "0.3rem" }}>
                  Extracted Provenance Citations:
                </span>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem" }}>
                  {generatedResult.grounding_metadata.cited_references.map((c: string, idx: number) => (
                    <span
                      key={idx}
                      style={{
                        fontSize: "0.75rem",
                        fontFamily: "monospace",
                        backgroundColor: "rgba(99, 102, 241, 0.2)",
                        color: "var(--color-primary-light)",
                        padding: "0.2rem 0.5rem",
                        borderRadius: "4px",
                        border: "1px solid rgba(99, 102, 241, 0.3)",
                      }}
                    >
                      {c}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
