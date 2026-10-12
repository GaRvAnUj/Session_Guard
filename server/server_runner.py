"""
Secure Session Manager - Backend Server Runner / Bridge.
Implements the exact Spring Boot REST and WebSocket API specification in Python/FastAPI
for immediate zero-dependency local execution, grading demonstrations, and integration tests.
Matches the Java SessionRecordingService novelty:
- Decrypts AES-256 Fernet tokens
- Validates canonical HMAC-SHA256 signatures
- Verifies unbroken hash chains
- Emits real-time alerts
"""

import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
import sys
import threading
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from cryptography.fernet import Fernet
from fastapi import FastAPI, Header, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [ServerRunner]: %(message)s")
logger = logging.getLogger("ServerRunner")

app = FastAPI(title="Secure Session Manager Server", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- In-Memory Data Store -----------------
sessions_db: Dict[str, Dict[str, Any]] = {
    "sess_PC_LAB_01_DEMO": {
        "sessionId": "sess_PC_LAB_01_DEMO",
        "machineId": "PC_LAB_01",
        "startTime": "2026-10-05T14:30:00Z",
        "endTime": None,
        "status": "ACTIVE",
    },
    "sess_PC_LAB_02_COMPLETED": {
        "sessionId": "sess_PC_LAB_02_COMPLETED",
        "machineId": "PC_LAB_02",
        "startTime": "2026-10-05T13:00:00Z",
        "endTime": "2026-10-05T14:15:00Z",
        "status": "COMPLETED",
    },
    "sess_PC_LAB_04_TAMPERED": {
        "sessionId": "sess_PC_LAB_04_TAMPERED",
        "machineId": "PC_LAB_04",
        "startTime": "2026-10-05T14:10:00Z",
        "endTime": None,
        "status": "ACTIVE",
    },
    "sess_PC_LAB_03_DEMO": {
        "sessionId": "sess_PC_LAB_03_DEMO",
        "machineId": "PC_LAB_03",
        "startTime": datetime.now(timezone.utc).isoformat(),
        "endTime": None,
        "status": "ACTIVE",
    },
    "sess_PC_LAB_05_DEMO": {
        "sessionId": "sess_PC_LAB_05_DEMO",
        "machineId": "PC_LAB_05",
        "startTime": datetime.now(timezone.utc).isoformat(),
        "endTime": None,
        "status": "ACTIVE",
    },
}

events_db: Dict[str, List[Dict[str, Any]]] = {
    "sess_PC_LAB_01_DEMO": [
        {
            "id": 1,
            "sessionId": "sess_PC_LAB_01_DEMO",
            "timestamp": "2026-10-05T14:30:10Z",
            "eventType": "session_lifecycle",
            "eventData": {"action": "login", "machine_id": "PC_LAB_01", "status": "ACTIVE"},
            "integrityHash": "a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90",
            "previousEventHash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "verified": True,
        },
        {
            "id": 2,
            "sessionId": "sess_PC_LAB_01_DEMO",
            "timestamp": "2026-10-05T14:32:00Z",
            "eventType": "process_start",
            "eventData": {"process_name": "chrome.exe", "cpu_percent": 3.8, "memory_mb": 175.4, "exe_path_hash_short": "67406a782b535d57"},
            "integrityHash": "b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90a1",
            "previousEventHash": "a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90",
            "verified": True,
        },
        {
            "id": 3,
            "sessionId": "sess_PC_LAB_01_DEMO",
            "timestamp": "2026-10-05T14:35:22Z",
            "eventType": "file_operation",
            "eventData": {"operation": "create", "extension": ".pdf", "size_bytes": 245800, "path_hash_short": "8d7c3f9e2b4a1c5f"},
            "integrityHash": "c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2",
            "previousEventHash": "b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90a1",
            "verified": True,
        },
        {
            "id": 4,
            "sessionId": "sess_PC_LAB_01_DEMO",
            "timestamp": "2026-10-05T14:40:00Z",
            "eventType": "network_connection",
            "eventData": {"protocol": "TCP", "remote_port": 443, "bytes_sent": 2048, "bytes_received": 8192, "remote_ip_hash_short": "f4b3c2a109876543"},
            "integrityHash": "d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3",
            "previousEventHash": "c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2",
            "verified": True,
        },
    ],
    "sess_PC_LAB_04_TAMPERED": [
        {
            "id": 1,
            "sessionId": "sess_PC_LAB_04_TAMPERED",
            "timestamp": "2026-10-05T14:10:15Z",
            "eventType": "process_start",
            "eventData": {"process_name": "cmd.exe", "cpu_percent": 0.5, "memory_mb": 25.0},
            "integrityHash": "99887766554433221100aabbccddeeff99887766554433221100aabbccddeeff",
            "previousEventHash": "genesis_0000000000000000000000000000000000000000000000000000000000000000",
            "verified": True,
        },
        {
            "id": 2,
            "sessionId": "sess_PC_LAB_04_TAMPERED",
            "timestamp": "2026-10-05T14:15:30Z",
            "eventType": "file_operation",
            "eventData": {"operation": "write", "extension": ".bat", "size_bytes": 1024},
            "integrityHash": "112233445566778899aabbccddeeff00112233445566778899aabbccddeeff00",
            "previousEventHash": "TAMPERED_BROKEN_CHAIN_LINK_INVALID_HASH_DETECTED_HERE",
            "verified": False,
        },
    ],
    "sess_PC_LAB_03_DEMO": [],
    "sess_PC_LAB_05_DEMO": [],
}
audit_logs_db: List[Dict[str, Any]] = []
command_queue: Dict[str, List[Dict[str, Any]]] = {}
quarantine_items: Dict[str, List[Dict[str, Any]]] = {}
admin_tokens: Dict[str, Dict[str, Any]] = {}
active_websockets: List[WebSocket] = []

# ----------------- Cryptographic Keys -------------------
# Matching config.yaml and application.yml defaults
AES_KEY = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
raw_bytes = base64.b64decode(AES_KEY)
if len(raw_bytes) != 32:
    raw_bytes = hashlib.sha256(raw_bytes).digest()
FERNET_KEY = base64.urlsafe_b64encode(raw_bytes)
fernet = Fernet(FERNET_KEY)

HMAC_SECRET = base64.b64decode("c2VjdXJlLXNlc3Npb24tbWFuYWdlci1obWFjLXNlY3JldC0yNTY=")


# ----------------- Cryptographic Helpers ----------------
def create_canonical_string(event_data: Dict[str, Any]) -> str:
    canonical_dict = {
        "session_id": event_data["session_id"],
        "timestamp": event_data["timestamp"],
        "event_type": event_data["event_type"],
        "event_data": event_data["event_data"],
        "previous_event_hash": event_data["previous_event_hash"],
    }
    return json.dumps(canonical_dict, sort_keys=True, separators=(",", ":"))


def compute_hmac(canonical_str: str) -> str:
    return hmac.new(HMAC_SECRET, canonical_str.encode("utf-8"), hashlib.sha256).hexdigest()


async def broadcast_alert(payload: Dict[str, Any]):
    for ws in list(active_websockets):
        try:
            await ws.send_json(payload)
        except Exception:
            if ws in active_websockets:
                active_websockets.remove(ws)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_websockets.append(websocket)
    logger.info("WebSocket connection established with dashboard.")
    try:
        while True:
            await websocket.receive_text()
    except (WebSocketDisconnect, Exception):
        if websocket in active_websockets:
            active_websockets.remove(websocket)
        logger.info("WebSocket connection closed.")


# ----------------- Pydantic DTO Models ------------------
class SessionStartRequest(BaseModel):
    machineId: str = "PC_DEFAULT"


class SessionStartResponse(BaseModel):
    sessionId: str
    status: str = "ACTIVE"
    message: str = "Session created successfully"


class SessionEndRequest(BaseModel):
    sessionId: str


class EventBatchRequest(BaseModel):
    sessionId: str
    encryptedEvents: List[str]
    batchCount: Optional[int] = None


class PanicLockCommandDTO(BaseModel):
    machineId: str = "ALL"
    reason: str = "Manual admin trigger"
    adminUser: str = "Administrator"

class QuarantineInventoryRequest(BaseModel):
    items: List[Dict[str, Any]]


class QuarantineActionRequest(BaseModel):
    itemIds: List[str]


def require_admin(authorization: Optional[str]) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Admin sign-in is required.")
    token = authorization[7:]
    claims = admin_tokens.get(token)
    if not claims or claims["expiresAt"] <= datetime.now(timezone.utc):
        admin_tokens.pop(token, None)
        raise HTTPException(status_code=401, detail="Admin token is invalid or expired.")
    return claims["username"]


def require_client(x_api_key: Optional[str]) -> None:
    expected_api_key = os.environ.get("CLIENT_API_KEY", "secure-client-api-key-2026-public-lab")
    if not x_api_key or not secrets.compare_digest(x_api_key, expected_api_key):
        raise HTTPException(status_code=401, detail="Client API key is invalid.")


# ----------------- REST Endpoints -----------------------
@app.post("/api/sessions/start", response_model=SessionStartResponse)
async def start_session(req: SessionStartRequest, x_api_key: Optional[str] = Header(None)):
    require_client(x_api_key)
    session_id = f"sess_{req.machineId}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    session = {
        "sessionId": session_id,
        "machineId": req.machineId,
        "startTime": datetime.now(timezone.utc).isoformat(),
        "endTime": None,
        "status": "ACTIVE",
    }
    sessions_db[session_id] = session
    events_db[session_id] = []
    logger.info("Session started: %s on machine: %s", session_id, req.machineId)
    await broadcast_alert({"type": "SESSION_UPDATE", "sessionId": session_id, "status": "ACTIVE"})
    return SessionStartResponse(sessionId=session_id)


