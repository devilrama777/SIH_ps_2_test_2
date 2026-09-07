# MineIntel — Local Authentication & Session Management

## 1. Overview
MineIntel operates in an air-gapped, local-first enterprise environment. Authentication validates local user identity against the embedded SQLite user database (`data/users.db`) using industry-standard, FIPS-compliant cryptographic primitives without any cloud dependencies.

```
Desktop App (LoginView)
      │
      │ POST /api/v1/auth/login { username, password }
      ▼
FastAPI Processing Backend (127.0.0.1:8765)
      │
      ├─► Brute-Force Check (Local rate-limiter & 30s lockout after 5 failures)
      ├─► Password Verification (PBKDF2-HMAC-SHA256, 100,000 iterations, 32-byte salt)
      ├─► Session Generation (64-character cryptographically secure token)
      ├─► Audit Logging (Tamper-evident SHA-256 chained audit ledger)
      ▼
Returns AuthResponse { session_token, user: UserPublic }
```

## 2. Password Security Architecture
- **Algorithm**: PBKDF2-HMAC-SHA256
- **Iterations**: 100,000 rounds
- **Salt**: 32-byte cryptographically secure random salt generated via `secrets.token_hex(32)`
- **Comparison**: Constant-time byte-level verification (`secrets.compare_digest`) to prevent timing side-channel attacks.
- **Inviolable Invariant**: Passwords are never stored in plaintext, never logged, and never returned in API payloads.

## 3. Session Lifecycle & Token Management
- Sessions are identified by 64-character hexadecimal tokens generated with cryptographically secure entropy (`secrets.token_hex(32)`).
- Session tokens are passed via the standard HTTP `Authorization: Bearer <session_token>` header.
- Sliding activity window updates `last_activity_at` on every authenticated request with a default 24-hour expiration.
- Explicit logout (`POST /api/v1/auth/logout`) revokes the active session immediately and purges all in-memory client state.

## 4. API Endpoints
| Endpoint | Method | Description | Auth Required |
|---|---|---|---|
| `/api/v1/auth/setup-status` | `GET` | Checks if local users exist or if first-run setup is required | No |
| `/api/v1/auth/first-run-setup` | `POST` | Creates the primary administrator profile on clean install | No (blocked if users exist) |
| `/api/v1/auth/login` | `POST` | Authenticates credentials and issues session token | No |
| `/api/v1/auth/logout` | `POST` | Revokes the current session token | Yes |
| `/api/v1/auth/session` | `GET` | Verifies active session token validity | Yes |
| `/api/v1/users/me` | `GET` | Returns sanitized current user profile | Yes |

## 5. Future Role-Based Access Control (RBAC) Extensibility
The user model includes an extensible `role` field (default `'analyst'`, with `'admin'` assigned to initial setup). The architecture is decoupled so that fine-grained role permissions can be layered on top of the backend boundary without database schema overhauls.
