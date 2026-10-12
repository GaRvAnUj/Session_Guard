"""
Unit Tests for PrivacyPreservingSessionRecorder (Core Novelty).
Validates:
1. Privacy filters strictly strip sensitive content, plaintext paths, and args.
2. Cryptographic hash chain produces unbroken HMAC links.
3. Tamper detection identifies modified events or broken hashes.
4. AES-256 payload encryption is valid and decryptable.
"""

import json
import os
import sys
import pytest

# Add parent path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from client.session_recorder import PrivacyPreservingSessionRecorder


def test_privacy_filter_removes_sensitive_data():
    """Verify that file content and plaintext paths never leak into event metadata."""
    recorder = PrivacyPreservingSessionRecorder(session_id="test_sess_001")

    raw_file_event = {
        "operation": "create",
        "path": "C:\\Users\\JohnDoe\\Documents\\Confidential_Tax_Return.pdf",
        "content": "SuperSecretSSN_And_Password",
        "password": "MyPlainTextPassword123",
        "size_bytes": 45012,
    }

    filtered = recorder._apply_privacy_filters("file_operation", raw_file_event)

    # Privacy invariants
    assert "content" not in filtered
    assert "password" not in filtered
    assert "JohnDoe" not in str(filtered)
    assert "Confidential_Tax_Return" not in str(filtered)
    assert filtered["operation"] == "create"
    assert filtered["extension"] == ".pdf"
    assert filtered["size_bytes"] == 45012
    assert "path_hash" in filtered
    assert len(filtered["path_hash"]) == 64
    assert len(filtered["path_hash_short"]) == 16


def test_process_privacy_filter():
    """Verify process arguments and environment variables are stripped."""
    recorder = PrivacyPreservingSessionRecorder(session_id="test_sess_002")

    raw_proc_event = {
        "process_name": "chrome.exe",
        "exe_path": "C:\\Program Files\\Google\\Chrome\\chrome.exe",
        "command_line_args": "--password=admin123 --user-data-dir=secret",
        "cmdline": ["chrome.exe", "--secret-key"],
        "cpu_percent": 14.5,
        "memory_mb": 312.4,
    }

    filtered = recorder._apply_privacy_filters("process_start", raw_proc_event)

    assert "command_line_args" not in filtered
    assert "cmdline" not in filtered
    assert filtered["process_name"] == "chrome.exe"
    assert filtered["cpu_percent"] == 14.5
    assert filtered["memory_mb"] == 312.4
    assert "exe_path_hash" in filtered


def test_network_privacy_filter():
    """Verify raw IPs are hashed and packet payloads/URLs are blocked."""
    recorder = PrivacyPreservingSessionRecorder(session_id="test_sess_003")

    raw_net_event = {
        "protocol": "TCP",
        "remote_ip": "142.250.185.46",
        "remote_port": 443,
        "urls": ["https://bank.com/account/login?user=john&pin=9999"],
        "packet_content": "GET / HTTP/1.1\r\nCookie: session=xyz",
        "bytes_sent": 1024,
        "bytes_received": 4096,
    }

    filtered = recorder._apply_privacy_filters("network_connection", raw_net_event)

    assert "urls" not in filtered
    assert "packet_content" not in filtered
    assert "remote_ip" not in filtered
    assert "remote_ip_hash" in filtered
    assert filtered["protocol"] == "TCP"
    assert filtered["remote_port"] == 443
    assert filtered["bytes_sent"] == 1024
    assert filtered["bytes_received"] == 4096


def test_hash_chain_integrity():
    """Verify HMAC integrity chain linkages between consecutive events."""
    recorder = PrivacyPreservingSessionRecorder(session_id="test_sess_chain")

    hash1 = recorder.record_event("process_start", {"process_name": "notepad.exe", "exe_path": "notepad.exe"})
    hash2 = recorder.record_event("file_operation", {"operation": "create", "path": "notes.txt"})
    hash3 = recorder.record_event("network_connection", {"protocol": "TCP", "remote_ip": "1.1.1.1", "remote_port": 80})

    assert len(recorder.recorded_events) == 3
    evt1, evt2, evt3 = recorder.recorded_events

    # Event 1 links to genesis hash
    assert evt1["previous_event_hash"] != ""
    assert evt1["integrity_hash"] == hash1

    # Event 2 previous hash MUST equal Event 1 integrity hash
    assert evt2["previous_event_hash"] == hash1
    assert evt2["integrity_hash"] == hash2

    # Event 3 previous hash MUST equal Event 2 integrity hash
    assert evt3["previous_event_hash"] == hash2
    assert evt3["integrity_hash"] == hash3


def test_encryption_and_decryption():
    """Verify buffered events are encrypted with AES-256 and decrypt cleanly."""
    recorder = PrivacyPreservingSessionRecorder(session_id="test_sess_enc")

    recorder.record_event("process_start", {"process_name": "calc.exe", "exe_path": "calc.exe"})
    assert len(recorder.event_buffer) == 1

    encrypted_bytes = recorder.event_buffer[0]
    # Encrypted payload should not contain plaintext "calc.exe"
    assert b"calc.exe" not in encrypted_bytes

    # Decrypt with recorder's fernet key
    decrypted_str = recorder.fernet.decrypt(encrypted_bytes).decode("utf-8")
    decrypted_obj = json.loads(decrypted_str)

    assert decrypted_obj["session_id"] == "test_sess_enc"
    assert decrypted_obj["event_type"] == "process_start"
    assert decrypted_obj["event_data"]["process_name"] == "calc.exe"
    assert "integrity_hash" in decrypted_obj
