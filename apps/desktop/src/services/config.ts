/**
 * Centralized API Base URL Resolver for MineIntel Desktop Application.
 *
 * Supports:
 * 1. Runtime injection via window.__MINEINTEL_API_BASE__ (from Tauri shell)
 * 2. Environment variable VITE_API_BASE (if defined)
 * 3. Default fallback to loopback port http://127.0.0.1:8765
 */
export const getApiBaseUrl = (): string => {
  if (typeof window !== 'undefined' && (window as any).__MINEINTEL_API_BASE__) {
    return (window as any).__MINEINTEL_API_BASE__.replace(/\/+$/, '');
  }
  return 'http://127.0.0.1:8765';
};

export const API_BASE = getApiBaseUrl();
