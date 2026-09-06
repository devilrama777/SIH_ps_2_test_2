import React, { useState, useRef, useEffect } from 'react';
import {
  ShieldCheck,
  Cpu,
  Minus,
  Square,
  X,
  HardDrive,
  Database,
  Radio,
  Monitor,
  ChevronDown,
  FileText,
  FolderOpen,
  Download,
  Terminal,
  Info,
  Maximize2,
  RefreshCw,
  Sparkles,
  Layers,
  FilePlus,
  HelpCircle,
  Pickaxe,
  Sun,
  Moon,
} from 'lucide-react';
import { AppView, DesktopPlatform, DesktopSystemInfo } from '../../types';
import { desktopBridge } from '../../services/desktopBridge';
import { useTheme } from '../../context/ThemeContext';

interface AppTitlebarProps {
  currentPlatform: DesktopPlatform;
  onChangePlatform: (platform: DesktopPlatform) => void;
  activeReportTitle?: string;
  isAirgapped?: boolean;
  onNavigate: (view: AppView) => void;
  onOpenAudit: () => void;
  onOpenAbout: () => void;
}

export const AppTitlebar: React.FC<AppTitlebarProps> = ({
  currentPlatform,
  onChangePlatform,
  activeReportTitle,
  isAirgapped = true,
  onNavigate,
  onOpenAudit,
  onOpenAbout,
}) => {
  const { theme, toggleTheme, isLight } = useTheme();
  const [activeMenu, setActiveMenu] = useState<string | null>(null);
  const [isMaximized, setIsMaximized] = useState(false);
  const menuBarRef = useRef<HTMLDivElement>(null);

  // Close menus when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuBarRef.current && !menuBarRef.current.contains(e.target as Node)) {
        setActiveMenu(null);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleMinimize = () => {
    desktopBridge.minimizeWindow();
  };

  const handleToggleMaximize = () => {
    const state = desktopBridge.toggleMaximize();
    setIsMaximized(state);
  };

  const handleClose = () => {
    const closed = desktopBridge.closeWindow();
    if (!closed) {
      alert('MineIntel Desktop: Window minimized to background system tray. The local AI daemon continues operating airgapped.');
    }
  };

  const isMac = currentPlatform === 'macos';
  const isWin = currentPlatform === 'windows';
  const isLinux = currentPlatform === 'linux';

  const shortcutKey = isMac ? '⌘' : 'Ctrl+';

  return (
    <header
      data-tauri-drag-region
      className={`h-10 w-full border-b flex items-center justify-between px-2.5 text-xs select-none z-50 shrink-0 relative transition-colors ${
        isLight
          ? 'bg-white border-slate-200 text-slate-800'
          : 'bg-[#090d15] border-[#1b2535] text-slate-200'
      }`}
    >
      {/* Left: macOS Traffic lights OR Linux/Windows Icon + Branding */}
      <div className="flex items-center gap-3">
        {/* macOS Traffic Lights on Left */}
        {isMac && (
          <div className="flex items-center gap-2 pl-1 pr-1">
            <button
              type="button"
              onClick={handleClose}
              className="w-3 h-3 rounded-full bg-[#ff5f56] hover:bg-[#ff4136] border border-[#e0443e] flex items-center justify-center text-black/60 group cursor-pointer"
              title="Close MineIntel Desktop (⌘Q)"
            >
              <X className="w-2 h-2 opacity-0 group-hover:opacity-100 transition" />
            </button>
            <button
              type="button"
              onClick={handleMinimize}
              className="w-3 h-3 rounded-full bg-[#ffbd2e] hover:bg-[#ffaa00] border border-[#dea123] flex items-center justify-center text-black/60 group cursor-pointer"
              title="Minimize to Dock (⌘M)"
            >
              <Minus className="w-2 h-2 opacity-0 group-hover:opacity-100 transition" />
            </button>
            <button
              type="button"
              onClick={handleToggleMaximize}
              className="w-3 h-3 rounded-full bg-[#27c93f] hover:bg-[#1ebd33] border border-[#1aab29] flex items-center justify-center text-black/60 group cursor-pointer"
              title="Zoom / Fullscreen (⌘F)"
            >
              <Maximize2 className="w-1.5 h-1.5 opacity-0 group-hover:opacity-100 transition" />
            </button>
          </div>
        )}

        {/* Brand Icon & Name: Axe Mining Emblem */}
        <div className="flex items-center gap-2">
          <div
            className={`w-6 h-6 rounded flex items-center justify-center shadow-xs shrink-0 border ${
              isLight
                ? 'bg-gradient-to-br from-blue-600 to-indigo-700 border-blue-400/40 text-white'
                : 'bg-gradient-to-br from-blue-600 via-indigo-700 to-slate-900 border-blue-400/40 text-blue-200'
            }`}
          >
            <Pickaxe className="w-3.5 h-3.5 transform -rotate-12" />
          </div>
          <div className="flex flex-col justify-center leading-none">
            <div className="flex items-center gap-1.5">
              <span
                className={`font-extrabold tracking-wide text-[12px] ${
                  isLight ? 'text-slate-900' : 'text-slate-100'
                }`}
              >
                MineIntel
              </span>
              <span
                className={`text-[9px] font-mono px-1 py-0.2 rounded font-semibold ${
                  isLight
                    ? 'text-blue-700 bg-blue-50 border border-blue-200'
                    : 'text-blue-400 bg-blue-950/70 border border-blue-800/60'
                }`}
              >
                DESKTOP
              </span>
            </div>
            <span
              className={`text-[9px] font-medium tracking-tight pt-0.5 ${
                isLight ? 'text-slate-500' : 'text-slate-400'
              }`}
            >
              AI Powered Report Generator Program
            </span>
          </div>
        </div>

        <div className={`h-4 w-px ${isLight ? 'bg-slate-200' : 'bg-[#233145]'}`} />

        {/* Desktop Application Menu Bar (File, Edit, View, Platform, Help) */}
        <div ref={menuBarRef} className="hidden md:flex items-center gap-0.5 text-[11px]">
          {/* File Menu */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setActiveMenu(activeMenu === 'file' ? null : 'file')}
              className={`px-2 py-1 rounded transition cursor-pointer ${
                activeMenu === 'file'
                  ? isLight
                    ? 'bg-slate-100 text-blue-600 font-semibold'
                    : 'bg-slate-800 text-white'
                  : isLight
                  ? 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800/70'
              }`}
            >
              File
            </button>
            {activeMenu === 'file' && (
              <div
                className={`absolute left-0 top-full mt-1 w-56 border rounded-lg shadow-xl py-1 z-50 font-mono text-xs ${
                  isLight
                    ? 'bg-white border-slate-200 text-slate-700 shadow-slate-200/50'
                    : 'bg-[#111722] border-[#233145] text-slate-200'
                }`}
              >
                <button
                  type="button"
                  onClick={() => {
                    onNavigate('new-report');
                    setActiveMenu(null);
                  }}
                  className={`w-full text-left px-3 py-1.5 flex items-center justify-between cursor-pointer ${
                    isLight ? 'hover:bg-blue-50 hover:text-blue-700' : 'hover:bg-blue-600 hover:text-white'
                  }`}
                >
                  <span className="flex items-center gap-2">
                    <FilePlus className="w-3.5 h-3.5" />
                    <span>New Report Wizard</span>
                  </span>
                  <span className="text-[10px] opacity-70">{shortcutKey}N</span>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    onNavigate('data-sources');
                    setActiveMenu(null);
                  }}
                  className={`w-full text-left px-3 py-1.5 flex items-center justify-between cursor-pointer ${
                    isLight ? 'hover:bg-blue-50 hover:text-blue-700' : 'hover:bg-blue-600 hover:text-white'
                  }`}
                >
                  <span className="flex items-center gap-2">
                    <FolderOpen className="w-3.5 h-3.5" />
                    <span>Ingest Data Source...</span>
                  </span>
                  <span className="text-[10px] opacity-70">{shortcutKey}O</span>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    onNavigate('export');
                    setActiveMenu(null);
                  }}
                  className={`w-full text-left px-3 py-1.5 flex items-center justify-between cursor-pointer ${
                    isLight ? 'hover:bg-blue-50 hover:text-blue-700' : 'hover:bg-blue-600 hover:text-white'
                  }`}
                >
                  <span className="flex items-center gap-2">
                    <Download className="w-3.5 h-3.5" />
                    <span>Export Statutory PDF...</span>
                  </span>
                  <span className="text-[10px] opacity-70">{shortcutKey}E</span>
                </button>
                <div className={`h-px my-1 ${isLight ? 'bg-slate-100' : 'bg-slate-800'}`} />
                <button
                  type="button"
                  onClick={() => {
                    handleClose();
                    setActiveMenu(null);
                  }}
                  className="w-full text-left px-3 py-1.5 hover:bg-rose-600 hover:text-white flex items-center justify-between text-rose-500 cursor-pointer"
                >
                  <span>Exit Desktop Program</span>
                  <span className="text-[10px]">{shortcutKey}Q</span>
                </button>
              </div>
            )}
          </div>

          {/* Edit Menu */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setActiveMenu(activeMenu === 'edit' ? null : 'edit')}
              className={`px-2 py-1 rounded transition cursor-pointer ${
                activeMenu === 'edit'
                  ? isLight
                    ? 'bg-slate-100 text-blue-600 font-semibold'
                    : 'bg-slate-800 text-white'
                  : isLight
                  ? 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800/70'
              }`}
            >
              Edit
            </button>
            {activeMenu === 'edit' && (
              <div
                className={`absolute left-0 top-full mt-1 w-52 border rounded-lg shadow-xl py-1 z-50 font-mono text-xs ${
                  isLight
                    ? 'bg-white border-slate-200 text-slate-700 shadow-slate-200/50'
                    : 'bg-[#111722] border-[#233145] text-slate-200'
                }`}
              >
                <button
                  type="button"
                  onClick={() => {
                    onNavigate('evidence-search');
                    setActiveMenu(null);
                  }}
                  className={`w-full text-left px-3 py-1.5 flex items-center justify-between cursor-pointer ${
                    isLight ? 'hover:bg-blue-50 hover:text-blue-700' : 'hover:bg-blue-600 hover:text-white'
                  }`}
                >
                  <span>Search Evidence Index</span>
                  <span className="text-[10px] opacity-70">{shortcutKey}F</span>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    onNavigate('report-editor');
                    setActiveMenu(null);
                  }}
                  className={`w-full text-left px-3 py-1.5 flex items-center justify-between cursor-pointer ${
                    isLight ? 'hover:bg-blue-50 hover:text-blue-700' : 'hover:bg-blue-600 hover:text-white'
                  }`}
                >
                  <span>Active Report Editor</span>
                  <span className="text-[10px] opacity-70">{shortcutKey}T</span>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    onNavigate('validation');
                    setActiveMenu(null);
                  }}
                  className={`w-full text-left px-3 py-1.5 flex items-center justify-between cursor-pointer ${
                    isLight ? 'hover:bg-blue-50 hover:text-blue-700' : 'hover:bg-blue-600 hover:text-white'
                  }`}
                >
                  <span>Consistency Gate</span>
                  <span className="text-[10px] opacity-70">{shortcutKey}G</span>
                </button>
              </div>
            )}
          </div>

          {/* View Menu */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setActiveMenu(activeMenu === 'view' ? null : 'view')}
              className={`px-2 py-1 rounded transition cursor-pointer ${
                activeMenu === 'view'
                  ? isLight
                    ? 'bg-slate-100 text-blue-600 font-semibold'
                    : 'bg-slate-800 text-white'
                  : isLight
                  ? 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800/70'
              }`}
            >
              View
            </button>
            {activeMenu === 'view' && (
              <div
                className={`absolute left-0 top-full mt-1 w-52 border rounded-lg shadow-xl py-1 z-50 font-mono text-xs ${
                  isLight
                    ? 'bg-white border-slate-200 text-slate-700 shadow-slate-200/50'
                    : 'bg-[#111722] border-[#233145] text-slate-200'
                }`}
              >
                <button
                  type="button"
                  onClick={() => {
                    onNavigate('dashboard');
                    setActiveMenu(null);
                  }}
                  className={`w-full text-left px-3 py-1.5 cursor-pointer ${
                    isLight ? 'hover:bg-blue-50 hover:text-blue-700' : 'hover:bg-blue-600 hover:text-white'
                  }`}
                >
                  Executive Dashboard
                </button>
                <button
                  type="button"
                  onClick={() => {
                    onNavigate('report-planner');
                    setActiveMenu(null);
                  }}
                  className={`w-full text-left px-3 py-1.5 cursor-pointer ${
                    isLight ? 'hover:bg-blue-50 hover:text-blue-700' : 'hover:bg-blue-600 hover:text-white'
                  }`}
                >
                  Report Structure Planner
                </button>
                <button
                  type="button"
                  onClick={() => {
                    onNavigate('preview');
                    setActiveMenu(null);
                  }}
                  className={`w-full text-left px-3 py-1.5 cursor-pointer ${
                    isLight ? 'hover:bg-blue-50 hover:text-blue-700' : 'hover:bg-blue-600 hover:text-white'
                  }`}
                >
                  Proofing Preview (PDF)
                </button>
                <div className={`h-px my-1 ${isLight ? 'bg-slate-100' : 'bg-slate-800'}`} />
                <button
                  type="button"
                  onClick={() => {
                    desktopBridge.toggleFullscreen();
                    setActiveMenu(null);
                  }}
                  className={`w-full text-left px-3 py-1.5 flex items-center justify-between cursor-pointer ${
                    isLight ? 'hover:bg-blue-50 hover:text-blue-700' : 'hover:bg-blue-600 hover:text-white'
                  }`}
                >
                  <span>Toggle Fullscreen</span>
                  <span className="text-[10px] opacity-70">F11</span>
                </button>
              </div>
            )}
          </div>

          {/* OS Platform Switcher Menu (Linux / macOS / Windows) */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setActiveMenu(activeMenu === 'platform' ? null : 'platform')}
              className={`px-2 py-1 rounded transition cursor-pointer flex items-center gap-1 ${
                activeMenu === 'platform'
                  ? isLight
                    ? 'bg-slate-100 text-blue-600 font-semibold'
                    : 'bg-slate-800 text-white'
                  : isLight
                  ? 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800/70'
              }`}
            >
              <Monitor className="w-3 h-3 text-emerald-500" />
              <span>OS: {currentPlatform === 'linux' ? 'Linux' : currentPlatform === 'macos' ? 'macOS' : 'Windows'}</span>
              <ChevronDown className="w-2.5 h-2.5 opacity-60" />
            </button>
            {activeMenu === 'platform' && (
              <div
                className={`absolute left-0 top-full mt-1 w-64 border rounded-lg shadow-xl py-1 z-50 font-mono text-xs ${
                  isLight
                    ? 'bg-white border-slate-200 text-slate-700 shadow-slate-200/50'
                    : 'bg-[#111722] border-[#233145] text-slate-200'
                }`}
              >
                <div
                  className={`px-3 py-1 text-[10px] uppercase tracking-wider border-b ${
                    isLight ? 'text-slate-400 border-slate-100' : 'text-slate-400 border-slate-800'
                  }`}
                >
                  Target Desktop Environment
                </div>
                <button
                  type="button"
                  onClick={() => {
                    onChangePlatform('linux');
                    setActiveMenu(null);
                  }}
                  className={`w-full text-left px-3 py-2 flex items-center justify-between cursor-pointer ${
                    isLinux
                      ? isLight ? 'bg-blue-50 text-blue-700 font-bold' : 'bg-blue-900/40 text-blue-300 font-bold'
                      : isLight ? 'hover:bg-slate-50' : 'hover:bg-blue-600 hover:text-white'
                  }`}
                >
                  <div>
                    <div>🐧 Linux (Ubuntu / RHEL / Debian)</div>
                    <div className="text-[10px] opacity-70">POSIX sockets, /opt/mineintel, GTK</div>
                  </div>
                  {isLinux && <span className="text-emerald-500 text-xs">Active</span>}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    onChangePlatform('macos');
                    setActiveMenu(null);
                  }}
                  className={`w-full text-left px-3 py-2 flex items-center justify-between cursor-pointer ${
                    isMac
                      ? isLight ? 'bg-blue-50 text-blue-700 font-bold' : 'bg-blue-900/40 text-blue-300 font-bold'
                      : isLight ? 'hover:bg-slate-50' : 'hover:bg-blue-600 hover:text-white'
                  }`}
                >
                  <div>
                    <div>🍎 macOS (Apple Silicon / Intel)</div>
                    <div className="text-[10px] opacity-70">Cocoa titlebar, ~/Library/Application Support</div>
                  </div>
                  {isMac && <span className="text-emerald-500 text-xs">Active</span>}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    onChangePlatform('windows');
                    setActiveMenu(null);
                  }}
                  className={`w-full text-left px-3 py-2 flex items-center justify-between cursor-pointer ${
                    isWin
                      ? isLight ? 'bg-blue-50 text-blue-700 font-bold' : 'bg-blue-900/40 text-blue-300 font-bold'
                      : isLight ? 'hover:bg-slate-50' : 'hover:bg-blue-600 hover:text-white'
                  }`}
                >
                  <div>
                    <div>🪟 Windows (11 / 10 Enterprise)</div>
                    <div className="text-[10px] opacity-70">WinUI controls, C:\ProgramData\MineIntel</div>
                  </div>
                  {isWin && <span className="text-emerald-500 text-xs">Active</span>}
                </button>
              </div>
            )}
          </div>

          {/* Help Menu */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setActiveMenu(activeMenu === 'help' ? null : 'help')}
              className={`px-2 py-1 rounded transition cursor-pointer ${
                activeMenu === 'help'
                  ? isLight
                    ? 'bg-slate-100 text-blue-600 font-semibold'
                    : 'bg-slate-800 text-white'
                  : isLight
                  ? 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800/70'
              }`}
            >
              Help
            </button>
            {activeMenu === 'help' && (
              <div
                className={`absolute left-0 top-full mt-1 w-56 border rounded-lg shadow-xl py-1 z-50 font-mono text-xs ${
                  isLight
                    ? 'bg-white border-slate-200 text-slate-700 shadow-slate-200/50'
                    : 'bg-[#111722] border-[#233145] text-slate-200'
                }`}
              >
                <button
                  type="button"
                  onClick={() => {
                    onOpenAudit();
                    setActiveMenu(null);
                  }}
                  className={`w-full text-left px-3 py-1.5 flex items-center gap-2 cursor-pointer ${
                    isLight ? 'hover:bg-blue-50 hover:text-blue-700' : 'hover:bg-blue-600 hover:text-white'
                  }`}
                >
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
                  <span>Verify Airgap Security</span>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    onNavigate('settings');
                    setActiveMenu(null);
                  }}
                  className={`w-full text-left px-3 py-1.5 flex items-center gap-2 cursor-pointer ${
                    isLight ? 'hover:bg-blue-50 hover:text-blue-700' : 'hover:bg-blue-600 hover:text-white'
                  }`}
                >
                  <Terminal className="w-3.5 h-3.5 text-blue-500" />
                  <span>Local Daemon IPC Test</span>
                </button>
                <div className={`h-px my-1 ${isLight ? 'bg-slate-100' : 'bg-slate-800'}`} />
                <button
                  type="button"
                  onClick={() => {
                    onOpenAbout();
                    setActiveMenu(null);
                  }}
                  className={`w-full text-left px-3 py-1.5 flex items-center gap-2 cursor-pointer ${
                    isLight ? 'hover:bg-blue-50 hover:text-blue-700' : 'hover:bg-blue-600 hover:text-white'
                  }`}
                >
                  <Info className="w-3.5 h-3.5 text-indigo-500" />
                  <span>About MineIntel Desktop...</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Middle: Active Report Document Badge */}
      {activeReportTitle && (
        <div
          className={`hidden lg:flex items-center gap-2 px-2.5 py-0.5 rounded font-mono text-[11px] max-w-sm truncate border ${
            isLight
              ? 'bg-slate-100 border-slate-200 text-slate-700'
              : 'bg-[#121926] border-slate-800 text-slate-300'
          }`}
        >
          <FileText className="w-3 h-3 text-blue-500 shrink-0" />
          <span className="truncate">{activeReportTitle}</span>
        </div>
      )}

      {/* Right: Theme Toggle + Airgap Security Status & Windows/Linux Window Controls */}
      <div className="flex items-center gap-2">
        {/* Light / Dark Mode Toggle Button */}
        <button
          type="button"
          onClick={toggleTheme}
          className={`flex items-center gap-1.5 px-2 py-1 rounded-md text-[11px] font-medium border transition cursor-pointer ${
            isLight
              ? 'bg-slate-100 hover:bg-slate-200 text-slate-700 border-slate-300'
              : 'bg-slate-800/80 hover:bg-slate-700 text-slate-200 border-slate-700'
          }`}
          title={isLight ? 'Switch to Dark Mode' : 'Switch to Light Mode (White Interface)'}
        >
          {isLight ? (
            <>
              <Moon className="w-3.5 h-3.5 text-indigo-600" />
              <span className="hidden sm:inline">Dark</span>
            </>
          ) : (
            <>
              <Sun className="w-3.5 h-3.5 text-amber-400" />
              <span className="hidden sm:inline">Light</span>
            </>
          )}
        </button>

        {/* Airgap badge */}
        <button
          type="button"
          onClick={onOpenAudit}
          className={`flex items-center gap-1.5 text-[10px] font-mono px-2 py-0.5 rounded border transition cursor-pointer ${
            isLight
              ? 'text-emerald-700 bg-emerald-50 hover:bg-emerald-100 border-emerald-200'
              : 'text-emerald-400 bg-emerald-950/40 hover:bg-emerald-900/50 border-emerald-800/40'
          }`}
          title="Airgap Hardware Integrity Active"
        >
          <ShieldCheck className="w-3 h-3 text-emerald-500" />
          <span className="font-semibold hidden sm:inline">AIRGAPPED NODE</span>
        </button>

        {/* Windows / Linux Window Controls on Right */}
        {!isMac && (
          <div
            className={`flex items-center ml-1 border-l pl-1 ${
              isLight ? 'border-slate-200' : 'border-slate-800'
            }`}
          >
            <button
              type="button"
              onClick={handleMinimize}
              className={`w-8 h-7 flex items-center justify-center transition cursor-pointer ${
                isLight
                  ? 'text-slate-500 hover:text-slate-900 hover:bg-slate-100'
                  : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/80'
              }`}
              title="Minimize Window"
            >
              <Minus className="w-3.5 h-3.5" />
            </button>
            <button
              type="button"
              onClick={handleToggleMaximize}
              className={`w-8 h-7 flex items-center justify-center transition cursor-pointer ${
                isLight
                  ? 'text-slate-500 hover:text-slate-900 hover:bg-slate-100'
                  : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/80'
              }`}
              title={isMaximized ? 'Restore Window' : 'Maximize Window'}
            >
              <Square className="w-3 h-3" />
            </button>
            <button
              type="button"
              onClick={handleClose}
              className={`w-8 h-7 flex items-center justify-center transition cursor-pointer ${
                isLight
                  ? 'text-slate-500 hover:text-white hover:bg-rose-600'
                  : 'text-slate-400 hover:text-white hover:bg-rose-600'
              }`}
              title="Close MineIntel Desktop"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