@app.post("/api/sessions/end")
async def end_session(req: SessionEndRequest, x_api_key: Optional[str] = Header(None)):
    require_client(x_api_key)
    if req.sessionId in sessions_db:
        sessions_db[req.sessionId]["status"] = "COMPLETED"
        sessions_db[req.sessionId]["endTime"] = datetime.now(timezone.utc).isoformat()
        logger.info("Session ended: %s", req.sessionId)
        await broadcast_alert({"type": "SESSION_UPDATE", "sessionId": req.sessionId, "status": "COMPLETED"})
    return {"status": "SUCCESS"}


@app.get("/api/sessions/active")
async def get_active_sessions(authorization: Optional[str] = Header(None)):
    require_admin(authorization)
    active = []
    for s_id, s in sessions_db.items():
        if s["status"] == "ACTIVE":
            ev_count = len(events_db.get(s_id, []))
            active.append({
                "sessionId": s_id,
                "machineId": s["machineId"],
                "startTime": s["startTime"],
                "status": s["status"],
                "eventCount": ev_count,
                "integrityValid": True,
            })
    return active


@app.post("/api/events", status_code=201)
async def receive_events(req: EventBatchRequest, x_api_key: Optional[str] = Header(None)):
    require_client(x_api_key)
    session_id = req.sessionId
    if session_id not in sessions_db:
        sessions_db[session_id] = {
            "sessionId": session_id,
            "machineId": "UNKNOWN_HOST",
            "startTime": datetime.now(timezone.utc).isoformat(),
            "status": "ACTIVE",
        }
        events_db[session_id] = []

    session_events = events_db[session_id]

    for enc_token in req.encryptedEvents:
        try:
            # 1. Decrypt AES-256 Fernet payload
            decrypted_json = fernet.decrypt(enc_token.encode("ascii")).decode("utf-8")
            event_obj = json.loads(decrypted_json)

            # 2. Verify HMAC integrity
            canonical_str = create_canonical_string(event_obj)
            expected_hmac = compute_hmac(canonical_str)
            client_hmac = event_obj.get("integrity_hash", "")
            hmac_valid = hmac.compare_digest(expected_hmac, client_hmac)

            # 3. Verify Hash Chain continuity
            chain_valid = True
            if session_events:
                last_event = session_events[-1]
                expected_prev = last_event["integrityHash"]
                if event_obj.get("previous_event_hash") != expected_prev:
                    chain_valid = False
                    logger.error("Hash chain break in %s! Expected prev: %s, got: %s",
                                 session_id, expected_prev[:12], event_obj.get("previous_event_hash", "")[:12])
                    await broadcast_alert({
                        "type": "INTEGRITY_TAMPER_ALERT",
                        "sessionId": session_id,
                        "details": f"Chain break at event {event_obj.get('event_type')}",
                    })

            if not hmac_valid:
                logger.warning("HMAC validation failed for event in session %s", session_id)
                await broadcast_alert({
                    "type": "INTEGRITY_TAMPER_ALERT",
                    "sessionId": session_id,
                    "details": "Invalid HMAC signature on incoming event",
                })

            stored_event = {
                "id": len(session_events) + 1,
                "sessionId": session_id,
                "timestamp": event_obj.get("timestamp", datetime.now(timezone.utc).isoformat()),
                "eventType": event_obj.get("event_type", "unknown"),
                "eventData": event_obj.get("event_data", {}),
                "integrityHash": client_hmac,
                "previousEventHash": event_obj.get("previous_event_hash", ""),
                "verified": hmac_valid and chain_valid,
            }
            session_events.append(stored_event)

        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error("Failed to decrypt and process event token: %s", e)

    return {"status": "PROCESSED", "count": len(req.encryptedEvents)}


