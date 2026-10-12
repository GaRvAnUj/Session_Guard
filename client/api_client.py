"""
API Client for communication between Python Client and Spring Boot Server.
Features:
- Encrypted event batch dispatch (Base64-wrapped binary)
- Session lifecycle calls (start, end)
- Exponential backoff retry logic
- Command polling (panic lock triggers, configuration updates)
"""

import base64
import logging
import time
from typing import Any, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class APIClient:
    """
    HTTP REST client handling encrypted communications with the Java server.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8443",
        api_key: str = "secure-client-api-key-2026-public-lab",
        verify_ssl: bool = False,
        timeout: int = 10,
        max_retries: int = 3,
        backoff_factor: float = 1.5,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.verify_ssl = verify_ssl
        self.timeout = timeout

        # Session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        self.session.headers.update({
            "Content-Type": "application/json",
            "X-API-KEY": self.api_key,
            "User-Agent": "SecureSessionManager-Client/1.0",
        })

    def start_session(self, machine_id: str) -> Optional[str]:
        """
        Notifies server that a new session has started. Returns server session ID.
        """
        url = f"{self.base_url}/api/sessions/start"
        payload = {"machineId": machine_id}

        try:
            logger.info("Requesting session start from server: %s", url)
            resp = self.session.post(url, json=payload, timeout=self.timeout, verify=self.verify_ssl)
            if resp.status_code in (200, 201):
                data = resp.json()
                session_id = data.get("sessionId")
                logger.info("Session established successfully: %s", session_id)
                return session_id
            else:
                logger.error("Failed to start session. Status: %d, Response: %s", resp.status_code, resp.text)
                return None
        except requests.RequestException as e:
            logger.error("Network error while connecting to server start_session: %s", e)
            return None

    def end_session(self, session_id: str) -> bool:
        """
        Notifies server that the current session has concluded.
        """
        url = f"{self.base_url}/api/sessions/end"
        payload = {"sessionId": session_id}

        try:
            resp = self.session.post(url, json=payload, timeout=self.timeout, verify=self.verify_ssl)
            if resp.status_code == 200:
                logger.info("Session %s successfully ended on server.", session_id)
                return True
            logger.warning("End session responded with status %d: %s", resp.status_code, resp.text)
            return False
        except requests.RequestException as e:
            logger.error("Network error ending session: %s", e)
            return False

    def send_events(self, session_id: str, encrypted_events: List[bytes]) -> bool:
        """
        Transmits a batch of AES-256 encrypted events to /api/events.
        """
        if not encrypted_events:
            return True

        url = f"{self.base_url}/api/events"
        # Convert Fernet token bytes to ASCII strings
        b64_events = [evt.decode("ascii") if isinstance(evt, bytes) else str(evt) for evt in encrypted_events]

        payload = {
            "sessionId": session_id,
            "encryptedEvents": b64_events,
            "batchCount": len(b64_events),
        }

        try:
            resp = self.session.post(url, json=payload, timeout=self.timeout, verify=self.verify_ssl)
            if resp.status_code in (200, 201, 202):
                return True
            logger.warning("Failed to send events. Status: %d, Message: %s", resp.status_code, resp.text)
            return False
        except requests.RequestException as e:
            logger.error("Failed to send events to server: %s", e)
            return False

    def receive_commands(self, machine_id: str, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Polls server for administrative commands (e.g. panic lock, screen freeze, policy change).
        """
        url = f"{self.base_url}/api/admin/commands/{machine_id}"
        params = {}
        if session_id:
            params["sessionId"] = session_id

        try:
            resp = self.session.get(url, params=params, timeout=5, verify=self.verify_ssl)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and "commands" in data:
                    return data["commands"]
            logger.error(
                "Command polling failed for machine %s. Status: %d, Response: %s",
                machine_id,
                resp.status_code,
                resp.text,
            )
            return []
        except requests.RequestException:
            # Polling timeouts are expected when server has no commands
            return []

    def sync_quarantine_items(self, machine_id: str, items: List[Dict[str, Any]]) -> bool:
        url = f"{self.base_url}/api/client/quarantine/{machine_id}"
        try:
            resp = self.session.put(url, json={"items": items}, timeout=self.timeout, verify=self.verify_ssl)
            if resp.status_code == 200:
                return True
            logger.error("Failed to sync quarantine inventory. Status: %d, Response: %s", resp.status_code, resp.text)
            return False
        except requests.RequestException as e:
            logger.error("Network error syncing quarantine inventory: %s", e)
            return False
