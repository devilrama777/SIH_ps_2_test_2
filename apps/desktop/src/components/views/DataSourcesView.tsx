import React, { useState } from 'react';
import {
  FolderArchive,
  Plus,
  RefreshCw,
  Trash2,
  Eye,
  Search,
  Filter,
  FileText,
  Table,
  Image as ImageIcon,
  CheckCircle2,
  AlertCircle,
  Clock,
  HardDrive,
  Upload,
  FolderOpen,
} from 'lucide-react';
import { DataSourceItem } from '../../types';
import { StatusBadge } from '../common/StatusBadge';
import { desktopBridge } from '../../services/desktopBridge';

interface DataSourcesViewProps {
  dataSources: DataSourceItem[];
  onAddSource: (fileData: Partial<DataSourceItem>) => void;
  onRemoveSource: (id: string) => void;
  onReprocessSource: (id: string) => void;
  onViewSource: (doc: DataSourceItem) => void;
}

export const DataSourcesView: React.FC<DataSourcesViewProps> = ({
  dataSources,
  onAddSource,
  onRemoveSource,
  onReprocessSource,
  onViewSource,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTypeFilter, setSelectedTypeFilter] = useState<string>('All');
  const [showAddModal, setShowAddModal] = useState(false);

  // New source form state
  const [newFilename, setNewFilename] = useState('');
  const [newType, setNewType] = useState<DataSourceItem['type']>('PDF');
  const [newSourcePath, setNewSourcePath] = useState('/data/local_repos/finance/');
  const [newPages, setNewPages] = useState(16);

  const filteredSources = dataSources.filter((doc) => {
    const matchesSearch =
      doc.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.sourcePath.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType =
      selectedTypeFilter === 'All' || doc.type === selectedTypeFilter;
    return matchesSearch && matchesType;
  });

  const handleBrowseNativeFilesystem = async () => {
    const res = await desktopBridge.openNativeFileDialog();
    if (!res.cancelled && res.fileName && res.filePath) {
      setNewFilename(res.fileName);
      setNewSourcePath(res.filePath);
      setShowAddModal(true);
    }
  };

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newFilename.trim()) return;
    onAddSource({
      filename: newFilename,
      type: newType,
      sourcePath: `${newSourcePath}${newFilename}`,
      pages: newPages,
      sizeBytes: Math.floor(Math.random() * 8000000) + 1200000,
      summary: 'Ingested local organizational file registered for evidence extraction.',
    });
    setNewFilename('');
    setShowAddModal(false);
  };

  const types = ['All', 'PDF', 'Scanned PDF', 'DOCX', 'XLSX', 'CSV', 'Images', 'TXT'];

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-5">
      {/* Header & Metric Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#233145] pb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <FolderArchive className="w-5 h-5 text-blue-400" />
            <h1 className="text-lg font-bold text-slate-100 tracking-tight">
              Local Data Repositories & Ingested Corpus
            </h1>
          </div>
          <p className="text-xs text-slate-400">
            Ingest and index corporate PDFs, scanned documents, Excel sheets, and CSV ledgers from local partitions.
          </p>
        </div>

        <div className="flex items-center gap-2 self-start md:self-auto">
          <button
            type="button"
            onClick={handleBrowseNativeFilesystem}
            className="px-3 py-2 text-xs font-semibold text-slate-200 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded transition shadow-sm flex items-center gap-2 cursor-pointer"
            title="Open Native OS File Dialog (Linux/macOS/Windows)"
          >
            <FolderOpen className="w-4 h-4 text-blue-400" />
            <span>Browse OS Filesystem...</span>
          </button>
          <button
            type="button"
            onClick={() => setShowAddModal(true)}
            className="px-4 py-2 text-xs font-bold text-white bg-blue-600 hover:bg-blue-500 rounded transition shadow-sm flex items-center gap-2 cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>Manual Register</span>
          </button>
        </div>
      </div>

      {/* Filter and Search Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-[#111722] border border-[#1e2a3b] p-3 rounded-md text-xs">
        <div className="flex items-center gap-2 flex-1 min-w-[260px] max-w-md">
          <Search className="w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by filename or file path..."
            className="w-full bg-slate-900/80 border border-slate-700/80 rounded px-2.5 py-1.5 text-slate-200 placeholder-slate-400 focus:outline-none focus:border-blue-500 font-mono text-xs"
          />
        </div>

        <div className="flex items-center gap-1 overflow-x-auto">
          <span className="text-slate-400 text-[11px] font-mono mr-1">Type:</span>
          {types.map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => setSelectedTypeFilter(t)}
              className={`px-2 py-1 rounded text-[11px] font-mono transition cursor-pointer ${
                selectedTypeFilter === t
                  ? 'bg-blue-600 text-white font-semibold'
                  : 'bg-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-700'
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Main Table */}
      <div className="bg-[#111722] border border-[#1e2a3b] rounded-md overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left border-collapse">
            <thead>
              <tr className="bg-[#141d2b] text-slate-400 border-b border-[#1e2a3b] font-mono uppercase text-[10px] tracking-wider">
                <th className="py-2.5 px-4">Filename / Hash</th>
                <th className="py-2.5 px-3">Format</th>
                <th className="py-2.5 px-3">Size</th>
                <th className="py-2.5 px-3">Pages / Tables</th>
                <th className="py-2.5 px-3">OCR Status</th>
                <th className="py-2.5 px-3">Index State</th>
                <th className="py-2.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#182333]">
              {filteredSources.map((doc) => (
                <tr key={doc.id} className="hover:bg-[#141c2a] transition">
                  <td className="py-3 px-4">
                    <div className="font-semibold text-slate-200 font-mono flex items-center gap-2">
                      <FileText className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                      <span className="truncate max-w-sm">{doc.filename}</span>
                    </div>
                    <div className="text-[11px] font-mono text-slate-400 truncate max-w-md mt-0.5">
                      {doc.sourcePath}
                    </div>
                  </td>

                  <td className="py-3 px-3">
                    <StatusBadge status={doc.type} size="sm" />
                  </td>

                  <td className="py-3 px-3 font-mono text-slate-300">
                    {(doc.sizeBytes / 1024 / 1024).toFixed(2)} MB
                  </td>

                  <td className="py-3 px-3 font-mono text-slate-300">
                    <div>{doc.pages} pages</div>
                    <div className="text-[10px] text-slate-400">
                      {doc.extractedTablesCount} tables • {doc.extractedImagesCount} images
                    </div>
                  </td>

                  <td className="py-3 px-3">
                    <StatusBadge status={doc.ocrStatus} size="sm" />
                  </td>

                  <td className="py-3 px-3">
                    <StatusBadge status={doc.indexedStatus} size="sm" />
                  </td>

                  <td className="py-3 px-4 text-right">
                    <div className="flex items-center justify-end gap-1.5">
                      <button
                        type="button"
                        onClick={() => onViewSource(doc)}
                        className="p-1.5 text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded transition"
                        title="View Document & Extraction Region"
                      >
                        <Eye className="w-3.5 h-3.5" />
                      </button>
                      <button
                        type="button"
                        onClick={() => onReprocessSource(doc.id)}
                        className="p-1.5 text-slate-300 hover:text-blue-300 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded transition"
                        title="Reprocess & Re-extract"
                      >
                        <RefreshCw className="w-3.5 h-3.5" />
                      </button>
                      <button
                        type="button"
                        onClick={() => onRemoveSource(doc.id)}
                        className="p-1.5 text-slate-300 hover:text-rose-300 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded transition"
                        title="Purge from Local Index"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Local Source Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-xs p-4">
          <div className="w-full max-w-lg bg-[#141c28] border border-slate-700 rounded-md shadow-2xl p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <HardDrive className="w-4 h-4 text-blue-400" />
                <h3 className="text-sm font-semibold text-slate-100">
                  Connect Local Organizational File
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setShowAddModal(false)}
                className="text-slate-400 hover:text-slate-200"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateSubmit} className="space-y-3 font-mono text-xs">
              <div>
                <label className="block text-slate-300 mb-1">File Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Northern_Coalfields_Offtake_Audit_2026.pdf"
                  value={newFilename}
                  onChange={(e) => setNewFilename(e.target.value)}
                  className="w-full bg-[#182333] border border-slate-700 rounded px-3 py-1.5 text-slate-100 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 mb-1">Document Format</label>
                  <select
                    value={newType}
                    onChange={(e) => setNewType(e.target.value as any)}
                    className="w-full bg-[#182333] border border-slate-700 rounded px-3 py-1.5 text-slate-100 focus:outline-none focus:border-blue-500"
                  >
                    <option value="PDF">PDF (Digital Text)</option>
                    <option value="Scanned PDF">Scanned PDF (Requires OCR)</option>
                    <option value="DOCX">DOCX (Word Document)</option>
                    <option value="XLSX">XLSX (Excel Workbook)</option>
                    <option value="CSV">CSV (Tabular Ledger)</option>
                    <option value="Images">Images (Site Photos / GIS)</option>
                    <option value="TXT">TXT (Raw Memorandum)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-300 mb-1">Page Count Estimate</label>
                  <input
                    type="number"
                    min="1"
                    value={newPages}
                    onChange={(e) => setNewPages(parseInt(e.target.value) || 1)}
                    className="w-full bg-[#182333] border border-slate-700 rounded px-3 py-1.5 text-slate-100 focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-300 mb-1">Local Filesystem Path</label>
                <input
                  type="text"
                  value={newSourcePath}
                  onChange={(e) => setNewSourcePath(e.target.value)}
                  className="w-full bg-[#182333] border border-slate-700 rounded px-3 py-1.5 text-slate-100 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="p-3 bg-blue-950/20 border border-blue-800/40 rounded text-[11px] text-blue-300 font-sans">
                Upon registration, the local daemon will initiate OCR extraction, table lattice identification, and BGE-M3 vector embedding asynchronously in the background.
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded"
                >
                  Register Source
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