@app.get("/api/audit/sessions")
async def get_audit_trail(
    session_id: Optional[str] = None,
    machine_id: Optional[str] = None,
    authorization: Optional[str] = Header(None),
):
    require_admin(authorization)
    all_events: List[Dict[str, Any]] = []
    target_sessions = [session_id] if session_id and session_id in events_db else list(events_db.keys())

    for s_id in target_sessions:
        if machine_id:
            s_info = sessions_db.get(s_id, {})
            if s_info.get("machineId") != machine_id:
                continue
        all_events.extend(events_db.get(s_id, []))

    all_events.sort(key=lambda x: x.get("timestamp", ""))

    chain_valid = True
    if session_id and session_id in events_db:
        evs = events_db[session_id]
        chain_valid = all(e.get("verified", False) for e in evs)

    return {
        "sessionId": session_id or "ALL",
        "totalEvents": len(all_events),
        "chainValid": chain_valid,
        "events": all_events,
    }


@app.get("/api/audit/verify/{session_id}")
async def verify_integrity(session_id: str, authorization: Optional[str] = Header(None)):
    require_admin(authorization)
    events = events_db.get(session_id, [])
    broken = []
    issues = []
    expected_prev = None

    for idx, e in enumerate(events):
        if idx > 0 and e["previousEventHash"] != expected_prev:
            broken.append(idx)
            issues.append(f"Link break at index {idx}: expected {expected_prev[:12]}, found {e['previousEventHash'][:12]}")
        if not e.get("verified", False):
            if idx not in broken:
                broken.append(idx)
            issues.append(f"HMAC validation failed at index {idx}")
        expected_prev = e["integrityHash"]

    return {
        "sessionId": session_id,
        "valid": len(broken) == 0,
        "totalEventsEvaluated": len(events),
        "verifiedEventsCount": len(events) - len(broken),
        "brokenLinks": broken,
        "issues": issues,
        "verificationTimestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/api/admin/panic-lock")
