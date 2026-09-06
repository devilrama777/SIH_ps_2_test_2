# MineIntel — First-Run Setup & Zero-Default-Credential Policy

## 1. Zero Default Credentials Policy
MineIntel strictly complies with enterprise security regulations prohibiting hardcoded default passwords (such as `admin/admin`, `test/test`, or default root credentials).

- Fresh installations initialize an empty user table in `data/users.db`.
- No demo users or dummy accounts are seeded into production tables.

## 2. First-Run Setup Workflow
1. When MineIntel is launched for the first time on a new workstation, the frontend calls `GET /api/v1/auth/setup-status`.
2. The endpoint returns:
   ```json
   {
     "has_users": false,
     "requires_setup": true
   }
   ```
3. The desktop interface automatically presents the **First-Run Account Setup** wizard:
   - Operator specifies primary administrator username (minimum 3 chars).
   - Operator specifies official display name / title (e.g. *Dr. A. Sharma, Director Operations*).
   - Operator sets a strong master password (minimum 6 chars, confirmed twice).
4. Submitting calls `POST /api/v1/auth/first-run-setup`:
   - Hashes password using PBKDF2-HMAC-SHA256 with unique 32-byte salt.
   - Saves administrator record with `role="admin"`.
   - Creates user workspace directory.
   - Logs `ACCOUNT_CREATED` and `LOGIN_SUCCESS` in the audit ledger.
   - Issues active session token.
5. All subsequent requests to `POST /api/v1/auth/first-run-setup` are blocked with `400 Bad Request`.
