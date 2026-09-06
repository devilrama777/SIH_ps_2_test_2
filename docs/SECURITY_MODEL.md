# MineIntel — Security Model & Air-Gap Defense Specification

## 1. Zero Cloud Dependency
MineIntel runs strictly on loopback interfaces (`127.0.0.1:8765`). All network outbound connections to the public internet are blocked by `NetworkSecurityGuard`. No cloud telemetry, external fonts, or remote authentication providers (Auth0, Supabase, Google, Firebase) are loaded.

## 2. Authentication Security Boundaries
- **No Plaintext Passwords**: Neither in database, `.env`, source code, nor frontend localStorage.
- **Generic Error Responses**: Authentication failures return `"Invalid username or password."` without disclosing whether the username exists or whether the password was incorrect.
- **Brute-Force Protection**: 5 consecutive failed login attempts on a single account triggers a 30-second local backoff cooldown.
- **Tamper-Evident Audit Logging**: Authentication events (`LOGIN_SUCCESS`, `LOGIN_FAILURE`, `LOGIN_LOCKED`, `LOGOUT`, `ACCOUNT_CREATED`) are cryptographically chained with SHA-256 genesis hashing into `data/workspace/audit_log.db`.

## 3. Storage Security Classification
| Mechanism | Permitted Data | Prohibited Data |
|---|---|---|
| **sessionStorage** | Temporary active session token (`Bearer <hex>`) | Plaintext passwords, business data, confidential reports |
| **localStorage** | Non-sensitive UI theme ('dark'/'light'), sidebar collapse state | User credentials, session tokens, report contents |
| **data/users.db** | User profiles, PBKDF2 hashes, cryptographic salts, session registry | Plaintext passwords |
| **OS Secure DPAPI** | Windows DPAPI / machine-salted key vault (`vault.bin`) | Plaintext secrets |
