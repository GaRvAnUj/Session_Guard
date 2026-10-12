# Secure Session Manager - Spring Boot Backend Server

Enterprise Java 25+ / Spring Boot 3 backend responsible for session lifecycle, AES-256 decryption of metadata events, cryptographic HMAC-SHA256 integrity verification, tamper detection, and audit trail presentation.

The administrator dashboard requires sign-in. The controlled-demo credentials are `admin` / `admin`; set `ADMIN_USERNAME` and `ADMIN_PASSWORD` for any non-demo deployment.

## Architectural Highlights
- **SessionRecordingService (Core Novelty)**:
  - Decrypts client AES-256 Fernet tokens.
  - Verifies HMAC-SHA256 signatures for tamper proofing.
  - Validates cryptographic hash chains ($H_n = \text{HMAC}(H_{n-1}, \text{Metadata}_n)$).
  - Automatically raises alerts upon hash chain disruption.
- **REST APIs**:
  - `/api/sessions/*`: Session creation, termination, and live status.
  - `/api/events`: Batched encrypted intake.
  - `/api/audit/*`: Privacy-preserving timeline and hash chain verification.
  - `/api/admin/*`: Instant panic lock, command queue, and GDPR compliance metrics.
- **WebSocket Streaming**:
  - Real-time event streaming to `/topic/sessions` and `/topic/alerts`.
- **Database Support**:
  - In-memory H2 for development (`application-dev.yml`).
  - Production-ready PostgreSQL (`application-prod.yml`).

## Building & Running

Set a unique signing secret of at least 32 bytes in the environment before starting the Spring Boot application. Do not commit the secret:

```powershell
$env:JWT_SECRET = "<unique-random-secret-at-least-32-bytes>"
```

```bash
# Build with Maven
mvn clean package

# Run with Dev profile (H2 database)
java -jar target/secure-session-manager-server-1.0.0.jar --spring.profiles.active=dev

# Run the local backend runner
python server_runner.py
```
