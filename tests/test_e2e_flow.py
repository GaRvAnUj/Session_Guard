"""
End-to-End Integration Test for Secure Session Manager.
Validates the complete pipeline:
1. Session start via API
2. Privacy-preserving recording with cryptographic HMAC chain
3. AES-256 Fernet encrypted transmission
4. Backend decryption and HMAC verification
5. Hash chain integrity audit verification
6. Remote Panic Lock trigger & command delivery
7. Session conclusion and isolation cleanup
"""

import os
import sys
import pytest
from starlette.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from server.server_runner import app
from client.api_client import APIClient
from client.session_recorder import PrivacyPreservingSessionRecorder
from client.cleanup_engine import CleanupEngine


@pytest.fixture
def test_client():
    return TestClient(app)


def test_e2e_session_recording_and_integrity_verification(test_client):
    client_headers = {"X-API-KEY": "secure-client-api-key-2026-public-lab"}

    # 1. Start Session
    start_resp = test_client.post(
        "/api/sessions/start",
        json={"machineId": "PC_LAB_E2E"},
        headers=client_headers,
    )
    assert start_resp.status_code == 200
    session_id = start_resp.json()["sessionId"]
    assert "PC_LAB_E2E" in session_id

    # 2. Record privacy-filtered events on client with shared demo keys
    aes_key = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
    hmac_key = "c2VjdXJlLXNlc3Npb24tbWFuYWdlci1obWFjLXNlY3JldC0yNTY="
    recorder = PrivacyPreservingSessionRecorder(session_id=session_id, aes_key=aes_key, hmac_key=hmac_key)

    hash1 = recorder.record_event("process_start", {
        "process_name": "notepad.exe",
        "exe_path": "C:\\Windows\\notepad.exe",
        "command_line_args": "--confidential-flag",
        "cpu_percent": 2.1,
        "memory_mb": 45.0,
    })

    hash2 = recorder.record_event("file_operation", {
        "operation": "create",
        "path": "C:\\Users\\Student\\Documents\\MyResearch.pdf",
        "content": "SecretEssayContent",
        "size_bytes": 1048576,
    })

    hash3 = recorder.record_event("network_connection", {
        "protocol": "TCP",
        "remote_ip": "172.217.16.206",
        "remote_port": 443,
        "bytes_sent": 512,
        "bytes_received": 2048,
    })

    assert len(recorder.event_buffer) == 3

    # 3. Transmit encrypted events to server
    session_token = test_client.post(
        "/api/admin/login",
        json={"username": "admin", "password": "admin"},
    ).json()["token"]
    admin_headers = {"Authorization": f"Bearer {session_token}"}
    batch_tokens = [e.decode("ascii") if isinstance(e, bytes) else str(e) for e in recorder.event_buffer]
    ev_resp = test_client.post("/api/events", json={
        "sessionId": session_id,
        "encryptedEvents": batch_tokens,
    }, headers=client_headers)
    assert ev_resp.status_code == 201

    # 4. Fetch Audit Trail via Admin API
    audit_resp = test_client.get(f"/api/audit/sessions?session_id={session_id}", headers=admin_headers)
    assert audit_resp.status_code == 200
    audit_data = audit_resp.json()

    assert audit_data["totalEvents"] == 3
    assert audit_data["chainValid"] is True

    events = audit_data["events"]
    # Check that privacy is strictly preserved
    for ev in events:
        data = ev["eventData"]
        # Invariants: No content, no raw paths, verified flag is true
        assert "content" not in data
        assert "command_line_args" not in data
        assert ev["verified"] is True

    # 5. Verify Cryptographic Integrity Endpoint
    verify_resp = test_client.get(f"/api/audit/verify/{session_id}", headers=admin_headers)
    assert verify_resp.status_code == 200
    verify_data = verify_resp.json()

    assert verify_data["valid"] is True
    assert verify_data["totalEventsEvaluated"] == 3
    assert len(verify_data["brokenLinks"]) == 0

    # 6. Test Panic Lock Trigger
    panic_resp = test_client.post("/api/admin/panic-lock", json={
        "machineId": "PC_LAB_E2E",
        "reason": "Suspicious tampering detected",
    }, headers=admin_headers)
    assert panic_resp.status_code == 200

    # Check client retrieves command
    cmd_resp = test_client.get(
        "/api/admin/commands/PC_LAB_E2E",
        headers={"X-API-KEY": "secure-client-api-key-2026-public-lab"},
    )
    assert cmd_resp.status_code == 200
    cmds = cmd_resp.json()
    assert len(cmds) == 1
    assert cmds[0]["type"] == "PANIC_LOCK"

    # 7. End session
    end_resp = test_client.post(
        "/api/sessions/end",
        json={"sessionId": session_id},
        headers=client_headers,
    )
    assert end_resp.status_code == 200


def test_quarantine_inventory_requires_admin_and_actions_are_selected(test_client):
    machine_id = "PC_QUARANTINE_E2E"
    item = {
        "itemId": "selected-file-id",
        "fileName": "notes.txt",
        "relativePath": "notes.txt",
        "category": "downloads",
        "sizeBytes": 25,
        "quarantinedAt": "2026-10-07T00:00:00+00:00",
    }
    client_headers = {"X-API-KEY": "secure-client-api-key-2026-public-lab"}

    sync = test_client.put(
        f"/api/client/quarantine/{machine_id}",
        json={"items": [item]},
        headers=client_headers,
    )
    assert sync.status_code == 200
    assert test_client.get("/api/admin/quarantine").status_code == 401
    assert test_client.get("/api/sessions/active").status_code == 401
    assert test_client.get("/api/admin/compliance-stats").status_code == 401
    assert test_client.post(
        "/api/admin/panic-lock",
        json={"machineId": machine_id, "reason": "Unauthorized attempt"},
    ).status_code == 401

    login = test_client.post("/api/admin/login", json={"username": "admin", "password": "admin"})
    assert login.status_code == 200
    admin_headers = {"Authorization": f"Bearer {login.json()['token']}"}
    inventory = test_client.get("/api/admin/quarantine", headers=admin_headers)
    assert inventory.status_code == 200
    assert inventory.json()[0]["itemId"] == "selected-file-id"

    denied = test_client.post(
        f"/api/admin/quarantine/{machine_id}/permanently-delete",
        json={"itemIds": ["selected-file-id"]},
    )
    assert denied.status_code == 401
    restore_queued = test_client.post(
        f"/api/admin/quarantine/{machine_id}/restore",
        json={"itemIds": ["selected-file-id"]},
        headers=admin_headers,
    )
    assert restore_queued.status_code == 200
    queued = test_client.post(
        f"/api/admin/quarantine/{machine_id}/permanently-delete",
        json={"itemIds": ["selected-file-id"]},
        headers=admin_headers,
    )
    assert queued.status_code == 200
    assert queued.json()["count"] == 1

    commands = test_client.get(f"/api/admin/commands/{machine_id}", headers=client_headers)
    assert commands.status_code == 200
    assert [command["type"] for command in commands.json()] == [
        "RESTORE_QUARANTINE",
        "PERMANENTLY_DELETE_QUARANTINE",
    ]
    assert all(command["itemIds"] == ["selected-file-id"] for command in commands.json())
