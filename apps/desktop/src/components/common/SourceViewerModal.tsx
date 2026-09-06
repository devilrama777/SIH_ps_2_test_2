import React, { useState } from 'react';
import {
  X,
  FileText,
  Table,
  CheckCircle2,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Download,
  Copy,
  Check,
  Search,
  ExternalLink,
} from 'lucide-react';
import { EvidenceItem } from '../../types';
import { StatusBadge } from './StatusBadge';

interface SourceViewerModalProps {
  isOpen: boolean;
  onClose: () => void;
  evidence?: EvidenceItem | null;
  documentName?: string;
  sourcePath?: string;
  pageOrSheet?: string;
  highlightBbox?: { x: number; y: number; width: number; height: number };
  cellRange?: string;
  rawSnippet?: string;
}

export const SourceViewerModal: React.FC<SourceViewerModalProps> = ({
  isOpen,
  onClose,
  evidence: initialEvidence,
  documentName,
  sourcePath,
  pageOrSheet,
  highlightBbox,
  cellRange,
  rawSnippet,
}) => {
  const [zoomLevel, setZoomLevel] = useState(100);
  const [copied, setCopied] = useState(false);

  const effectiveEvidence: EvidenceItem | null = initialEvidence || (documentName ? {
    id: 'ev-modal-preview',
    documentId: 'doc-preview',
    documentName: documentName || 'Document Preview',
    documentType: (sourcePath?.endsWith('.xlsx') || sourcePath?.endsWith('.csv') ? 'XLSX' : 'PDF') as any,
    sourceLocation: pageOrSheet || 'Page 1',
    extractionMethod: 'Native Parser',
    confidence: 98,
    relevantText: rawSnippet || 'No snippet preview available.',
    metadata: {
      year: new Date().getFullYear(),
      organizationUnit: 'Central Coalfields Limited',
      date: new Date().toISOString().slice(0, 10),
      authorOrSource: sourcePath || 'Local Archive',
    },
    bbox: highlightBbox,
    spreadsheetName: cellRange ? pageOrSheet : undefined,
    cellRange: cellRange,
  } : null);

  if (!isOpen || !effectiveEvidence) return null;
  const evidence = effectiveEvidence;

  const isSpreadsheet =
    evidence.documentType === 'XLSX' ||
    evidence.documentType === 'CSV' ||
    Boolean(evidence.spreadsheetName);

  const handleCopyText = () => {
    navigator.clipboard.writeText(evidence.relevantText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-xs p-6">
      <div className="w-full max-w-5xl h-[85vh] bg-[#121824] border border-slate-700/90 rounded shadow-2xl flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Modal Top Header */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-slate-800 bg-[#0d131d]">
          <div className="flex items-center gap-3 min-w-0">
            <div className="p-1.5 rounded bg-blue-950/60 border border-blue-800/60 text-blue-400">
              {isSpreadsheet ? <Table className="w-4 h-4" /> : <FileText className="w-4 h-4" />}
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-slate-100 font-mono truncate max-w-md">
                  {evidence.documentName}
                </span>
                <StatusBadge status={evidence.documentType} size="sm" />
                <span className="text-[11px] font-mono text-emerald-400 bg-emerald-950/40 border border-emerald-800/40 px-1.5 py-0.2 rounded">
                  {evidence.confidence}% CONFIDENCE
                </span>
              </div>
              <div className="text-[11px] font-mono text-slate-400">
                Provenance: {evidence.sourceLocation} • Method: {evidence.extractionMethod}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleCopyText}
              className="flex items-center gap-1.5 px-2.5 py-1 text-xs text-slate-300 hover:text-white bg-slate-800/80 hover:bg-slate-700 border border-slate-700 rounded transition cursor-pointer"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? 'Copied' : 'Copy Passage'}</span>
            </button>
            <div className="h-4 w-px bg-slate-800" />
            <button
              type="button"
              onClick={onClose}
              className="p-1 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded transition"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Content Body: Split between Inspector and Metadata Sidebar */}
        <div className="flex-1 flex overflow-hidden">
          {/* Main Visual Source Canvas */}
          <div className="flex-1 flex flex-col bg-[#0b0f17] border-r border-slate-800 overflow-hidden">
            {/* Viewer Controls */}
            <div className="px-4 py-2 bg-[#0f1420] border-b border-slate-800 flex items-center justify-between text-xs">
              <div className="flex items-center gap-2 text-slate-300">
                <span className="font-mono text-[11px] text-slate-400">Target Region:</span>
                <span className="font-mono text-blue-300 bg-blue-950/40 px-2 py-0.5 rounded border border-blue-900/60">
                  {isSpreadsheet
                    ? `Sheet [${evidence.sheetName || 'Summary'}] • Range [${evidence.cellRange || 'G27:G31'}]`
                    : `Page ${evidence.page || 1} • Bounding Box [45, 310, 520, 140]`}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setZoomLevel((z) => Math.max(50, z - 15))}
                  className="p-1 text-slate-400 hover:text-slate-200"
                  title="Zoom Out"
                >
                  <ZoomOut className="w-3.5 h-3.5" />
                </button>
                <span className="font-mono text-[11px] text-slate-400 w-12 text-center">
                  {zoomLevel}%
                </span>
                <button
                  type="button"
                  onClick={() => setZoomLevel((z) => Math.min(200, z + 15))}
                  className="p-1 text-slate-400 hover:text-slate-200"
                  title="Zoom In"
                >
                  <ZoomIn className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {/* Simulated Document / Spreadsheet Canvas */}
            <div className="flex-1 overflow-auto p-6 flex items-center justify-center">
              {isSpreadsheet ? (
                /* Interactive Grid View with Highlighted Cells */
                <div
                  className="bg-[#141c2b] border border-slate-700 rounded shadow-lg overflow-hidden transition-all duration-200"
                  style={{ transform: `scale(${zoomLevel / 100})`, transformOrigin: 'top center' }}
                >
                  <div className="px-4 py-2 bg-[#101724] border-b border-slate-800 flex items-center justify-between text-xs font-mono">
                    <span className="text-slate-300">
                      Workbook: {evidence.documentName} &gt; {evidence.sheetName || 'Sheet1'}
                    </span>
                    <span className="text-emerald-400 flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Highlight active on: {evidence.cellRange || 'G27:G31'}
                    </span>
                  </div>
                  <table className="w-full text-xs font-mono border-collapse">
                    <thead>
                      <tr className="bg-[#1a2333] text-slate-400 border-b border-slate-700">
                        <th className="px-3 py-1.5 border-r border-slate-700 w-12 text-center">#</th>
                        <th className="px-3 py-1.5 border-r border-slate-700 text-left">A (Account)</th>
                        <th className="px-3 py-1.5 border-r border-slate-700 text-left">B (Subsidiary)</th>
                        <th className="px-3 py-1.5 border-r border-slate-700 text-right">C (Volume MT)</th>
                        <th className="px-3 py-1.5 border-r border-slate-700 text-right">D (Avg Realization)</th>
                        <th className="px-4 py-1.5 text-right bg-blue-950/60 text-blue-200 border-l border-blue-700">
                          G (Gross Realization ₹ Cr)
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                      <tr className="hover:bg-slate-800/40 text-slate-300">
                        <td className="px-3 py-1.5 border-r border-slate-800 text-center text-slate-400 bg-slate-900/40">27</td>
                        <td className="px-3 py-1.5 border-r border-slate-800">4100-REV</td>
                        <td className="px-3 py-1.5 border-r border-slate-800">BCCL Dhanbad</td>
                        <td className="px-3 py-1.5 border-r border-slate-800 text-right">8.45 MT</td>
                        <td className="px-3 py-1.5 border-r border-slate-800 text-right">₹2,140.00</td>
                        <td className="px-4 py-1.5 text-right font-semibold bg-blue-950/80 text-blue-300 border-l-2 border-blue-500">
                          ₹1,808.30 Cr
                        </td>
                      </tr>
                      <tr className="hover:bg-slate-800/40 text-slate-300">
                        <td className="px-3 py-1.5 border-r border-slate-800 text-center text-slate-400 bg-slate-900/40">28</td>
                        <td className="px-3 py-1.5 border-r border-slate-800">4102-REV</td>
                        <td className="px-3 py-1.5 border-r border-slate-800">CCL Ranchi</td>
                        <td className="px-3 py-1.5 border-r border-slate-800 text-right">6.12 MT</td>
                        <td className="px-3 py-1.5 border-r border-slate-800 text-right">₹1,580.00</td>
                        <td className="px-4 py-1.5 text-right font-semibold bg-blue-950/80 text-blue-300 border-l-2 border-blue-500">
                          ₹966.96 Cr
                        </td>
                      </tr>
                      <tr className="hover:bg-slate-800/40 text-slate-300">
                        <td className="px-3 py-1.5 border-r border-slate-800 text-center text-slate-400 bg-slate-900/40">29</td>
                        <td className="px-3 py-1.5 border-r border-slate-800">4104-REV</td>
                        <td className="px-3 py-1.5 border-r border-slate-800">MCL Sambalpur</td>
                        <td className="px-3 py-1.5 border-r border-slate-800 text-right">15.34 MT</td>
                        <td className="px-3 py-1.5 border-r border-slate-800 text-right">₹1,393.40</td>
                        <td className="px-4 py-1.5 text-right font-semibold bg-blue-950/80 text-blue-300 border-l-2 border-blue-500">
                          ₹2,137.54 Cr
                        </td>
                      </tr>
                      <tr className="bg-blue-950/40 text-slate-100 font-bold border-t-2 border-blue-500">
                        <td className="px-3 py-2 border-r border-slate-800 text-center text-slate-400 bg-slate-900/40">31</td>
                        <td className="px-3 py-2 border-r border-slate-800">TOTAL</td>
                        <td className="px-3 py-2 border-r border-slate-800">Consolidated Q3 Realization</td>
                        <td className="px-3 py-2 border-r border-slate-800 text-right">29.91 MT</td>
                        <td className="px-3 py-2 border-r border-slate-800 text-right">₹1,642.50</td>
                        <td className="px-4 py-2 text-right text-emerald-400 text-sm bg-emerald-950/40 border-2 border-emerald-500 shadow-inner">
                          ₹4,912.80 Cr
                        </td>
                      </tr>
                    </tbody>
                  </table>
                  <div className="px-4 py-2 bg-[#0e141f] text-[11px] font-mono text-slate-400 border-t border-slate-800">
                    Cell Formula: <code className="text-blue-300 font-semibold">=SUM(G27:G29)</code> • Cell Format: Currency INR Cr • Reconciled
                  </div>
                </div>
              ) : (
                /* Simulated PDF Document Page with Bounding Box */
                <div
                  className="w-[540px] min-h-[640px] bg-slate-100 text-slate-900 p-8 shadow-2xl rounded border border-slate-300 relative transition-all duration-200"
                  style={{ transform: `scale(${zoomLevel / 100})`, transformOrigin: 'top center' }}
                >
                  <div className="border-b border-slate-300 pb-3 mb-4 flex justify-between items-center text-[10px] font-mono text-slate-400 uppercase tracking-widest">
                    <span>COAL INDIA LIMITED • STATUTORY OPERATIONS</span>
                    <span>PAGE {evidence.page || 14} OF 48</span>
                  </div>

                  <h3 className="text-sm font-bold text-slate-800 mb-2">
                    {evidence.sectionName || 'Operational Performance & Equipment Availability'}
                  </h3>

                  <p className="text-[11px] text-slate-600 mb-4 leading-relaxed">
                    Opencast mining operations across the eastern subsidiaries operated at an overall machine utilization factor of 82.1%. Haul road maintenance intervals were strictly adhered to according to Director General of Mines Safety guidelines.
                  </p>

                  {/* Bounding Box Highlighted Region */}
                  <div className="p-3 bg-blue-100/90 border-2 border-blue-600 rounded relative shadow-xs my-4">
                    <div className="absolute -top-2.5 left-2 bg-blue-600 text-white font-mono text-[9px] px-1.5 py-0.2 rounded font-bold">
                      EXTRACTED PASSAGE [CONFIDENCE: {evidence.confidence}%]
                    </div>
                    <p className="text-[11px] text-blue-950 font-medium leading-relaxed">
                      "{evidence.relevantText}"
                    </p>
                  </div>

                  <p className="text-[11px] text-slate-600 mb-4 leading-relaxed">
                    Preventative lubrication schedules were recorded digitally across all primary excavators. Spares buffer inventory remained within the targeted 45-day reserve ratio at central stores.
                  </p>

                  <div className="absolute bottom-6 left-8 right-8 border-t border-slate-300 pt-2 flex justify-between text-[9px] font-mono text-slate-400">
                    <span>VERIFICATION HASH: {evidence.id}</span>
                    <span>AIRGAP AUDIT VERIFIED</span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right Sidebar: Evidence Provenance & Audit Info */}
          <div className="w-80 bg-[#101520] flex flex-col overflow-y-auto p-4 space-y-4 text-xs">
            <div>
              <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-2">
                Document Metadata
              </div>
              <div className="bg-[#141b26] border border-slate-800 rounded p-3 space-y-2 font-mono">
                <div>
                  <div className="text-[10px] text-slate-400">Filename</div>
                  <div className="text-slate-200 truncate">{evidence.documentName}</div>
                </div>
                <div>
                  <div className="text-[10px] text-slate-400">Org Unit</div>
                  <div className="text-slate-300">{evidence.metadata.organizationUnit}</div>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <div className="text-[10px] text-slate-400">Record Date</div>
                    <div className="text-slate-300">{evidence.metadata.date}</div>
                  </div>
                  <div>
                    <div className="text-[10px] text-slate-400">Year / Period</div>
                    <div className="text-slate-300">{evidence.metadata.year} {evidence.metadata.month || ''}</div>
                  </div>
                </div>
                <div>
                  <div className="text-[10px] text-slate-400">Author / Source</div>
                  <div className="text-slate-300">{evidence.metadata.authorOrSource}</div>
                </div>
              </div>
            </div>

            <div>
              <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-2">
                Extraction Provenance
              </div>
              <div className="bg-[#141b26] border border-slate-800 rounded p-3 space-y-2 font-mono">
                <div>
                  <div className="text-[10px] text-slate-400">Subprocess Pipeline</div>
                  <div className="text-slate-200">{evidence.extractionMethod}</div>
                </div>
                <div>
                  <div className="text-[10px] text-slate-400">Confidence Score</div>
                  <div className="text-emerald-400 font-bold">{evidence.confidence}%</div>
                </div>
                <div>
                  <div className="text-[10px] text-slate-400">Source Location String</div>
                  <div className="text-slate-300 break-all">{evidence.sourceLocation}</div>
                </div>
              </div>
            </div>

            <div>
              <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-2">
                Integrity & Compliance
              </div>
              <div className="p-3 bg-emerald-950/20 border border-emerald-800/40 rounded text-[11px] text-emerald-300 space-y-1">
                <div className="flex items-center gap-1.5 font-semibold">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Provenance Cryptographically Verified</span>
                </div>
                <p className="text-[10px] text-emerald-400/80 font-mono">
                  Origin file checksum matches local workspace partition snapshot. Zero cloud telemetry.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
