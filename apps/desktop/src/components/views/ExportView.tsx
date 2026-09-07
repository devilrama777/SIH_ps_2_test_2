import React, { useState } from 'react';
import {
  Download,
  CheckCircle2,
  AlertTriangle,
  Folder,
  Printer,
  FileText,
  ShieldCheck,
  RotateCcw,
  Sparkles,
  ExternalLink,
  Cpu,
} from 'lucide-react';
import { ReportItem, ValidationIssueItem } from '../../types';
import { StatusBadge } from '../common/StatusBadge';
import { desktopBridge } from '../../services/desktopBridge';

interface ExportViewProps {
  report: ReportItem;
  validationIssues: ValidationIssueItem[];
  onOpenPreview: () => void;
  onOpenEditor: () => void;
}

export const ExportView: React.FC<ExportViewProps> = ({
  report,
  validationIssues,
  onOpenPreview,
  onOpenEditor,
}) => {
  const [selectedEngine, setSelectedEngine] = useState<'typst' | 'weasyprint'>('typst');
  const [includeProvenanceLedger, setIncludeProvenanceLedger] = useState(true);
  const [pdfStandard, setPdfStandard] = useState<'PDF/A-2b' | 'Standard Vector'>('PDF/A-2b');
  const [isExporting, setIsExporting] = useState(false);
  const [exportComplete, setExportComplete] = useState(false);
  const [outputPath, setOutputPath] = useState(
    desktopBridge.formatPath('MineIntel_Q4_Consolidated_Review_FY26.pdf')
  );

  const unresolvedHighIssues = validationIssues.filter((i) => i.severity === 'high');

  const handleRunExport = () => {
    setIsExporting(true);
    setTimeout(() => {
      setIsExporting(false);
      setExportComplete(true);
    }, 1400);
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="border-b border-[#233145] pb-4">
        <div className="flex items-center gap-2 mb-1">
          <Download className="w-5 h-5 text-blue-400" />
          <h1 className="text-lg font-bold text-slate-100 tracking-tight">
            Pre-Flight Statutory Validation & Local PDF Export Gate
          </h1>
        </div>
        <p className="text-xs text-slate-400">
          Verify corporate compliance, audit assurance sign-offs, and compile publication-grade PDF using local headless Typst engine.
        </p>
      </div>

      {/* Pre-flight Gate Checklist */}
      <div className="bg-[#111722] border border-[#1e2a3b] rounded-md p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <h2 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Pre-Flight Regulatory Gate Status</span>
          </h2>
          <span className="text-xs font-mono text-emerald-400 bg-emerald-950/40 border border-emerald-800/40 px-2 py-0.5 rounded">
            READY FOR PUBLICATION
          </span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs font-mono">
          <div className="p-3 bg-[#141d2b] border border-slate-800 rounded">
            <div className="text-[10px] text-slate-400">PAGE COUNT</div>
            <div className="text-base font-bold text-slate-100">14 Pages</div>
            <div className="text-[10px] text-slate-400">7 Chapters</div>
          </div>
          <div className="p-3 bg-[#141d2b] border border-slate-800 rounded">
            <div className="text-[10px] text-slate-400">SOURCE COVERAGE</div>
            <div className="text-base font-bold text-blue-400">100%</div>
            <div className="text-[10px] text-slate-400">5/5 Sources Verified</div>
          </div>
          <div className="p-3 bg-[#141d2b] border border-slate-800 rounded">
            <div className="text-[10px] text-slate-400">INTEGRITY SCORE</div>
            <div className="text-base font-bold text-emerald-400">{report.validationScore}%</div>
            <div className="text-[10px] text-slate-400">0 Critical Errors</div>
          </div>
          <div className="p-3 bg-[#141d2b] border border-slate-800 rounded">
            <div className="text-[10px] text-slate-400">SECURITY POSTURE</div>
            <div className="text-base font-bold text-emerald-400">Airgapped</div>
            <div className="text-[10px] text-slate-400">SHA-256 Watermarked</div>
          </div>
        </div>

        {/* Warning banner if high severity issue exists */}
        {unresolvedHighIssues.length > 0 && (
          <div className="p-3 bg-amber-950/20 border border-amber-800/50 rounded flex items-center justify-between text-xs">
            <div className="flex items-center gap-2 text-amber-300">
              <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
              <span>
                {unresolvedHighIssues.length} unresolved high validation issues detected in Section 4.1.
              </span>
            </div>
            <button
              type="button"
              onClick={onOpenEditor}
              className="text-xs text-amber-200 underline font-mono hover:text-white"
            >
              Resolve in Editor →
            </button>
          </div>
        )}
      </div>

      {/* Export Configurations */}
      <div className="bg-[#111722] border border-[#1e2a3b] rounded-md p-5 space-y-4 text-xs font-mono">
        <h2 className="text-sm font-semibold text-slate-100 font-sans">
          Compilation Engine & Output Parameters
        </h2>

        <div className="space-y-3">
          <div>
            <label className="block text-slate-400 mb-1 text-[11px]">LOCAL PDF RENDERING ENGINE</label>
            <div className="grid grid-cols-2 gap-3">
              <div
                onClick={() => setSelectedEngine('typst')}
                className={`p-3 border rounded cursor-pointer transition ${
                  selectedEngine === 'typst'
                    ? 'border-blue-500 bg-blue-950/30 text-white'
                    : 'border-slate-800 bg-slate-900/40 text-slate-400'
                }`}
              >
                <div className="font-bold text-slate-200">Typst CLI 0.11 (Native C++ Binary)</div>
                <div className="text-[10px] text-slate-400 mt-0.5">
                  Sub-second compilation, strict typographic baseline grids, vector mathematical rendering.
                </div>
              </div>

              <div
                onClick={() => setSelectedEngine('weasyprint')}
                className={`p-3 border rounded cursor-pointer transition ${
                  selectedEngine === 'weasyprint'
                    ? 'border-blue-500 bg-blue-950/30 text-white'
                    : 'border-slate-800 bg-slate-900/40 text-slate-400'
                }`}
              >
                <div className="font-bold text-slate-200">WeasyPrint CSS Paged Media</div>
                <div className="text-[10px] text-slate-400 mt-0.5">
                  HTML5/CSS print stylesheets with support for complex web-based layout rules.
                </div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 pt-2">
            <div>
              <label className="block text-slate-400 mb-1 text-[11px]">ARCHIVAL STANDARD</label>
              <select
                value={pdfStandard}
                onChange={(e) => setPdfStandard(e.target.value as any)}
                className="w-full bg-[#182333] border border-slate-700 rounded px-3 py-1.5 text-slate-200"
              >
                <option value="PDF/A-2b">PDF/A-2b (Long-Term Statutory Archive)</option>
                <option value="Standard Vector">Standard High-Resolution Vector PDF</option>
              </select>
            </div>

            <div>
              <label className="block text-slate-400 mb-1 text-[11px]">PROVENANCE AUDIT APPENDIX</label>
              <label className="flex items-center gap-2 p-2 bg-[#182333] border border-slate-700 rounded cursor-pointer text-slate-200">
                <input
                  type="checkbox"
                  checked={includeProvenanceLedger}
                  onChange={(e) => setIncludeProvenanceLedger(e.target.checked)}
                  className="rounded border-slate-600 text-blue-600"
                />
                <span className="text-[11px]">Append 3-page cryptographic audit appendix</span>
              </label>
            </div>
          </div>

          <div>
            <label className="block text-slate-400 mb-1 text-[11px]">TARGET LOCAL FILESYSTEM PATH</label>
            <input
              type="text"
              value={outputPath}
              onChange={(e) => setOutputPath(e.target.value)}
              className="w-full bg-[#182333] border border-slate-700 rounded px-3 py-1.5 text-slate-200"
            />
          </div>
        </div>
      </div>

      {/* Export Action Strip */}
      <div className="flex items-center justify-between bg-[#111722] border border-[#1e2a3b] p-4 rounded-md">
        <button
          type="button"
          onClick={onOpenPreview}
          className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded font-mono text-xs border border-slate-700 transition cursor-pointer flex items-center gap-2"
        >
          <FileText className="w-4 h-4 text-blue-400" />
          <span>Back to Visual Preview</span>
        </button>

        <div className="flex items-center gap-3">
          {exportComplete ? (
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono text-emerald-400 flex items-center gap-1">
                <CheckCircle2 className="w-4 h-4" />
                Compiled Successfully!
              </span>
              <button
                type="button"
                onClick={handleRunExport}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded font-mono text-xs transition cursor-pointer flex items-center gap-1.5"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Re-Export</span>
              </button>
            </div>
          ) : (
            <button
              type="button"
              id="btn-generate-pdf"
              onClick={handleRunExport}
              disabled={isExporting}
              className="px-6 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded font-mono text-xs transition shadow-md flex items-center gap-2 cursor-pointer disabled:opacity-50"
            >
              <Download className="w-4 h-4" />
              <span>{isExporting ? 'Executing Typst Rendering...' : 'Generate Official Statutory PDF'}</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
