import React, { useState, useEffect } from "react";
import {
  Scan,
  CheckCircle2,
  AlertCircle,
  Play,
  RotateCw,
  Zap,
} from "lucide-react";

const API_BASE = "http://127.0.0.1:8765";

interface OCRHealth {
  engine_name: string;
  available: boolean;
  hardware_backend: string;
  version: string;
  details: Record<string, any>;
  error?: string;
}

interface EngineMetrics {
  engine_name: string;
  pages_processed: number;
  total_time_sec: number;
  pages_per_second: number;
  avg_latency_ms: number;
  avg_confidence: number;
  tables_detected: number;
  lines_detected: number;
  ram_usage_mb: number;
  peak_ram_mb: number;
}

interface BenchmarkReport {
  run_timestamp: number;
  sample_pages_count: number;
  system_cpu_count: number;
  results: Record<string, EngineMetrics>;
  recommended_default: string;
}

interface OCRPageResult {
  page_number: number;
  lines: Array<{
    text: string;
    bbox: { x0: number; y0: number; x1: number; y1: number };
    confidence: number;
    is_heading: boolean;
  }>;
  tables: Array<{
    headers: string[];
    rows: string[][];
    confidence: number;
    title?: string;
  }>;
  overall_confidence: number;
  latency_ms: number;
  engine_name: string;
}

