import React, { useState, useEffect } from "react";
import {
  Image as ImageIcon,
  RefreshCw,
  Plus,
  CheckCircle2,
  Layers,
} from "lucide-react";

const API_BASE = "http://127.0.0.1:8765";

interface ImageAsset {
  asset_id: string;
  filename: string;
  file_path: string;
  format: string;
  width: number;
  height: number;
  aspect_ratio: number;
  file_size_bytes: number;
  quality_grade: "excellent" | "acceptable" | "low_res" | "unsuitable";
  is_duplicate: boolean;
  duplicate_of?: string;
  caption?: string;
  tags: string[];
  recommended_layout: string;
  phash?: string;
}

export const AssetManagerView: React.FC = () => {
  const [assets, setAssets] = useState<ImageAsset[]>([]);
  const [activeTag, setActiveTag] = useState<string>("all");
  const [includeDuplicates, setIncludeDuplicates] = useState<boolean>(false);
  const [registerPath, setRegisterPath] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [selectedAsset, setSelectedAsset] = useState<ImageAsset | null>(null);
  const [targetSection, setTargetSection] = useState<string>("sec_ops_01");
  const [targetLayout, setTargetLayout] = useState<string>("with_caption");
  const [assignmentSuccess, setAssignmentSuccess] = useState<string | null>(null);

  const fetchAssets = async () => {
    setIsLoading(true);
    try {
      let url = `${API_BASE}/api/v1/assets?include_duplicates=${includeDuplicates}`;
      if (activeTag !== "all") {
        url += `&tag=${activeTag}`;
      }
      const res = await fetch(url);
      if (res.ok) {
        const data: ImageAsset[] = await res.json();
        setAssets(data);
        if (data.length > 0 && !selectedAsset) {
          setSelectedAsset(data[0]);
        }
      }
    } catch (err) {
      console.error("Failed to load assets:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegisterImage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!registerPath) return;

    try {
      const res = await fetch(`${API_BASE}/api/v1/assets/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_path: registerPath }),
      });
      if (res.ok) {
        setRegisterPath("");
        await fetchAssets();
      } else {
        const err = await res.json();
        alert(`Error: ${err.detail}`);
      }
    } catch (err) {
      console.error("Failed to register image:", err);
    }
  };

  const handleAssignToSection = async () => {
    if (!selectedAsset) return;
    try {
      const res = await fetch(`${API_BASE}/api/v1/assets/assign`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          section_id: targetSection,
          asset_id: selectedAsset.asset_id,
          layout_type: targetLayout,
          caption: selectedAsset.caption || selectedAsset.filename,
        }),
      });
      if (res.ok) {
        setAssignmentSuccess(`Successfully assigned ${selectedAsset.filename} to ${targetSection}`);
        setTimeout(() => setAssignmentSuccess(null), 4000);
      }
    } catch (err) {
      console.error("Assignment error:", err);
    }
  };

  useEffect(() => {
    fetchAssets();
  }, [activeTag, includeDuplicates]);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      {/* Header Bar */}
      <div className="card" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "16px 20px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div style={{ background: "rgba(168, 85, 247, 0.1)", color: "#a855f7", padding: "8px", borderRadius: "8px" }}>
            <ImageIcon size={22} />
          </div>
          <div>
            <h2 style={{ fontSize: "1.15rem", margin: 0, fontWeight: 600 }}>Image Intelligence & Asset Catalog</h2>
            <p style={{ margin: 0, fontSize: "0.82rem", color: "var(--text-secondary)" }}>
              Perceptual deduplication, quality assessment, and deterministic visual layout placement
            </p>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <label style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "0.82rem", cursor: "pointer" }}>
            <input
              type="checkbox"
              checked={includeDuplicates}
              onChange={(e) => setIncludeDuplicates(e.target.checked)}
            />
            Show Duplicates
          </label>

          <button className="btn btn-secondary" onClick={fetchAssets} disabled={isLoading}>
            <RefreshCw size={15} className={isLoading ? "spin" : ""} /> Refresh
          </button>
        </div>
      </div>

      {/* Manual Registration Input */}
      <form onSubmit={handleRegisterImage} className="card" style={{ display: "flex", gap: "10px", padding: "14px 20px" }}>
        <input
          type="text"
          placeholder="Register local image path (e.g. C:/data/reports/images/ccl_dragline.jpg)..."
          value={registerPath}
          onChange={(e) => setRegisterPath(e.target.value)}
          style={{
            flex: 1,
            padding: "8px 12px",
            borderRadius: "6px",
            background: "var(--bg-secondary)",
            color: "var(--text-primary)",
            border: "1px solid var(--border-color)",
          }}
        />
        <button type="submit" className="btn btn-primary" disabled={!registerPath}>
          <Plus size={15} /> Index Image Asset
        </button>
      </form>

      {/* Tag Filters */}
      <div style={{ display: "flex", gap: "8px" }}>
        {["all", "mining", "machinery", "sustainability", "safety", "dispatch", "csr", "governance"].map((tag) => (
          <button
            key={tag}
            onClick={() => setActiveTag(tag)}
            className={`btn ${activeTag === tag ? "btn-primary" : "btn-secondary"}`}
            style={{ fontSize: "0.8rem", padding: "6px 14px", textTransform: "capitalize" }}
          >
            {tag}
          </button>
        ))}
      </div>

      {/* Main Two-Column Layout */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 340px", gap: "20px", alignItems: "start" }}>
        {/* Left: Gallery Grid */}
        <div className="card" style={{ padding: "20px" }}>
          <h3 style={{ fontSize: "1rem", margin: "0 0 16px 0", fontWeight: 600 }}>Cataloged Assets ({assets.length})</h3>

          {assets.length > 0 ? (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: "16px" }}>
              {assets.map((asset) => {
                const isSelected = selectedAsset?.asset_id === asset.asset_id;
                return (
                  <div
                    key={asset.asset_id}
                    onClick={() => setSelectedAsset(asset)}
                    style={{
                      border: `2px solid ${isSelected ? "#a855f7" : "var(--border-color)"}`,
                      borderRadius: "8px",
                      padding: "10px",
                      background: isSelected ? "rgba(168, 85, 247, 0.08)" : "var(--bg-secondary)",
                      cursor: "pointer",
                      display: "flex",
                      flexDirection: "column",
                      gap: "8px",
                    }}
                  >
                    {/* Visual Box */}
                    <div
                      style={{
                        height: "120px",
                        background: "rgba(0, 0, 0, 0.2)",
                        borderRadius: "4px",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        position: "relative",
                        overflow: "hidden",
                      }}
                    >
                      <ImageIcon size={36} style={{ opacity: 0.3 }} />
                      {asset.is_duplicate && (
                        <span
                          style={{
                            position: "absolute",
                            top: "6px",
                            right: "6px",
                            background: "rgba(239, 68, 68, 0.9)",
                            color: "#fff",
                            fontSize: "0.68rem",
                            padding: "2px 6px",
                            borderRadius: "4px",
                            fontWeight: 600,
                          }}
                        >
                          DUPLICATE
                        </span>
                      )}
                    </div>

                    {/* Metadata summary */}
                    <div>
                      <div style={{ fontSize: "0.82rem", fontWeight: 600, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {asset.filename}
                      </div>
                      <div style={{ fontSize: "0.72rem", color: "var(--text-secondary)", marginTop: "2px" }}>
                        {asset.width}x{asset.height} &bull; {asset.format}
                      </div>
                    </div>

                    {/* Quality & Layout Tags */}
                    <div style={{ display: "flex", gap: "4px", flexWrap: "wrap" }}>
                      <span
                        style={{
                          fontSize: "0.68rem",
                          padding: "2px 6px",
                          borderRadius: "4px",
                          fontWeight: 600,
                          background:
                            asset.quality_grade === "excellent"
                              ? "rgba(16, 185, 129, 0.15)"
                              : asset.quality_grade === "acceptable"
                              ? "rgba(59, 130, 246, 0.15)"
                              : "rgba(239, 68, 68, 0.15)",
                          color:
                            asset.quality_grade === "excellent"
                              ? "#10b981"
                              : asset.quality_grade === "acceptable"
                              ? "#3b82f6"
                              : "#ef4444",
                        }}
                      >
                        {asset.quality_grade.toUpperCase()}
                      </span>

                      <span style={{ fontSize: "0.68rem", padding: "2px 6px", borderRadius: "4px", background: "rgba(255, 255, 255, 0.06)", color: "var(--text-secondary)" }}>
                        {asset.recommended_layout}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div style={{ textAlign: "center", padding: "48px 0", color: "var(--text-secondary)" }}>
              <ImageIcon size={40} style={{ opacity: 0.3, marginBottom: "8px" }} />
              <p>No image assets cataloged yet. Use the input above to index local photos.</p>
            </div>
          )}
        </div>

        {/* Right: Selected Asset Inspector & Section Assignment */}
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {selectedAsset ? (
            <div className="card" style={{ padding: "20px" }}>
              <h3 style={{ fontSize: "1rem", margin: "0 0 16px 0", fontWeight: 600 }}>Asset Inspector</h3>

              <div style={{ display: "flex", flexDirection: "column", gap: "10px", fontSize: "0.84rem" }}>
                <div>
                  <span style={{ color: "var(--text-secondary)" }}>Asset ID:</span>
                  <div style={{ fontFamily: "monospace", fontSize: "0.8rem", wordBreak: "break-all" }}>{selectedAsset.asset_id}</div>
                </div>

                <div>
                  <span style={{ color: "var(--text-secondary)" }}>Resolution & Aspect:</span>
                  <div>{selectedAsset.width} x {selectedAsset.height} px ({selectedAsset.aspect_ratio}:1)</div>
                </div>

                <div>
                  <span style={{ color: "var(--text-secondary)" }}>Quality Grade:</span>
                  <div style={{ fontWeight: 600 }}>{selectedAsset.quality_grade.toUpperCase()}</div>
                </div>

                {selectedAsset.phash && (
                  <div>
                    <span style={{ color: "var(--text-secondary)" }}>Perceptual Hash (dHash):</span>
                    <div style={{ fontFamily: "monospace", fontSize: "0.78rem" }}>{selectedAsset.phash}</div>
                  </div>
                )}

                <div>
                  <span style={{ color: "var(--text-secondary)" }}>Local Path:</span>
                  <div style={{ fontSize: "0.76rem", wordBreak: "break-all", background: "var(--bg-secondary)", padding: "6px", borderRadius: "4px" }}>
                    {selectedAsset.file_path}
                  </div>
                </div>

                {/* Section Assignment Workflow */}
                <div style={{ borderTop: "1px solid var(--border-color)", paddingTop: "14px", marginTop: "8px" }}>
                  <h4 style={{ fontSize: "0.88rem", margin: "0 0 10px 0", fontWeight: 600 }}>Assign to Report Section</h4>

                  <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                    <div>
                      <label style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>Target Section ID</label>
                      <input
                        type="text"
                        value={targetSection}
                        onChange={(e) => setTargetSection(e.target.value)}
                        style={{
                          width: "100%",
                          padding: "6px 10px",
                          borderRadius: "4px",
                          background: "var(--bg-secondary)",
                          color: "var(--text-primary)",
                          border: "1px solid var(--border-color)",
                          marginTop: "2px",
                        }}
                      />
                    </div>

                    <div>
                      <label style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>Layout Mode</label>
                      <select
                        value={targetLayout}
                        onChange={(e) => setTargetLayout(e.target.value)}
                        style={{
                          width: "100%",
                          padding: "6px 10px",
                          borderRadius: "4px",
                          background: "var(--bg-secondary)",
                          color: "var(--text-primary)",
                          border: "1px solid var(--border-color)",
                          marginTop: "2px",
                        }}
                      >
                        <option value="single_hero">Single Hero Banner</option>
                        <option value="two_column">Two-Column (Text + Image)</option>
                        <option value="grid_2x2">2x2 Grid</option>
                        <option value="with_caption">With Caption</option>
                        <option value="controlled_spacing">Controlled Spacing</option>
                      </select>
                    </div>

                    <button
                      className="btn btn-primary"
                      onClick={handleAssignToSection}
                      style={{ marginTop: "10px", width: "100%" }}
                    >
                      <Layers size={14} /> Assign Image
                    </button>

                    {assignmentSuccess && (
                      <div style={{ color: "#10b981", fontSize: "0.78rem", display: "flex", alignItems: "center", gap: "4px", marginTop: "6px" }}>
                        <CheckCircle2 size={14} /> {assignmentSuccess}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="card" style={{ padding: "24px", textAlign: "center", color: "var(--text-secondary)" }}>
              <p>Select an asset from the gallery to view metadata and configure section layout assignments.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
