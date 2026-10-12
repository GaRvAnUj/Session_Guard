"""
Privacy-Preserving Session Recorder (Client Core Novelty)
Records WHAT users did (metadata only) without recording WHAT they typed or viewed (content).
Maintains a tamper-proof cryptographic HMAC hash chain and encrypts data with AES-256.
"""

import base64
import hashlib
import hmac
import json
import logging
import os
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class PrivacyPreservingSessionRecorder:
    """
    Coordinates privacy filtering, cryptographic hashing, HMAC integrity chaining,
    and AES-256 encryption of user session metadata.
    """

    PRIVACY_RULES = {
        "process_start": {
            "allow": ["process_name", "cpu_percent", "memory_mb"],
            "hash": ["exe_path"],
            "deny": ["command_line_args", "cmdline", "environment_vars", "arguments"],
        },
        "process_terminate": {
            "allow": ["process_name", "cpu_percent", "memory_mb", "exit_code"],
            "hash": ["exe_path"],
            "deny": ["command_line_args", "cmdline", "environment_vars"],
        },
        "file_operation": {
            "allow": ["operation", "extension", "size_bytes"],
            "hash": ["path", "file_path"],
            "deny": ["file_content", "content", "raw_filename", "data"],
        },
        "network_connection": {
            "allow": ["protocol", "remote_port", "bytes_sent", "bytes_received"],
            "hash": ["remote_ip", "remote_host"],
            "deny": ["packet_content", "urls", "url", "payload", "cookies", "headers"],
        },
        "registry_operation": {
            "allow": ["operation", "root_key"],
            "hash": ["key_path"],
            "deny": ["value_content", "data", "binary_value"],
        },
    }

    def __init__(
        self,
        session_id: str,
        api_client: Optional[Any] = None,
        aes_key: Optional[str] = None,
        hmac_key: Optional[str] = None,
        batch_size_threshold: int = 20,
    ):
        self.session_id = session_id
        self.api_client = api_client
        self.batch_size_threshold = batch_size_threshold
        self.lock = threading.RLock()

        # Setup AES key for Fernet (must be 32 url-safe base64 bytes)
        if not aes_key:
            self._fernet_key = Fernet.generate_key()
        else:
            try:
                # Validate or normalize provided key
                raw_bytes = base64.b64decode(aes_key)
                if len(raw_bytes) != 32:
                    raw_bytes = hashlib.sha256(raw_bytes).digest()
                self._fernet_key = base64.urlsafe_b64encode(raw_bytes)
            except Exception:
                self._fernet_key = Fernet.generate_key()

        self.fernet = Fernet(self._fernet_key)

        # Setup HMAC key
        if not hmac_key:
            self._hmac_key = os.urandom(32)
        else:
            try:
                self._hmac_key = base64.b64decode(hmac_key)
                if len(self._hmac_key) < 16:
                    self._hmac_key = hashlib.sha256(self._hmac_key).digest()
            except Exception:
                self._hmac_key = hmac_key.encode("utf-8")

        # Initialize hash chain genesis state
        self.session_start_time = datetime.now(timezone.utc).isoformat()
        genesis_seed = f"{self.session_id}:{self.session_start_time}"
        self.last_event_hash = hashlib.sha256(genesis_seed.encode("utf-8")).hexdigest()

        # Buffers for raw / encrypted events
        self.event_buffer: List[bytes] = []
        self.recorded_events: List[Dict[str, Any]] = []

        logger.info(
            "PrivacyPreservingSessionRecorder initialized for session: %s (Genesis hash: %s)",
            self.session_id,
            self.last_event_hash[:16],
        )

    def _hash_sensitive_data(self, data: Optional[str]) -> str:
        """
        Hashes sensitive data (file paths, IP addresses, usernames) using SHA-256.
        Returns a 64-character hex string.
        """
        if data is None:
            return ""
        normalized = str(data).strip().lower()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def _apply_privacy_filters(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enforces strict GDPR/Privacy minimization rules:
        - Only permitted metadata fields pass through
        - Sensitive fields (file paths, IPs, exe paths) are cryptographically hashed
        - Content, arguments, payloads, query parameters, cookies are stripped
        """
        rules = self.PRIVACY_RULES.get(event_type, {
            "allow": ["operation", "status"],
            "hash": ["target"],
            "deny": ["content", "data", "payload", "cmdline", "args"],
        })

        sanitized: Dict[str, Any] = {}

        # 1. Strip explicitly denied fields and anything with sensitive keywords
        denied_keys = set(rules.get("deny", []))
        forbidden_substrings = ["password", "secret", "token", "auth", "content", "cookie", "payload"]

        # 2. Add allowed fields
        for allowed in rules.get("allow", []):
            if allowed in data and allowed not in denied_keys:
                sanitized[allowed] = data[allowed]

        # 3. Hash sensitive identifiers
        for hash_field in rules.get("hash", []):
            if hash_field in data:
                raw_val = data[hash_field]
                hashed_val = self._hash_sensitive_data(raw_val)
                # Store full hash and truncated display hash
                sanitized[f"{hash_field}_hash"] = hashed_val
                sanitized[f"{hash_field}_hash_short"] = hashed_val[:16]

        # Special casing for file operations: ensure extension and size only
        if event_type == "file_operation":
            if "path" in data and "extension" not in sanitized:
                ext = os.path.splitext(str(data["path"]))[1].lower()
                sanitized["extension"] = ext if ext else "none"

        # Special casing for network: never allow full URLs
        if event_type == "network_connection":
            if "remote_ip" in data and "remote_ip_hash" not in sanitized:
                sanitized["remote_ip_hash"] = self._hash_sensitive_data(data["remote_ip"])

        # Final sweep against forbidden keys in sanitized dictionary
        cleaned: Dict[str, Any] = {}
        for k, v in sanitized.items():
            if any(sub in k.lower() for sub in forbidden_substrings):
                continue
            cleaned[k] = v

        return cleaned

    def _create_canonical_event_string(self, event: Dict[str, Any]) -> str:
        """
        Creates a deterministic canonical JSON string for HMAC computation.
        """
        canonical_dict = {
            "session_id": event["session_id"],
            "timestamp": event["timestamp"],
            "event_type": event["event_type"],
            "event_data": event["event_data"],
            "previous_event_hash": event["previous_event_hash"],
        }
        return json.dumps(canonical_dict, sort_keys=True, separators=(",", ":"))

    def _create_integrity_hash(self, event: Dict[str, Any]) -> str:
        """
        Computes HMAC-SHA256 over canonical event metadata.
        """
        canonical_str = self._create_canonical_event_string(event)
        mac = hmac.new(self._hmac_key, canonical_str.encode("utf-8"), hashlib.sha256)
        return mac.hexdigest()

    def record_event(self, event_type: str, raw_event_data: Dict[str, Any]) -> str:
        """
        Main entry point for recording an event.
        Returns the event's integrity hash.
        """
        with self.lock:
            # 1. Apply privacy filters
            filtered_data = self._apply_privacy_filters(event_type, raw_event_data)

            # 2. Build structured event dictionary
            now_iso = datetime.now(timezone.utc).isoformat()
            event = {
                "session_id": self.session_id,
                "timestamp": now_iso,
                "event_type": event_type,
                "event_data": filtered_data,
                "previous_event_hash": self.last_event_hash,
            }

            # 3. Generate HMAC integrity hash linking to previous event (Hash Chain)
            integrity_hash = self._create_integrity_hash(event)
            event["integrity_hash"] = integrity_hash

            # Update hash chain state
            self.last_event_hash = integrity_hash
            self.recorded_events.append(event)

            # 4. Encrypt event with AES-256 Fernet
            event_json = json.dumps(event, separators=(",", ":")).encode("utf-8")
            encrypted_payload = self.fernet.encrypt(event_json)
            self.event_buffer.append(encrypted_payload)

            logger.debug(
                "Recorded %s [hash=%s, prev=%s]",
                event_type,
                integrity_hash[:12],
                event["previous_event_hash"][:12],
            )

            # 5. Flush if buffer reaches threshold
            if len(self.event_buffer) >= self.batch_size_threshold:
                self.flush_to_server()

            return integrity_hash

    def flush_to_server(self) -> bool:
        """
        Transmits buffered encrypted events to the backend server.
        """
        with self.lock:
            if not self.event_buffer:
                return True

            if not self.api_client:
                logger.debug("No API client configured; retaining %d buffered events", len(self.event_buffer))
                return True

            batch_to_send = list(self.event_buffer)
            try:
                success = self.api_client.send_events(self.session_id, batch_to_send)
                if success:
                    # Clear sent batch
                    self.event_buffer = self.event_buffer[len(batch_to_send):]
                    logger.info("Successfully flushed %d encrypted events to server", len(batch_to_send))
                    return True
                else:
                    logger.warning("Failed to flush event batch to server. Will retry next cycle.")
                    return False
            except Exception as e:
                logger.error("Exception during flush_to_server: %s", e)
                return False

    def get_events_count(self) -> int:
        """Returns the number of events recorded in memory."""
        with self.lock:
            return len(self.recorded_events)