export const OCRControlView: React.FC = () => {
  const [activeEngine, setActiveEngine] = useState<string>("paddleocr_ppstructure_v3");
  const [engines, setEngines] = useState<OCRHealth[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [benchmarkReport, setBenchmarkReport] = useState<BenchmarkReport | null>(null);
  const [isBenchmarking, setIsBenchmarking] = useState<boolean>(false);
  const [ocrSampleResult, setOcrSampleResult] = useState<OCRPageResult | null>(null);
  const [isProcessingSample, setIsProcessingSample] = useState<boolean>(false);
  const [notification, setNotification] = useState<{ message: string; type: "success" | "error" } | null>(null);

  const fetchEngines = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/ocr/engines`);
      if (res.ok) {
        const data = await res.json();
        setActiveEngine(data.active_engine);
        setEngines(data.engines);
      }
    } catch (err) {
      console.error("Failed to load OCR engines:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchEngines();
  }, []);

  const handleSelectEngine = async (engineName: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/ocr/engines/select`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ engine_name: engineName }),
      });
      if (res.ok) {
        setActiveEngine(engineName);
        setNotification({ message: `Active OCR engine changed to ${engineName}`, type: "success" });
      } else {
        const err = await res.json();
        setNotification({ message: `Failed to change engine: ${err.detail}`, type: "error" });
      }
    } catch (err) {
      setNotification({ message: "Network error connecting to local server", type: "error" });
    }
  };

  const handleRunBenchmark = async () => {
    setIsBenchmarking(true);
    setNotification(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/ocr/benchmark`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sample_pages: 2 }),
      });
      if (res.ok) {
        const data = await res.json();
        setBenchmarkReport(data);
        setNotification({ message: "OCR Benchmark completed successfully!", type: "success" });
      } else {
        const err = await res.json();
        setNotification({ message: `Benchmark failed: ${err.detail}`, type: "error" });
      }
    } catch (err) {
      setNotification({ message: "Error running benchmark harness", type: "error" });
    } finally {
      setIsBenchmarking(false);
    }
  };

  const handleRunSampleOCR = async () => {
    setIsProcessingSample(true);
    try {
      // 1x1 transparent PNG payload fallback or simple sample call
      const canvas = document.createElement("canvas");
      canvas.width = 400;
      canvas.height = 300;
      const ctx = canvas.getContext("2d");
      if (ctx) {
        ctx.fillStyle = "#ffffff";
        ctx.fillRect(0, 0, 400, 300);
        ctx.fillStyle = "#000000";
        ctx.font = "16px sans-serif";
        ctx.fillText("BHARAT COKING COAL LIMITED", 30, 40);
        ctx.fillText("Monthly Excavation Record: 185,000 MT", 30, 80);
        ctx.fillText("Colliery Availability: 97.4%", 30, 110);
      }
      const dataUrl = canvas.toDataURL("image/png");
      const b64 = dataUrl.split(",")[1];

      const res = await fetch(`${API_BASE}/api/v1/ocr/process-page`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          image_base64: b64,
          page_number: 1,
          engine_name: activeEngine,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setOcrSampleResult(data);
      }
    } catch (err) {
      console.error("Failed sample OCR:", err);
    } finally {
      setIsProcessingSample(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      {/* Header */}
      <div className="card" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "16px 20px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div style={{ background: "rgba(16, 185, 129, 0.1)", color: "#10b981", padding: "8px", borderRadius: "8px" }}>
            <Scan size={22} />
          </div>
          <div>
            <h2 style={{ fontSize: "1.15rem", margin: 0, fontWeight: 600 }}>Multi-Engine OCR & Layout Intelligence</h2>
            <p style={{ margin: 0, fontSize: "0.82rem", color: "var(--text-secondary)" }}>
              Section 7 Docling, PaddleOCR / PP-StructureV3, and PyMuPDF air-gapped layout analysis
            </p>
          </div>
        </div>

        <div style={{ display: "flex", gap: "10px" }}>
          <button className="btn btn-secondary" onClick={fetchEngines} disabled={isLoading}>
            <RotateCw size={14} className={isLoading ? "spin" : ""} /> Refresh Status
          </button>
          <button className="btn btn-primary" onClick={handleRunBenchmark} disabled={isBenchmarking}>
            <Zap size={14} /> {isBenchmarking ? "Running Benchmark..." : "Run Empirical Benchmark"}
          </button>
        </div>
      </div>

      {notification && (
        <div
          style={{
            padding: "12px 16px",
            borderRadius: "6px",
            background: notification.type === "success" ? "rgba(16, 185, 129, 0.12)" : "rgba(239, 68, 68, 0.12)",
            color: notification.type === "success" ? "#10b981" : "#ef4444",
            border: `1px solid ${notification.type === "success" ? "rgba(16, 185, 129, 0.3)" : "rgba(239, 68, 68, 0.3)"}`,
            fontSize: "0.85rem",
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          {notification.type === "success" ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
          {notification.message}
        </div>
      )}

      {/* Engine Status Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "16px" }}>
        {engines.map((eng) => {
          const isActive = eng.engine_name === activeEngine;
          return (
            <div
              key={eng.engine_name}
              className="card"
              style={{
                padding: "18px",
                border: isActive ? "2px solid #10b981" : "1px solid var(--border-color)",
                position: "relative",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "12px" }}>
                <div>
                  <h3 style={{ margin: 0, fontSize: "0.95rem", fontWeight: 700 }}>
                    {eng.engine_name === "paddleocr_ppstructure_v3"
                      ? "PaddleOCR / PP-Structure"
                      : eng.engine_name === "docling_layout_v1"
                      ? "Docling Multimodal Layout"
                      : "PyMuPDF Raster OCR"}
                  </h3>
                  <span style={{ fontSize: "0.74rem", color: "var(--text-secondary)", fontFamily: "monospace" }}>
                    {eng.engine_name}
                  </span>
                </div>
                {isActive && (
                  <span style={{ fontSize: "0.72rem", background: "#10b981", color: "#fff", padding: "2px 8px", borderRadius: "10px", fontWeight: 600 }}>
                    ACTIVE
                  </span>
                )}
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "6px", fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "16px" }}>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span>Hardware Backend:</span>
                  <strong style={{ color: "var(--text-primary)" }}>{eng.hardware_backend}</strong>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span>Engine Version:</span>
                  <strong style={{ color: "var(--text-primary)" }}>{eng.version}</strong>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span>Availability:</span>
                  <strong style={{ color: eng.available ? "#10b981" : "#ef4444" }}>
                    {eng.available ? "Ready (Air-Gapped)" : "Offline"}
                  </strong>
                </div>
              </div>

              {!isActive && (
                <button
                  className="btn btn-secondary"
                  style={{ width: "100%", fontSize: "0.8rem", padding: "6px 10px" }}
                  onClick={() => handleSelectEngine(eng.engine_name)}
                >
                  Set as Active Engine
                </button>
              )}
            </div>
          );
        })}
      </div>

      {/* Benchmark Results */}
      {benchmarkReport && (
        <div className="card" style={{ padding: "20px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
            <div>
              <h3 style={{ margin: 0, fontSize: "1rem", fontWeight: 600 }}>Section 34 Empirical Benchmark Metrics</h3>
              <p style={{ margin: 0, fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                Evaluated on synthetic CIL multi-column documents with tables, headings, and paragraphs
              </p>
            </div>
            <div style={{ fontSize: "0.8rem", background: "rgba(16, 185, 129, 0.1)", color: "#10b981", padding: "4px 10px", borderRadius: "6px", fontWeight: 600 }}>
              Recommended: {benchmarkReport.recommended_default}
            </div>
          </div>

          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.84rem" }}>
              <thead>
                <tr style={{ background: "var(--bg-secondary)", textAlign: "left" }}>
                  <th style={{ padding: "10px", borderBottom: "1px solid var(--border-color)" }}>Engine</th>
                  <th style={{ padding: "10px", borderBottom: "1px solid var(--border-color)" }}>Throughput (pps)</th>
                  <th style={{ padding: "10px", borderBottom: "1px solid var(--border-color)" }}>Avg Latency (ms)</th>
                  <th style={{ padding: "10px", borderBottom: "1px solid var(--border-color)" }}>Confidence</th>
                  <th style={{ padding: "10px", borderBottom: "1px solid var(--border-color)" }}>Tables Found</th>
                  <th style={{ padding: "10px", borderBottom: "1px solid var(--border-color)" }}>RAM Footprint</th>
                </tr>
              </thead>
              <tbody>
                {Object.values(benchmarkReport.results).map((r) => (
                  <tr key={r.engine_name} style={{ borderBottom: "1px solid var(--border-color)" }}>
                    <td style={{ padding: "10px", fontWeight: 600 }}>{r.engine_name}</td>
                    <td style={{ padding: "10px", color: "#10b981", fontWeight: 700 }}>{r.pages_per_second} pps</td>
                    <td style={{ padding: "10px" }}>{r.avg_latency_ms} ms</td>
                    <td style={{ padding: "10px" }}>{(r.avg_confidence * 100).toFixed(1)}%</td>
                    <td style={{ padding: "10px" }}>{r.tables_detected}</td>
                    <td style={{ padding: "10px" }}>{r.ram_usage_mb} MB</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Interactive OCR Sandbox */}
      <div className="card" style={{ padding: "20px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
          <div>
            <h3 style={{ margin: 0, fontSize: "1rem", fontWeight: 600 }}>Live Layout OCR Sandbox</h3>
            <p style={{ margin: 0, fontSize: "0.8rem", color: "var(--text-secondary)" }}>
              Test layout recognition and table coordinate extraction on sample data
            </p>
          </div>
          <button className="btn btn-secondary" onClick={handleRunSampleOCR} disabled={isProcessingSample}>
            <Play size={14} /> {isProcessingSample ? "Analyzing..." : "Run Test Recognition"}
          </button>
        </div>

        {ocrSampleResult ? (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
            <div>
              <h4 style={{ fontSize: "0.85rem", marginBottom: "8px", fontWeight: 600 }}>Extracted Lines & Coordinates</h4>
              <div
                style={{
                  background: "var(--bg-secondary)",
                  borderRadius: "6px",
                  padding: "12px",
                  maxHeight: "240px",
                  overflowY: "auto",
                  display: "flex",
                  flexDirection: "column",
                  gap: "6px",
                }}
              >
                {ocrSampleResult.lines.map((l, i) => (
                  <div key={i} style={{ fontSize: "0.78rem", borderBottom: "1px solid rgba(255,255,255,0.06)", paddingBottom: "4px" }}>
                    <span style={{ fontWeight: l.is_heading ? 700 : 400, color: l.is_heading ? "#3b82f6" : "inherit" }}>
                      {l.text}
                    </span>
                    <div style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>
                      bbox: [{l.bbox.x0}, {l.bbox.y0}, {l.bbox.x1}, {l.bbox.y1}] &bull; conf: {(l.confidence * 100).toFixed(0)}%
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h4 style={{ fontSize: "0.85rem", marginBottom: "8px", fontWeight: 600 }}>Engine Telemetry</h4>
              <div
                style={{
                  background: "var(--bg-secondary)",
                  borderRadius: "6px",
                  padding: "12px",
                  fontSize: "0.8rem",
                  display: "flex",
                  flexDirection: "column",
                  gap: "8px",
                }}
              >
                <div>Engine: <strong>{ocrSampleResult.engine_name}</strong></div>
                <div>Overall Confidence: <strong>{(ocrSampleResult.overall_confidence * 100).toFixed(1)}%</strong></div>
                <div>Lines Detected: <strong>{ocrSampleResult.lines.length}</strong></div>
                <div>Tables Detected: <strong>{ocrSampleResult.tables.length}</strong></div>
              </div>
            </div>
          </div>
        ) : (
          <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", margin: 0 }}>
            Click &quot;Run Test Recognition&quot; to test the active OCR engine on a synthesized CIL production document.
          </p>
        )}
      </div>
    </div>
  );
};
