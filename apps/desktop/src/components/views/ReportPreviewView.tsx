import React, { useState } from 'react';
import {
  FileText,
  ZoomIn,
  ZoomOut,
  Printer,
  Download,
  CheckCircle2,
  Table as TableIcon,
  ShieldCheck,
  ChevronRight,
  Layers,
  Sparkles,
} from 'lucide-react';
import { ReportItem, ReportSectionNode, EditorBlock } from '../../types';

interface ReportPreviewViewProps {
  report: ReportItem;
  sections: ReportSectionNode[];
  blocks: EditorBlock[];
  onNavigateToExport: () => void;
}

export const ReportPreviewView: React.FC<ReportPreviewViewProps> = ({
  report,
  sections,
  blocks,
  onNavigateToExport,
}) => {
  const [zoomLevel, setZoomLevel] = useState<number>(100);
  const [activeSectionId, setActiveSectionId] = useState<string>(sections[0]?.id || 'sec-1');

  const handleZoom = (delta: number) => {
    setZoomLevel((prev) => Math.min(150, Math.max(70, prev + delta)));
  };

  const handlePrint = () => {
    window.print();
  };

  const scrollToSection = (secId: string) => {
    setActiveSectionId(secId);
    const element = document.getElementById(`preview-${secId}`);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  // Default fallback sections if none in state
  const displaySections = sections.length > 0 ? sections : [
    { id: 'sec-1', title: '1.0 Executive Summary & Mine Concession Overview', level: 1, linkedEvidenceCount: 2, status: 'validated' as const, wordCount: 420 },
    { id: 'sec-2', title: '2.0 Geological Stratigraphy & Core Drillhole Logs', level: 1, linkedEvidenceCount: 2, status: 'validated' as const, wordCount: 680 },
    { id: 'sec-3', title: '3.0 Coal Quality & Certified Laboratory Assay', level: 1, linkedEvidenceCount: 1, status: 'validated' as const, wordCount: 560 },
    { id: 'sec-4', title: '4.0 Geotechnical Slope Stability & Field Observations', level: 1, linkedEvidenceCount: 1, status: 'validated' as const, wordCount: 520 },
    { id: 'sec-5', title: '5.0 Mine Production, Overburden & Stripping Efficiency', level: 1, linkedEvidenceCount: 1, status: 'validated' as const, wordCount: 490 },
    { id: 'sec-6', title: '6.0 Statutory Compliance & QA/QC Audit Trail', level: 1, linkedEvidenceCount: 2, status: 'validated' as const, wordCount: 380 },
  ];

  return (
    <div className="flex-1 overflow-hidden flex flex-col bg-[#0b0f17]">
      {/* Top Preview Control Bar */}
      <div className="h-12 bg-[#121824] border-b border-[#1f2b3d] px-5 flex items-center justify-between text-xs select-none shrink-0">
        <div className="flex items-center gap-3">
          <FileText className="w-4 h-4 text-blue-400" />
          <span className="font-mono font-bold text-slate-100 truncate max-w-md">
            {report?.name || 'Consolidated Technical & Geological Evaluation (Block ML-492)'}
          </span>
          <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-950/50 border border-emerald-800/60 text-emerald-400 flex items-center gap-1 font-semibold">
            <CheckCircle2 className="w-3 h-3" />
            AUTONOMOUSLY GENERATED • 5 SOURCES LINKED
          </span>
        </div>

        {/* Action & Zoom Controls */}
        <div className="flex items-center gap-3">
          {/* Zoom */}
          <div className="flex items-center gap-1 font-mono text-xs text-slate-300 bg-slate-900 border border-slate-700/80 rounded px-1.5 py-0.5">
            <button
              type="button"
              onClick={() => handleZoom(-10)}
              className="p-1 rounded hover:bg-slate-800 cursor-pointer text-slate-400 hover:text-white"
              title="Zoom Out"
            >
              <ZoomOut className="w-3.5 h-3.5" />
            </button>
            <span className="w-10 text-center text-[11px] font-bold">{zoomLevel}%</span>
            <button
              type="button"
              onClick={() => handleZoom(10)}
              className="p-1 rounded hover:bg-slate-800 cursor-pointer text-slate-400 hover:text-white"
              title="Zoom In"
            >
              <ZoomIn className="w-3.5 h-3.5" />
            </button>
          </div>

          <button
            type="button"
            onClick={handlePrint}
            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded font-mono text-xs transition flex items-center gap-1.5 cursor-pointer"
            title="Print Report"
          >
            <Printer className="w-3.5 h-3.5" />
            <span>Print</span>
          </button>

          <button
            type="button"
            onClick={onNavigateToExport}
            className="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded font-mono text-xs transition flex items-center gap-1.5 cursor-pointer shadow-sm"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export PDF</span>
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Clean Section Navigation */}
        <div className="w-64 bg-[#0f141f] border-r border-[#1f2b3d] flex flex-col shrink-0 select-none">
          <div className="p-3 border-b border-[#1f2b3d] bg-[#111722] flex items-center justify-between text-[11px] font-mono text-slate-400">
            <span className="flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-blue-400" />
              TABLE OF CONTENTS
            </span>
            <span className="text-emerald-400">{displaySections.length} SECTIONS</span>
          </div>

          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {displaySections.map((sec, idx) => {
              const isActive = sec.id === activeSectionId;
              return (
                <button
                  key={sec.id}
                  type="button"
                  onClick={() => scrollToSection(sec.id)}
                  className={`w-full text-left p-2.5 rounded transition text-xs font-mono flex items-start gap-2 cursor-pointer ${
                    isActive
                      ? 'bg-blue-950/60 border border-blue-600/70 text-blue-200 font-semibold'
                      : 'hover:bg-slate-800/50 text-slate-400 hover:text-slate-200 border border-transparent'
                  }`}
                >
                  <span className="text-slate-400 text-[10px] mt-0.5">{String(idx + 1).padStart(2, '0')}</span>
                  <span className="truncate flex-1 leading-snug">{sec.title}</span>
                </button>
              );
            })}
          </div>

          {/* Verification Badge Footer */}
          <div className="p-3 border-t border-slate-800 bg-[#0c1018] text-[11px] font-mono text-slate-400 space-y-1">
            <div className="flex items-center gap-1.5 text-emerald-400 font-bold">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>DGMS / CIL VERIFIED</span>
            </div>
            <div className="text-[10px] text-slate-400">
              Audit Score: 98% • Airgap Enforced
            </div>
          </div>
        </div>

        {/* Center: Clean, Readable A4 Document Canvas */}
        <div className="flex-1 overflow-y-auto p-8 flex justify-center bg-[#070a0f]">
          <div
            style={{ transform: `scale(${zoomLevel / 100})`, transformOrigin: 'top center' }}
            className="transition-transform duration-100 ease-out"
          >
            {/* The Clean White A4 Paper Sheet */}
            <div className="w-[820px] min-h-[1160px] bg-white text-slate-900 shadow-2xl p-12 flex flex-col justify-between select-text rounded-xs">
              {/* Document Running Header */}
              <div className="border-b-2 border-slate-900 pb-3 flex items-center justify-between text-[11px] text-slate-600 font-mono uppercase tracking-wider">
                <span className="font-bold text-slate-900">MineIntel • Autonomous Geological & Mine Technical Evaluation</span>
                <span className="text-blue-900 font-semibold">Block ML-492 • Q4 FY26</span>
              </div>

              {/* Main Document Body */}
              <div className="py-6 space-y-8 flex-1">
                {/* Title Banner */}
                <div className="border-b border-slate-200 pb-5">
                  <div className="text-xs font-mono font-bold text-blue-900 uppercase tracking-widest mb-1">
                    Statutory Mining Technical Report
                  </div>
                  <h1 className="text-2xl font-extrabold text-slate-950 tracking-tight leading-snug">
                    Consolidated Geological & Mine Technical Evaluation
                  </h1>
                  <p className="text-xs text-slate-600 font-mono mt-1">
                    Mining Lease Concession Block ML-492 (24.8 sq km) • WGS84 UTM Zone 45N
                  </p>
                </div>

                {/* Key Summary Cards Bar */}
                <div className="grid grid-cols-4 gap-3 text-xs font-mono">
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded text-center">
                    <div className="text-[10px] text-slate-500 uppercase">Proved Reserves</div>
                    <div className="text-base font-extrabold text-slate-900 mt-0.5">42.6 MT</div>
                    <div className="text-[9px] text-slate-400">Mineable Coal</div>
                  </div>
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded text-center">
                    <div className="text-[10px] text-slate-500 uppercase">Primary Intercept</div>
                    <div className="text-base font-extrabold text-blue-900 mt-0.5">9.6 m</div>
                    <div className="text-[9px] text-slate-400">Seam II (Clean Coal)</div>
                  </div>
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded text-center">
                    <div className="text-[10px] text-slate-500 uppercase">Coal Grade (GCV)</div>
                    <div className="text-base font-extrabold text-emerald-900 mt-0.5">G8 (5,420)</div>
                    <div className="text-[9px] text-slate-400">kcal/kg Composite</div>
                  </div>
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded text-center">
                    <div className="text-[10px] text-slate-500 uppercase">Slope Safety (FoS)</div>
                    <div className="text-base font-extrabold text-slate-900 mt-0.5">1.42</div>
                    <div className="text-[9px] text-emerald-700 font-semibold">DGMS Compliant</div>
                  </div>
                </div>

                {/* Section 1: Executive Summary */}
                <div id="preview-sec-1" className="space-y-3 pt-2">
                  <h2 className="text-base font-bold text-slate-900 border-b border-slate-200 pb-1.5 flex items-center justify-between">
                    <span>1.0 Executive Summary & Mine Concession Overview</span>
                    <span className="text-[10px] font-mono text-slate-500 font-normal">[EVID-005]</span>
                  </h2>
                  <p className="text-xs text-slate-700 leading-relaxed text-justify">
                    This technical synthesis compiles multi-source exploration drilling, certified laboratory proximate assays, geotechnical field observations, and production telemetry for Mining Lease Block ML-492 (24.8 sq km). All survey benchmarks are referenced in UTM Zone 45N (WGS84 datum, Northing 2634100m to 2638500m, Easting 432100m to 437400m) in strict conformance with CIL/CMPDI statutory exploration protocols. Exploration confirms a high-value bituminous deposit amenable to open-cast mechanized extraction.
                  </p>
                </div>

                {/* Section 2: Geological Stratigraphy & Drillhole Logs */}
                <div id="preview-sec-2" className="space-y-3">
                  <h2 className="text-base font-bold text-slate-900 border-b border-slate-200 pb-1.5 flex items-center justify-between">
                    <span>2.0 Geological Stratigraphy & Core Drillhole Logs</span>
                    <span className="text-[10px] font-mono text-slate-500 font-normal">[EVID-001, EVID-006]</span>
                  </h2>
                  <p className="text-xs text-slate-700 leading-relaxed text-justify">
                    Exploration diamond core drilling confirmed persistent lateral continuity of three primary coal seams across the tenement. Borehole BH-2026-04 intercepted prime metallurgical Seam II at depth 45.2m to 54.8m with a clean net thickness of 9.6m, displaying low dirt-band inclusion and favorable hanging-wall sandstone competence.
                  </p>

                  {/* Borehole Summary Table */}
                  <div className="space-y-1">
                    <div className="text-[11px] font-mono font-bold text-slate-800">
                      Table 2.1: Key Exploration Borehole Core Intercepts & Seam Assay Matrix
                    </div>
                    <table className="w-full text-[11px] font-mono border border-slate-300 border-collapse">
                      <thead>
                        <tr className="bg-slate-100 text-slate-800 border-b border-slate-300 font-bold">
                          <th className="p-2 text-left border-r border-slate-300">Borehole ID</th>
                          <th className="p-2 text-left border-r border-slate-300">Target Seam</th>
                          <th className="p-2 text-right border-r border-slate-300">Depth (m)</th>
                          <th className="p-2 text-right border-r border-slate-300">Thickness (m)</th>
                          <th className="p-2 text-right border-r border-slate-300">Ash (%)</th>
                          <th className="p-2 text-right border-r border-slate-300">GCV (kcal/kg)</th>
                          <th className="p-2 text-center">Grade</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-200 text-slate-700">
                        <tr>
                          <td className="p-1.5 border-r border-slate-300 font-semibold">BH-2026-01</td>
                          <td className="p-1.5 border-r border-slate-300">Seam I</td>
                          <td className="p-1.5 border-r border-slate-300 text-right">28.4 – 33.6</td>
                          <td className="p-1.5 border-r border-slate-300 text-right font-medium">5.2</td>
                          <td className="p-1.5 border-r border-slate-300 text-right">22.1%</td>
                          <td className="p-1.5 border-r border-slate-300 text-right">5,680</td>
                          <td className="p-1.5 text-center text-emerald-800 font-semibold">G7</td>
                        </tr>
                        <tr>
                          <td className="p-1.5 border-r border-slate-300 font-semibold">BH-2026-02</td>
                          <td className="p-1.5 border-r border-slate-300">Seam I</td>
                          <td className="p-1.5 border-r border-slate-300 text-right">31.0 – 36.8</td>
                          <td className="p-1.5 border-r border-slate-300 text-right font-medium">5.8</td>
                          <td className="p-1.5 border-r border-slate-300 text-right">21.4%</td>
                          <td className="p-1.5 border-r border-slate-300 text-right">5,740</td>
                          <td className="p-1.5 text-center text-emerald-800 font-semibold">G7</td>
                        </tr>
                        <tr className="bg-blue-50/60 font-semibold">
                          <td className="p-1.5 border-r border-slate-300 text-blue-900">BH-2026-04</td>
                          <td className="p-1.5 border-r border-slate-300 text-blue-900">Seam II (Prime)</td>
                          <td className="p-1.5 border-r border-slate-300 text-right">45.2 – 54.8</td>
                          <td className="p-1.5 border-r border-slate-300 text-right text-emerald-800 font-bold">9.6</td>
                          <td className="p-1.5 border-r border-slate-300 text-right">18.4%</td>
                          <td className="p-1.5 border-r border-slate-300 text-right font-bold text-blue-900">6,120</td>
                          <td className="p-1.5 text-center text-emerald-800 font-bold">G4</td>
                        </tr>
                        <tr>
                          <td className="p-1.5 border-r border-slate-300 font-semibold">BH-2026-05</td>
                          <td className="p-1.5 border-r border-slate-300">Seam III</td>
                          <td className="p-1.5 border-r border-slate-300 text-right">78.5 – 84.1</td>
                          <td className="p-1.5 border-r border-slate-300 text-right font-medium">5.6</td>
                          <td className="p-1.5 border-r border-slate-300 text-right">26.8%</td>
                          <td className="p-1.5 border-r border-slate-300 text-right">5,150</td>
                          <td className="p-1.5 text-center text-amber-800 font-semibold">G9</td>
                        </tr>
                        <tr className="bg-slate-100 font-bold text-slate-900 border-t-2 border-slate-300">
                          <td className="p-1.5 border-r border-slate-300" colSpan={3}>Proved Cumulative Reserve</td>
                          <td className="p-1.5 border-r border-slate-300 text-right text-emerald-800">26.2 m</td>
                          <td className="p-1.5 border-r border-slate-300 text-right">22.2%</td>
                          <td className="p-1.5 border-r border-slate-300 text-right">5,672</td>
                          <td className="p-1.5 text-center text-blue-900">42.6 MT</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Section 3: Coal Quality & Certified Laboratory Assay */}
                <div id="preview-sec-3" className="space-y-3">
                  <h2 className="text-base font-bold text-slate-900 border-b border-slate-200 pb-1.5 flex items-center justify-between">
                    <span>3.0 Coal Quality & Certified Laboratory Assay</span>
                    <span className="text-[10px] font-mono text-slate-500 font-normal">[EVID-002]</span>
                  </h2>
                  <p className="text-xs text-slate-700 leading-relaxed text-justify">
                    Certified proximate and ultimate analysis of drill core composites by the NABL-accredited Central Testing Laboratory indicates consistent medium-rank bituminous coal with low total sulfur (0.48%) and high ash fusion temperature (1,380°C).
                  </p>

                  {/* Lab Proximate Table */}
                  <div className="space-y-1">
                    <div className="text-[11px] font-mono font-bold text-slate-800">
                      Table 3.1: Certified Composite Proximate & Ultimate Assay Results (IS 1350)
                    </div>
                    <table className="w-full text-[11px] font-mono border border-slate-300 border-collapse">
                      <thead>
                        <tr className="bg-slate-100 text-slate-800 border-b border-slate-300 font-bold">
                          <th className="p-2 text-left border-r border-slate-300">Parameter</th>
                          <th className="p-2 text-right border-r border-slate-300">Measured Value</th>
                          <th className="p-2 text-left border-r border-slate-300">Standard Test Method</th>
                          <th className="p-2 text-center">Statutory Compliance</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-200 text-slate-700">
                        <tr>
                          <td className="p-1.5 border-r border-slate-300 font-medium">Total Moisture</td>
                          <td className="p-1.5 border-r border-slate-300 text-right font-bold">6.8%</td>
                          <td className="p-1.5 border-r border-slate-300">IS 1350 (Part I)</td>
                          <td className="p-1.5 text-center text-emerald-800 font-semibold">Pass (&lt; 10%)</td>
                        </tr>
                        <tr>
                          <td className="p-1.5 border-r border-slate-300 font-medium">Ash Content (air-dried)</td>
                          <td className="p-1.5 border-r border-slate-300 text-right font-bold">24.2%</td>
                          <td className="p-1.5 border-r border-slate-300">IS 1350 (Part I)</td>
                          <td className="p-1.5 text-center text-blue-900 font-semibold">Grade G8 Band</td>
                        </tr>
                        <tr>
                          <td className="p-1.5 border-r border-slate-300 font-medium">Volatile Matter</td>
                          <td className="p-1.5 border-r border-slate-300 text-right font-bold">28.5%</td>
                          <td className="p-1.5 border-r border-slate-300">IS 1350 (Part I)</td>
                          <td className="p-1.5 text-center text-emerald-800 font-semibold">Pass (25.0 – 32.0%)</td>
                        </tr>
                        <tr>
                          <td className="p-1.5 border-r border-slate-300 font-medium">Fixed Carbon</td>
                          <td className="p-1.5 border-r border-slate-300 text-right font-bold">40.5%</td>
                          <td className="p-1.5 border-r border-slate-300">By difference</td>
                          <td className="p-1.5 text-center text-emerald-800 font-semibold">Pass (&gt; 38.0%)</td>
                        </tr>
                        <tr className="bg-emerald-50/50">
                          <td className="p-1.5 border-r border-slate-300 font-bold text-slate-900">Gross Calorific Value (GCV)</td>
                          <td className="p-1.5 border-r border-slate-300 text-right font-bold text-emerald-900">5,420 kcal/kg</td>
                          <td className="p-1.5 border-r border-slate-300">Bomb Calorimeter</td>
                          <td className="p-1.5 text-center font-bold text-emerald-900">Grade G8 Verified</td>
                        </tr>
                        <tr>
                          <td className="p-1.5 border-r border-slate-300 font-medium">Total Sulfur</td>
                          <td className="p-1.5 border-r border-slate-300 text-right font-bold">0.48%</td>
                          <td className="p-1.5 border-r border-slate-300">Eschka Method</td>
                          <td className="p-1.5 text-center text-emerald-800 font-semibold">Low Sulfur (&lt; 0.80%)</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Section 4 & 5: Geotechnical & Production */}
                <div id="preview-sec-4" className="space-y-3">
                  <h2 className="text-base font-bold text-slate-900 border-b border-slate-200 pb-1.5 flex items-center justify-between">
                    <span>4.0 Geotechnical Slope Stability & Mine Production</span>
                    <span className="text-[10px] font-mono text-slate-500 font-normal">[EVID-003, EVID-004]</span>
                  </h2>
                  <p className="text-xs text-slate-700 leading-relaxed text-justify">
                    Geotechnical mapping of highwall bench #4 confirms competent sandstone overburden with Rock Mass Rating (RMR) of 68 (Good Rock). Calculated Factor of Safety is 1.42, exceeding the DGMS minimum threshold of 1.30. Monthly extraction telemetry indicates Run-of-Mine coal production of 245,000 MT/month with overburden removal of 680,000 m3/month (Stripping Ratio: 2.78 m3/MT).
                  </p>
                </div>

                {/* Section 6: Statutory Audit Assurance */}
                <div id="preview-sec-6" className="p-4 bg-slate-50 border border-slate-300 rounded text-[11px] leading-relaxed text-slate-700 space-y-1">
                  <div className="font-bold text-slate-900 flex items-center gap-1.5">
                    <ShieldCheck className="w-4 h-4 text-emerald-600" />
                    STATUTORY AUDITOR ASSURANCE & CRYPTOGRAPHIC LEDGER SIGN-OFF
                  </div>
                  <p>
                    All multi-source data streams were independently cross-referenced against original physical drill logs, certified NABL laboratory certificates, and electronic pit dispatch telemetry. Zero compliance non-conformances were detected. This autonomous evaluation is officially verified and certified for statutory corporate disclosure.
                  </p>
                </div>
              </div>

              {/* Document Running Footer */}
              <div className="border-t border-slate-300 pt-3 flex items-center justify-between text-[10px] text-slate-500 font-mono">
                <span>CONFIDENTIAL • MINING LEASE BLOCK ML-492 • STATUTORY DISCLOSURE ONLY</span>
                <span>MineIntel Verified • Page 1 of 1</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
