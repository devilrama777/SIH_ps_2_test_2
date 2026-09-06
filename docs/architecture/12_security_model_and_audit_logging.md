# Security Architecture & Cryptographic Audit Logging

> **Status:** Implemented & Verified (Phase 10 — Section 24 & Section 25)  
> **Subsystem:** `core.security` (`models.py`, `audit_logger.py`, `credentials.py`, `network_guard.py`)  
> **Integration:** `apps.processing.server`, `apps.desktop.src.components.SecurityAuditView`

---

## 1. Architectural Overview & Air-Gap Invariant

The **CIL Local AI Report Generator** operates under a strict **air-gapped, local-first mandate**:

1. **Zero External Cloud AI Calls**:
   - The application does not communicate with external LLM APIs (OpenAI, Anthropic Claude, Google Gemini, Azure OpenAI, AWS Bedrock, etc.).
   - All extraction, parsing, vector/keyword indexing, semantic classification, narrative generation, validation, and PDF rendering occur locally on the operator's machine.

2. **Strict Loopback Binding**:
   - The FastAPI backend server binds exclusively to `127.0.0.1` (local loopback).
   - Network security scanning actively inspects environment variables (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.) to detect and alert against unintentional credential leakage.
   - A runtime socket interceptor (`NetworkSecurityGuard.install_socket_airgap_hook`) blocks non-loopback outbound connections.

---

## 2. Cryptographic Tamper-Evident Audit Logging

Every critical business action is immutably recorded in SQLite (`data/workspace/audit_log.db`) using **cryptographic SHA-256 hash chaining**:

```
[Genesis Hash: 000...000]
         │
         ▼
[Log 1: Ingestion] ────────> entry_hash = SHA256(id | ts | type | user | act | res | status | prev_hash)
         │
         ▼
[Log 2: Report Created] ───> prev_hash = Log 1 entry_hash
         │
         ▼
[Log 3: Edit Accepted] ────> prev_hash = Log 2 entry_hash
         │
         ▼
[Log 4: PDF Export] ───────> prev_hash = Log 3 entry_hash
```

### Tamper Detection Guarantee
If an unauthorized actor modifies any record (e.g. changing an action or status directly in the SQLite database), recomputing the hash sequence during `verify_chain_integrity()` immediately detects the mismatch between expected hash and entry hash, flagging the chain as corrupted.

### Audited Event Types (`AuditEventType`)
- `ingestion`: File discovery and canonical document ingestion.
- `report_created`: Report synthesis and deterministic validation.
- `agent_edit_proposed`: Grounded narrative modification proposed by local editing agent.
- `agent_edit_accepted`: Human operator approved revision.
- `agent_edit_rejected`: Human operator discarded revision.
- `export_pdf`: Headless Chromium / PyMuPDF print execution.
- `export_html`: HTML generation.
- `config_change`: Secret vault modifications or setting updates.
- `network_violation`: Blocked non-loopback outbound socket access.

---

## 3. OS-Level Encrypted Credential Vault

Secrets (database passwords, internal tokens, HMAC keys) are protected without plaintext `.env` or configuration files via `SecureCredentialVault`:

- **Windows DPAPI Integration**: Uses `ctypes.windll.crypt32.CryptProtectData` and `CryptUnprotectData` to encrypt and decrypt secrets using the active Windows user logon session.
- **Machine-Salted Key Fallback**: On non-Windows environments, derives a salted AES/XOR key from the host hardware identifier (`uuid.getnode()`).
- **Encrypted Persistence**: Encrypted bytes are written to `data/workspace/vault.bin`.

---

## 4. REST API & UI Surface

### Endpoints
- `GET /api/v1/security/status`: Returns air-gap isolation status, active controls, ledger integrity, log count, and stored vault keys.
- `GET /api/v1/security/audit-logs`: Retrieves chronologically chained audit logs with optional event type filtering.
- `POST /api/v1/security/vault`: Stores credentials securely in the DPAPI encrypted vault.
- `GET /api/v1/security/vault/keys`: Lists stored vault key identifiers (values remain encrypted).

### Desktop UI (`SecurityAuditView.tsx`)
- Air-Gap status card (100% Air-Gapped pulse indicator).
- Cryptographic chain integrity badge (verified vs. corrupted).
- Filterable live table of audit records showing timestamps, event types, actions, users, and SHA-256 entry hashes.
- Credential vault management interface with key/value input and DPAPI encryption triggers.
