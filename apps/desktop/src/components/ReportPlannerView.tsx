import React, { useState, useEffect } from "react";

interface PlannedSection {
  section_id: string;
  title: string;
  level: number;
  type: string;
  discovery_reason?: string;
  subsections: PlannedSection[];
  evidence_package?: {
    sufficiency_score: number;
    is_sufficient: boolean;
    sufficiency_notes?: string;
    ranked_evidence?: Array<{
      element_id: string;
      source_reference: string;
      page_number?: number;
      text: string;
      score: number;
    }>;
    spreadsheet_coordinates?: Array<{
      workbook_name: string;
      sheet_name: string;
      cell?: string;
    }>;
  };
}

interface ReportPlan {
  plan_id: string;
  report_title: string;
  reporting_period: string;
  subsidiary_name: string;
  template_name: string;
  total_planned_sections: number;
  sufficient_sections_count: number;
  sections: PlannedSection[];
}

export const ReportPlannerView: React.FC = () => {
  const [activePlan, setActivePlan] = useState<ReportPlan | null>(null);
  const [historicalPlans, setHistoricalPlans] = useState<any[]>([]);
  const [isPlanning, setIsPlanning] = useState<boolean>(false);
  const [reportTitle, setReportTitle] = useState<string>("CIL Subsidiary Annual Performance & Sustainability Report");
  const [reportingPeriod, setReportingPeriod] = useState<string>("FY 2024-25");
  const [subsidiaryName, setSubsidiaryName] = useState<string>("Eastern Coalfields Limited (ECL)");
  const [templateName, setTemplateName] = useState<string>("modern");
  const [attachEvidence, setAttachEvidence] = useState<boolean>(true);
  const [selectedSectionId, setSelectedSectionId] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchPlans = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8765/api/v1/reports/plans");
      if (res.ok) {
        const data = await res.json();
        setHistoricalPlans(data);
        if (data.length > 0 && !activePlan) {
          loadPlan(data[0].plan_id);
        }
      }
    } catch {
      // Standby if backend offline
    }
  };

  const loadPlan = async (planId: string) => {
    try {
      setErrorMsg(null);
      const res = await fetch(`http://127.0.0.1:8765/api/v1/reports/plans/${planId}`);
      if (!res.ok) throw new Error("Failed to load plan");
      const data: ReportPlan = await res.json();
      setActivePlan(data);
    } catch (err: any) {
      setErrorMsg(err.message);
    }
  };

  useEffect(() => {
    fetchPlans();
  }, []);

  const handleGeneratePlan = async () => {
    try {
      setIsPlanning(true);
      setErrorMsg(null);
      const res = await fetch("http://127.0.0.1:8765/api/v1/reports/plan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          report_title: reportTitle,
          reporting_period: reportingPeriod,
          subsidiary_name: subsidiaryName,
          template_name: templateName,
          attach_evidence: attachEvidence,
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Planning failed");
      }

      const plan: ReportPlan = await res.json();
      setActivePlan(plan);
      await fetchPlans();
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setIsPlanning(false);
    }
  };

  const getSectionBadgeStyle = (type: string) => {
    switch (type.toLowerCase()) {
      case "new_top_level":
      case "discovered":
        return { backgroundColor: "rgba(168, 85, 247, 0.2)", color: "#c084fc", border: "1px solid rgba(168, 85, 247, 0.4)" };
      case "mandatory":
        return { backgroundColor: "rgba(59, 130, 246, 0.2)", color: "#60a5fa", border: "1px solid rgba(59, 130, 246, 0.4)" };
      case "recurring":
        return { backgroundColor: "rgba(34, 197, 94, 0.2)", color: "#4ade80", border: "1px solid rgba(34, 197, 94, 0.4)" };
      case "conditional":
        return { backgroundColor: "rgba(245, 158, 11, 0.2)", color: "#fbbf24", border: "1px solid rgba(245, 158, 11, 0.4)" };
      default:
        return { backgroundColor: "rgba(148, 163, 184, 0.2)", color: "#94a3b8", border: "1px solid rgba(148, 163, 184, 0.4)" };
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <div>
        <h2 style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--color-primary-light)" }}>
          Report Structure Planner & Dynamic Hierarchy
        </h2>
        <p style={{ color: "var(--color-text-dim)", fontSize: "0.875rem" }}>
          Synthesizes recurring corporate chapters with emergent topics discovered in current-year evidence (Sections 13 & 14).
        </p>
      </div>

      {errorMsg && (
        <div style={{ padding: "0.75rem 1rem", backgroundColor: "#3a1d1d", color: "#fca5a5", borderRadius: "8px", border: "1px solid #7f1d1d" }}>
          {errorMsg}
        </div>
      )}

      {/* Plan Configuration Card */}
      <div style={{ backgroundColor: "var(--color-bg-card)", border: "1px solid var(--color-border)", borderRadius: "10px", padding: "1.25rem" }}>
        <h3 style={{ fontSize: "1.1rem", fontWeight: 600, marginBottom: "1rem" }}>Formulate Report Plan</h3>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "1rem", marginBottom: "1rem" }}>
          <div>
            <label style={{ display: "block", fontSize: "0.75rem", color: "var(--color-text-dim)", marginBottom: "0.3rem" }}>Report Title</label>
            <input
              type="text"
              value={reportTitle}
              onChange={(e) => setReportTitle(e.target.value)}
              style={{ width: "100%", padding: "0.5rem", borderRadius: "6px", backgroundColor: "var(--color-bg-alt)", border: "1px solid var(--color-border)", color: "var(--color-text)", fontSize: "0.85rem" }}
            />
          </div>

          <div>
            <label style={{ display: "block", fontSize: "0.75rem", color: "var(--color-text-dim)", marginBottom: "0.3rem" }}>Reporting Period</label>
            <input
              type="text"
              value={reportingPeriod}
              onChange={(e) => setReportingPeriod(e.target.value)}
              style={{ width: "100%", padding: "0.5rem", borderRadius: "6px", backgroundColor: "var(--color-bg-alt)", border: "1px solid var(--color-border)", color: "var(--color-text)", fontSize: "0.85rem" }}
            />
          </div>

          <div>
            <label style={{ display: "block", fontSize: "0.75rem", color: "var(--color-text-dim)", marginBottom: "0.3rem" }}>Subsidiary Entity</label>
            <input
              type="text"
              value={subsidiaryName}
              onChange={(e) => setSubsidiaryName(e.target.value)}
              style={{ width: "100%", padding: "0.5rem", borderRadius: "6px", backgroundColor: "var(--color-bg-alt)", border: "1px solid var(--color-border)", color: "var(--color-text)", fontSize: "0.85rem" }}
            />
          </div>

          <div>
            <label style={{ display: "block", fontSize: "0.75rem", color: "var(--color-text-dim)", marginBottom: "0.3rem" }}>Layout Template (Section 20)</label>
            <select
              value={templateName}
              onChange={(e) => setTemplateName(e.target.value)}
              style={{ width: "100%", padding: "0.5rem", borderRadius: "6px", backgroundColor: "var(--color-bg-alt)", border: "1px solid var(--color-border)", color: "var(--color-text)", fontSize: "0.85rem" }}
            >
              <option value="modern">Template B: Modern Corporate</option>
              <option value="classic">Template A: Existing-Report-Inspired Classic</option>
            </select>
          </div>
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <label style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.85rem", color: "var(--color-text-dim)", cursor: "pointer" }}>
            <input
              type="checkbox"
              checked={attachEvidence}
              onChange={(e) => setAttachEvidence(e.target.checked)}
            />
            Attach Evidence Sets & Check Sufficiency (Recommended)
          </label>

          <button
            onClick={handleGeneratePlan}
            disabled={isPlanning}
            style={{
              padding: "0.6rem 1.4rem",
              borderRadius: "6px",
              backgroundColor: isPlanning ? "var(--color-bg-alt)" : "var(--color-primary)",
              color: "white",
              border: "none",
              fontWeight: 600,
              cursor: isPlanning ? "not-allowed" : "pointer",
              fontSize: "0.85rem",
            }}
          >
            {isPlanning ? "Formulating Plan & Mapping Evidence..." : "Generate Dynamic Report Plan"}
          </button>
        </div>
      </div>

      {/* Main Hierarchy & Details Section */}
      {activePlan && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 340px", gap: "1.5rem" }}>
          {/* Section Tree */}
          <div style={{ backgroundColor: "var(--color-bg-card)", border: "1px solid var(--color-border)", borderRadius: "10px", padding: "1.25rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
              <div>
                <h3 style={{ fontSize: "1.1rem", fontWeight: 600 }}>{activePlan.report_title}</h3>
                <span style={{ fontSize: "0.8rem", color: "var(--color-text-dim)" }}>
                  {activePlan.subsidiary_name} | {activePlan.reporting_period} | Template: {activePlan.template_name.toUpperCase()}
                </span>
              </div>
              <div style={{ textAlign: "right" }}>
                <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--color-primary-light)" }}>
                  {activePlan.total_planned_sections} Sections
                </div>
                <div style={{ fontSize: "0.75rem", color: "#4ade80" }}>
                  {activePlan.sufficient_sections_count} Sufficiently Grounded
                </div>
              </div>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
              {activePlan.sections.map((sec) => (
                <div
                  key={sec.section_id}
                  style={{
                    backgroundColor: selectedSectionId === sec.section_id ? "rgba(99, 102, 241, 0.15)" : "var(--color-bg-alt)",
                    border: selectedSectionId === sec.section_id ? "1px solid var(--color-primary)" : "1px solid var(--color-border)",
                    borderRadius: "8px",
                    padding: "0.9rem",
                    cursor: "pointer",
                  }}
                  onClick={() => setSelectedSectionId(sec.section_id)}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
                      <span style={{ fontSize: "0.75rem", color: "var(--color-text-dim)", fontFamily: "monospace" }}>{sec.section_id}</span>
                      <span style={{ fontWeight: 600, fontSize: "0.95rem" }}>{sec.title}</span>
                    </div>

                    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                      <span style={{ fontSize: "0.7rem", padding: "0.15rem 0.5rem", borderRadius: "4px", ...getSectionBadgeStyle(sec.type), fontWeight: 600 }}>
                        {sec.type.toUpperCase()}
                      </span>
                      {sec.evidence_package && (
                        <span style={{ fontSize: "0.75rem", color: sec.evidence_package.is_sufficient ? "#4ade80" : "#fbbf24" }}>
                          {sec.evidence_package.ranked_evidence?.length || 0} Evidences
                        </span>
                      )}
                    </div>
                  </div>

                  {sec.discovery_reason && (
                    <div style={{ marginTop: "0.4rem", fontSize: "0.75rem", color: "#c084fc", fontStyle: "italic" }}>
                      Reason: {sec.discovery_reason}
                    </div>
                  )}

                  {/* Subsections */}
                  {sec.subsections?.length > 0 && (
                    <div style={{ marginTop: "0.6rem", paddingLeft: "1.2rem", borderLeft: "2px solid rgba(255,255,255,0.1)", display: "flex", flexDirection: "column", gap: "0.4rem" }}>
                      {sec.subsections.map((sub) => (
                        <div
                          key={sub.section_id}
                          style={{
                            display: "flex",
                            justifyContent: "space-between",
                            fontSize: "0.85rem",
                            padding: "0.3rem 0.5rem",
                            borderRadius: "4px",
                            backgroundColor: selectedSectionId === sub.section_id ? "rgba(99, 102, 241, 0.25)" : "transparent",
                          }}
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedSectionId(sub.section_id);
                          }}
                        >
                          <span>{sub.title}</span>
                          <span style={{ fontSize: "0.7rem", color: "var(--color-text-dim)" }}>
                            {sub.type}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Section Evidence Inspector Panel */}
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            <div style={{ backgroundColor: "var(--color-bg-card)", border: "1px solid var(--color-border)", borderRadius: "10px", padding: "1rem" }}>
              <h4 style={{ fontSize: "0.95rem", fontWeight: 600, marginBottom: "0.75rem" }}>Section Evidence Inspector</h4>
              {selectedSectionId ? (
                (() => {
                  let found: PlannedSection | null = null;
                  for (const s of activePlan.sections) {
                    if (s.section_id === selectedSectionId) found = s;
                    for (const sub of s.subsections) {
                      if (sub.section_id === selectedSectionId) found = sub;
                    }
                  }

                  if (!found) return <div style={{ fontSize: "0.8rem", color: "var(--color-text-dim)" }}>Select a section node.</div>;

                  return (
                    <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                      <div>
                        <div style={{ fontSize: "0.75rem", color: "var(--color-text-dim)" }}>Selected Node</div>
                        <div style={{ fontWeight: 600, fontSize: "0.95rem" }}>{found.title}</div>
                      </div>

                      {found.evidence_package && (
                        <div>
                          <div style={{ fontSize: "0.75rem", color: "var(--color-text-dim)" }}>Evidence Grounding Status</div>
                          <div style={{ fontSize: "0.85rem", fontWeight: 600, color: found.evidence_package.is_sufficient ? "#4ade80" : "#fbbf24" }}>
                            {found.evidence_package.sufficiency_notes}
                          </div>

                          {found.evidence_package.spreadsheet_coordinates?.length ? (
                            <div style={{ marginTop: "0.5rem" }}>
                              <div style={{ fontSize: "0.75rem", color: "var(--color-text-dim)" }}>Spreadsheet Cells:</div>
                              {found.evidence_package.spreadsheet_coordinates.map((c, idx) => (
                                <div key={idx} style={{ fontSize: "0.75rem", fontFamily: "monospace", color: "#60a5fa" }}>
                                  {c.workbook_name} &gt; {c.sheet_name} &gt; {c.cell}
                                </div>
                              ))}
                            </div>
                          ) : null}

                          <div style={{ marginTop: "0.5rem" }}>
                            <div style={{ fontSize: "0.75rem", color: "var(--color-text-dim)", marginBottom: "0.3rem" }}>
                              Matched Evidence Excerpts:
                            </div>
                            <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem", maxHeight: "300px", overflowY: "auto" }}>
                              {found.evidence_package.ranked_evidence?.map((ev, idx) => (
                                <div key={idx} style={{ backgroundColor: "var(--color-bg-alt)", padding: "0.5rem", borderRadius: "6px", fontSize: "0.75rem" }}>
                                  <div style={{ color: "var(--color-primary-light)", fontWeight: 600, marginBottom: "0.2rem" }}>
                                    {ev.source_reference} (P.{ev.page_number || 1})
                                  </div>
                                  <div style={{ color: "var(--color-text)" }}>{ev.text.slice(0, 140)}...</div>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })()
              ) : (
                <div style={{ fontSize: "0.8rem", color: "var(--color-text-dim)" }}>
                  Click on any chapter or subsection in the hierarchy to inspect mapped evidence citations.
                </div>
              )}
            </div>

            {/* Saved Plans List */}
            {historicalPlans.length > 1 && (
              <div style={{ backgroundColor: "var(--color-bg-card)", border: "1px solid var(--color-border)", borderRadius: "10px", padding: "1rem" }}>
                <h4 style={{ fontSize: "0.9rem", fontWeight: 600, marginBottom: "0.5rem" }}>Historical Plans</h4>
                <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
                  {historicalPlans.map((p) => (
                    <div
                      key={p.plan_id}
                      onClick={() => loadPlan(p.plan_id)}
                      style={{
                        padding: "0.4rem 0.6rem",
                        borderRadius: "6px",
                        backgroundColor: activePlan.plan_id === p.plan_id ? "var(--color-bg-alt)" : "transparent",
                        border: "1px solid var(--color-border)",
                        fontSize: "0.75rem",
                        cursor: "pointer",
                      }}
                    >
                      <div style={{ fontWeight: 600 }}>{p.report_title}</div>
                      <div style={{ color: "var(--color-text-dim)" }}>{p.reporting_period} | {p.total_planned_sections} sections</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
