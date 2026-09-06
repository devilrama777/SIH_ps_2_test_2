import React, { useState } from 'react';
import {
  FileText,
  ChevronLeft,
  ChevronRight,
  ZoomIn,
  ZoomOut,
  Search,
  Bookmark,
  Printer,
  Download,
  Sliders,
  Maximize2,
  CheckCircle2,
  BookOpen,
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
  const [currentPage, setCurrentPage] = useState<number>(2);
  const totalPages = 14;
  const [zoomLevel, setZoomLevel] = useState<number>(100);
  const [designStyle, setDesignStyle] = useState<'reference' | 'modern'>('reference');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [showBookmarks, setShowBookmarks] = useState<boolean>(false);

  const handleZoom = (delta: number) => {
    setZoomLevel((prev) => Math.min(175, Math.max(60, prev + delta)));
  };

  return (
    <div className="flex-1 overflow-hidden flex flex-col bg-[#0b0f17]">
      {/* Top Preview Control Bar */}
      <div className="h-12 bg-[#121824] border-b border-[#1f2b3d] px-4 flex items-center justify-between text-xs select-none shrink-0">
        <div className="flex items-center gap-3">
          <span className="font-mono font-bold text-slate-200">
            PDF Document Preview
          </span>
          <div className="h-4 w-px bg-slate-700" />
          {/* Design Style Switcher */}
          <div className="flex items-center bg-slate-900 border border-slate-700 rounded p-0.5 font-mono text-[11px]">
            <button
              type="button"
              onClick={() => setDesignStyle('reference')}
              className={`px-2.5 py-1 rounded transition cursor-pointer ${
                designStyle === 'reference'
                  ? 'bg-blue-600 text-white font-semibold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Reference-Inspired (Statutory)
            </button>
            <button
              type="button"
              onClick={() => setDesignStyle('modern')}
              className={`px-2.5 py-1 rounded transition cursor-pointer ${
                designStyle === 'modern'
                  ? 'bg-blue-600 text-white font-semibold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Modern Corporate Minimalist
            </button>
          </div>
        </div>

        {/* Page & Zoom Navigation */}
        <div className="flex items-center gap-4">
          {/* Search */}
          <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-700 rounded px-2 py-1">
            <Search className="w-3.5 h-3.5 text-slate-400" />
            <input
              type="text"
              placeholder="Find in preview..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-transparent text-slate-200 placeholder-slate-500 text-[11px] font-mono focus:outline-none w-28"
            />
          </div>

          {/* Page Paging */}
          <div className="flex items-center gap-1 font-mono text-xs text-slate-300">
            <button
              type="button"
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="p-1 rounded hover:bg-slate-800 disabled:opacity-40"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span>
              Page <strong className="text-white">{currentPage}</strong> of {totalPages}
            </span>
            <button
              type="button"
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="p-1 rounded hover:bg-slate-800 disabled:opacity-40"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          {/* Zoom */}
          <div className="flex items-center gap-1 font-mono text-xs text-slate-300">
            <button
              type="button"
              onClick={() => handleZoom(-15)}
              className="p-1 rounded hover:bg-slate-800"
              title="Zoom Out"
            >
              <ZoomOut className="w-3.5 h-3.5" />
            </button>
            <span className="w-12 text-center text-[11px]">{zoomLevel}%</span>
            <button
              type="button"
              onClick={() => handleZoom(15)}
              className="p-1 rounded hover:bg-slate-800"
              title="Zoom In"
            >
              <ZoomIn className="w-3.5 h-3.5" />
            </button>
          </div>

          <button
            type="button"
            onClick={onNavigateToExport}
            className="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded font-mono text-xs transition flex items-center gap-1.5 cursor-pointer shadow-sm"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export Final PDF</span>
          </button>
        </div>
      </div>

      {/* Main Preview Container */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Thumbnails & Bookmarks Pane */}
        <div className="w-56 bg-[#0f141f] border-r border-[#1f2b3d] flex flex-col shrink-0 select-none">
          <div className="p-2.5 border-b border-[#1f2b3d] bg-[#111722] flex items-center justify-between text-[11px] font-mono text-slate-400">
            <span>PAGE THUMBNAILS</span>
            <span>{totalPages} PGS</span>
          </div>

          <div className="flex-1 overflow-y-auto p-3 space-y-3">
            {[1, 2, 3, 4, 5, 6].map((pg) => {
              const isSelected = pg === currentPage;
              return (
                <div
                  key={pg}
                  onClick={() => setCurrentPage(pg)}
                  className={`cursor-pointer rounded p-1.5 text-center transition ${
                    isSelected
                      ? 'bg-blue-950/40 ring-2 ring-blue-500'
                      : 'bg-slate-900/40 hover:bg-slate-800/40 border border-slate-800'
                  }`}
                >
                  <div className="h-28 bg-[#fdfdfd] rounded shadow-sm text-[6px] text-slate-700 p-2 overflow-hidden flex flex-col justify-between select-none">
                    <div className="border-b border-slate-300 pb-1 font-bold">
                      COAL INDIA LIMITED • STATUTORY REPORT
                    </div>
                    <div className="space-y-1">
                      <div className="h-1 bg-slate-300 rounded w-3/4" />
                      <div className="h-1 bg-slate-200 rounded w-full" />
                      <div className="h-1 bg-slate-200 rounded w-5/6" />
                      <div className="h-6 bg-slate-100 rounded border border-slate-300 my-1" />
                    </div>
                    <div className="text-[5px] text-slate-400 text-right">Pg. {pg}</div>
                  </div>
                  <div className="mt-1 text-[10px] font-mono text-slate-400">
                    Page {pg} {pg === 2 && '• Financial Review'}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Center Canvas: Physical Document Simulation */}
        <div className="flex-1 overflow-y-auto p-8 flex justify-center bg-[#070a0f]">
          <div
            style={{ transform: `scale(${zoomLevel / 100})`, transformOrigin: 'top center' }}
            className="transition-transform duration-100 ease-out"
          >
            {/* The White A4 Paper Sheet */}
            <div
              className={`w-[794px] min-h-[1123px] bg-white text-slate-900 shadow-2xl p-14 flex flex-col justify-between select-text ${
                designStyle === 'reference' ? 'font-serif' : 'font-sans'
              }`}
            >
              {/* Running Header */}
              <div className="border-b border-slate-300 pb-3 flex items-center justify-between text-[11px] text-slate-500 font-mono uppercase tracking-wider">
                <span>MineIntel • AI Powered Report Generator Program</span>
                <span>Statutory Review Q4 FY26</span>
              </div>

              {/* Page Body Content */}
              <div className="space-y-6 py-6 flex-1">
                {/* Chapter Title */}
                <div>
                  <div className="text-xs font-mono font-bold text-blue-900 uppercase tracking-widest mb-1">
                    Section 4.0
                  </div>
                  <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
                    Financial Performance & Realized Sales Turnover
                  </h1>
                  <p className="text-xs text-slate-500 font-mono mt-1">
                    Audited under DGMS and statutory corporate disclosure regulations.
                  </p>
                </div>

                {/* Sub-Section 4.1 */}
                <div className="space-y-3">
                  <h2 className="text-base font-bold text-slate-800">
                    4.1 Turnover, FSA Realizations & E-Auction Premiums
                  </h2>
                  <p className="text-xs text-slate-700 leading-relaxed">
                    During the fourth quarter of FY26, consolidated gross operational turnover from raw coal off-take and washed beneficiation reached ₹4,912.80 Crore, representing an increase of +1.9% against internal quarterly projections. Fuel Supply Agreement (FSA) despatches accounted for 81.4% of total volume off-take to critical pithead thermal power generators.
                  </p>
                </div>

                {/* Statutory Table 4.1.1 */}
                <div className="space-y-1.5">
                  <div className="text-[11px] font-mono font-bold text-slate-800 uppercase">
                    Table 4.1.1: Subsidiary-Wise Turnover Realization (Audited Q4 FY26 vs Q4 FY25)
                  </div>
                  <table className="w-full text-[11px] font-mono border border-slate-300 border-collapse">
                    <thead>
                      <tr className="bg-slate-100 text-slate-800 border-b border-slate-300 font-bold">
                        <th className="p-2 text-left border-r border-slate-300">Subsidiary / Command</th>
                        <th className="p-2 text-right border-r border-slate-300">Turnover (₹ Cr)</th>
                        <th className="p-2 text-right border-r border-slate-300">Growth (% YoY)</th>
                        <th className="p-2 text-right">Provenance Citation</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200 text-slate-700">
                      <tr>
                        <td className="p-2 border-r border-slate-300">Northern Coalfields Limited (NCL)</td>
                        <td className="p-2 text-right border-r border-slate-300 font-bold">₹1,940.20</td>
                        <td className="p-2 text-right border-r border-slate-300 text-emerald-700">+8.4%</td>
                        <td className="p-2 text-right text-[10px] text-slate-500">NCL_Q4_Audit.pdf #p12</td>
                      </tr>
                      <tr>
                        <td className="p-2 border-r border-slate-300">South Eastern Coalfields (SECL)</td>
                        <td className="p-2 text-right border-r border-slate-300 font-bold">₹1,620.10</td>
                        <td className="p-2 text-right border-r border-slate-300 text-emerald-700">+5.1%</td>
                        <td className="p-2 text-right text-[10px] text-slate-500">SECL_Ledger.xlsx #C4</td>
                      </tr>
                      <tr>
                        <td className="p-2 border-r border-slate-300">Mahanadi Coalfields Limited (MCL)</td>
                        <td className="p-2 text-right border-r border-slate-300 font-bold">₹1,352.50</td>
                        <td className="p-2 text-right border-r border-slate-300 text-emerald-700">+11.2%</td>
                        <td className="p-2 text-right text-[10px] text-slate-500">MCL_Dispatch.csv #r88</td>
                      </tr>
                      <tr className="bg-slate-50 font-bold text-slate-900 border-t-2 border-slate-400">
                        <td className="p-2 border-r border-slate-300">Total Consolidated Turnover</td>
                        <td className="p-2 text-right border-r border-slate-300">₹4,912.80</td>
                        <td className="p-2 text-right border-r border-slate-300 text-emerald-700">+7.9%</td>
                        <td className="p-2 text-right text-[10px] text-blue-800">Reconciled Verified</td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                {/* Audit Assurance Box */}
                <div className="p-3 bg-slate-50 border border-slate-300 rounded text-[11px] leading-relaxed text-slate-700">
                  <span className="font-bold text-slate-900">STATUTORY AUDITOR ASSURANCE: </span>
                  All figures reconciled against physical commercial invoices and electronic railway freight receipts (e-RR). Un-reconciled variance across all subsidiaries is bounded below 0.001%.
                </div>
              </div>

              {/* Running Footer */}
              <div className="border-t border-slate-300 pt-3 flex items-center justify-between text-[10px] text-slate-500 font-mono">
                <span>CONFIDENTIAL • FOR STATUTORY FILING ONLY</span>
                <span>Page {currentPage} of {totalPages}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
