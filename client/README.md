# Secure Session Manager - Client Agent (Python)

Privacy-preserving session monitoring and isolation client designed for Windows public computers (academic labs, libraries, cyber cafes).

## Key Features
- **Privacy-Preserving Audit Recording (Novelty)**:
  - Records *metadata only* (process names, CPU/RAM, file extensions, data volume).
  - Cryptographically hashes sensitive identifiers (file paths, executable paths, IP addresses) with SHA-256.
  - Zero keystroke recording, zero screen capture, zero content scraping.
  - Generates a tamper-proof cryptographic **HMAC-SHA256 Hash Chain** for legal admissibility.
  - Encrypts event batches with **AES-256 Fernet** prior to transmission.
- **Session Lifecycle & Idle Timeout**:
  - Detects Windows user login/logout.
  - Tracks user activity using Win32 `GetLastInputInfo`.
  - Automatically logs out and sanitizes state after configured idle duration.
- **Admin-Managed Quarantine**:
  - Routes Chrome and Edge downloads to `Downloads\SecureSessionManager\<machine>\<session>` and moves only that session folder's files into reversible local quarantine during logout or instant lock. Browser preferences are updated at session start, so Chrome and Edge should be closed when a new client session begins. Existing files elsewhere in Downloads are left untouched.
  - Moves configured browser data, temporary files, and Recent items into a reversible local quarantine.
  - Allows authenticated admins to review items, restore selected files, or explicitly authorize permanent deletion.
  - Quarantine data is stored under `%LOCALAPPDATA%\SecureSessionManager\Quarantine`.
  - Clears the Windows clipboard; clipboard contents are not recoverable through quarantine.
- **Emergency Panic Lock**:
  - Remote or local trigger that instantly sanitizes sensitive buffers and locks the workstation.

## Installation & Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure client
# Edit config.yaml for your server endpoint and machine ID

# 3. Run client agent
python main.py --test-login
```

The dashboard requires administrator sign-in. Controlled-demo credentials default to `admin` / `admin`; set `ADMIN_USERNAME` and `ADMIN_PASSWORD` on the server before use outside a local demo. Restore and permanent-delete requests are queued for the client and apply when it checks in. Restore does not overwrite an existing file.

## Running Unit Tests
```bash
pytest ../tests/test_session_recorder.py -v
```
