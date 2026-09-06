# Security Baseline Specification (Section 1.5 & Section 24)

## 1. Core Security Principle

Security is required from the very first prototype and is implemented across all layers:
- **Confidential Data**: Stays entirely on the local PC.
- **Local AI Only**: No remote LLM or OCR endpoints.
- **Controlled Tool Access**: Agents interact only via authorized application interfaces; raw shell and unbounded filesystem access are prohibited.
- **Default-Deny Networking**: Inbound/outbound traffic is denied by default; CORS is restricted to local origins.

---

## 2. Implemented Controls (Phase 0)

1. **Airgap Enforcement**:
   - Outbound HTTP requests to external hosts are disabled by default (`ALLOW_EXTERNAL_NETWORK=false`).
   - CORS middleware in `apps/processing/server.py` restricts origin access to `http://localhost:5173`, `http://127.0.0.1:5173`, and `tauri://localhost`.
2. **Zero-Secret Commits**:
   - `.env` and SQLite databases are explicitly excluded via `.gitignore`.
   - `.env.example` provides a sanitized configuration template.
3. **Sensitive Data Redaction**:
   - `apps/processing/logging_config.py` isolates diagnostic logs to stages, durations, and element counts, preventing raw confidential document dumps to standard output or unencrypted disk files.
4. **Workspace Isolation**:
   - Processing operations are sandboxed to `data/workspace/`, `data/cache/`, and `data/indexes/`.