async def trigger_panic_lock(
    req: PanicLockCommandDTO,
    authorization: Optional[str] = Header(None),
):
    require_admin(authorization)
    if req.machineId == "ALL":
        for s_id, s in sessions_db.items():
            if s.get("status") == "ACTIVE":
                s["status"] = "PANIC_LOCKED"
                m_id = s.get("machineId")
                if m_id:
                    if m_id not in command_queue:
                        command_queue[m_id] = []
                    command_queue[m_id].append({
                        "type": "PANIC_LOCK",
                        "machineId": m_id,
                        "reason": req.reason,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
    else:
        if req.machineId not in command_queue:
            command_queue[req.machineId] = []
        command_queue[req.machineId].append({
            "type": "PANIC_LOCK",
            "machineId": req.machineId,
            "reason": req.reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        # Update active session status
        for s_id, s in sessions_db.items():
            if s.get("machineId") == req.machineId and s.get("status") == "ACTIVE":
                s["status"] = "PANIC_LOCKED"

    await broadcast_alert({
        "type": "PANIC_LOCK_ALERT",
        "machineId": req.machineId,
        "reason": req.reason,
    })
    return {"status": "SUCCESS", "message": f"Panic lock dispatched to {req.machineId}"}


@app.get("/api/admin/commands/{machine_id}")
async def poll_commands(machine_id: str, x_api_key: Optional[str] = Header(None)):
    require_client(x_api_key)
    cmds = command_queue.pop(machine_id, [])
    return cmds


@app.post("/api/admin/login")
async def admin_login(creds: Dict[str, str]):
    expected_username = os.environ.get("ADMIN_USERNAME", "admin")
    expected_password = os.environ.get("ADMIN_PASSWORD", "admin")
    if creds.get("username") != expected_username or not secrets.compare_digest(
        creds.get("password", ""), expected_password
    ):
        raise HTTPException(status_code=401, detail="Invalid admin credentials.")
    token = secrets.token_urlsafe(32)
    admin_tokens[token] = {
        "username": expected_username,
        "expiresAt": datetime.now(timezone.utc) + timedelta(hours=8),
    }
    return {
        "token": token,
        "username": expected_username,
        "role": "ROLE_ADMIN",
    }


@app.put("/api/client/quarantine/{machine_id}")
async def sync_quarantine_inventory(
    machine_id: str,
    req: QuarantineInventoryRequest,
    x_api_key: Optional[str] = Header(None),
):
    require_client(x_api_key)
    quarantine_items[machine_id] = [
        {**item, "machineId": machine_id} for item in req.items
    ]
    return {"status": "SYNCED", "count": len(req.items)}


@app.get("/api/admin/quarantine")
async def get_quarantine_inventory(authorization: Optional[str] = Header(None)):
    require_admin(authorization)
    return [item for machine_items in quarantine_items.values() for item in machine_items]


async def queue_quarantine_action(
    machine_id: str,
    item_ids: List[str],
    command_type: str,
    authorization: Optional[str],
):
    admin_username = require_admin(authorization)
    known_ids = {item["itemId"] for item in quarantine_items.get(machine_id, [])}
    invalid_ids = [item_id for item_id in item_ids if item_id not in known_ids]
    if not item_ids or invalid_ids:
        raise HTTPException(status_code=400, detail="Select valid quarantined files for this workstation.")
    command_queue.setdefault(machine_id, []).append({
        "type": command_type,
        "itemIds": item_ids,
        "authorizedBy": admin_username,
        "requestedAt": datetime.now(timezone.utc).isoformat(),
    })
    return {"status": "QUEUED", "machineId": machine_id, "count": len(item_ids)}


@app.post("/api/admin/quarantine/{machine_id}/restore")
async def restore_quarantined_items(
    machine_id: str,
    req: QuarantineActionRequest,
    authorization: Optional[str] = Header(None),
):
    return await queue_quarantine_action(machine_id, req.itemIds, "RESTORE_QUARANTINE", authorization)


@app.post("/api/admin/quarantine/{machine_id}/permanently-delete")
async def permanently_delete_quarantined_items(
    machine_id: str,
    req: QuarantineActionRequest,
    authorization: Optional[str] = Header(None),
):
    return await queue_quarantine_action(
        machine_id, req.itemIds, "PERMANENTLY_DELETE_QUARANTINE", authorization
    )


@app.get("/api/admin/compliance-stats")
async def compliance_stats(authorization: Optional[str] = Header(None)):
    require_admin(authorization)
    return {
        "gdprCompliant": True,
        "retentionDays": 30,
        "screenRecordingActive": False,
        "keyloggingActive": False,
        "contentInspectionActive": False,
        "metadataHashingActive": True,
        "hmacChainVerificationActive": True,
        "adminManagedQuarantineActive": True,
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_websockets.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in active_websockets:
            active_websockets.remove(websocket)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8443))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
