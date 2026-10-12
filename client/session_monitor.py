"""
Session Monitor for Windows Public Computers.
Responsibilities:
- Tracks Windows user login/logout
- Computes user idle time via Win32 GetLastInputInfo
- Manages session lifecycle state machine (ACTIVE, IDLE, LOCKED, LOGGED_OUT, PANIC_LOCKED)
- Triggers isolation & cleanup on termination
- Provides instant Panic Lock feature
"""

import ctypes
import logging
import os
import threading
import time
import uuid
from typing import Optional

from client.cleanup_engine import CleanupEngine
from client.session_downloads import SessionDownloads
from client.monitors.file_monitor import FileSystemMonitor
from client.monitors.network_monitor import NetworkMonitor
from client.monitors.process_monitor import ProcessMonitor
from client.session_recorder import PrivacyPreservingSessionRecorder

logger = logging.getLogger(__name__)


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_uint),
        ("dwTime", ctypes.c_uint),
    ]


class SessionMonitor:
    """
    Orchestrates session lifecycle, monitors, idle tracking, and panic lock.
    """

    STATE_ACTIVE = "ACTIVE"
    STATE_IDLE = "IDLE"
    STATE_LOCKED = "LOCKED"
    STATE_LOGGED_OUT = "LOGGED_OUT"
    STATE_PANIC_LOCKED = "PANIC_LOCKED"

    def __init__(
        self,
        machine_id: str,
        api_client,
        aes_key: Optional[str] = None,
        hmac_key: Optional[str] = None,
        idle_timeout_seconds: int = 900,  # 15 minutes
        poll_interval: float = 2.0,
    ):
        self.machine_id = machine_id
        self.api_client = api_client
        self.aes_key = aes_key
        self.hmac_key = hmac_key
        self.idle_timeout_seconds = idle_timeout_seconds
        self.poll_interval = poll_interval

        self.current_state = self.STATE_LOGGED_OUT
        self.current_session_id: Optional[str] = None
        self.recorder: Optional[PrivacyPreservingSessionRecorder] = None
        self.cleanup_engine = CleanupEngine()
        self.session_downloads = SessionDownloads()
        self.session_downloads_dir: Optional[str] = None

        # Child monitors
        self.proc_monitor: Optional[ProcessMonitor] = None
        self.file_monitor: Optional[FileSystemMonitor] = None
        self.net_monitor: Optional[NetworkMonitor] = None

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()

    def get_idle_seconds(self) -> float:
        """
        Returns number of seconds since last keyboard or mouse input on Windows.
        """
        try:
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            lii = LASTINPUTINFO()
            lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
            if user32.GetLastInputInfo(ctypes.byref(lii)):
                millis = kernel32.GetTickCount() - lii.dwTime
                return max(0.0, millis / 1000.0)
        except Exception as e:
            logger.debug("Error reading GetLastInputInfo: %s", e)
        return 0.0

    def on_user_login(self) -> str:
        """
        Initializes a fresh user session and starts all monitors.
        """
        with self._lock:
            # Generate fallback ID or obtain from backend
            remote_id = None
            if self.api_client:
                remote_id = self.api_client.start_session(self.machine_id)

            self.current_session_id = remote_id or f"sess_{self.machine_id}_{uuid.uuid4().hex[:12]}"
            self.session_downloads_dir = self.session_downloads.start_session(
                self.machine_id, self.current_session_id
            )
            self.current_state = self.STATE_ACTIVE

            # Initialize Privacy Preserving Recorder
            self.recorder = PrivacyPreservingSessionRecorder(
                session_id=self.current_session_id,
                api_client=self.api_client,
                aes_key=self.aes_key,
                hmac_key=self.hmac_key,
            )

            # Record session startup event
            self.recorder.record_event("session_lifecycle", {
                "action": "login",
                "machine_id": self.machine_id,
                "status": "ACTIVE",
            })

            # Start child collectors
            self.proc_monitor = ProcessMonitor(self.recorder, poll_interval=3.0)
            self.file_monitor = FileSystemMonitor(
                self.recorder,
                session_downloads_dir=self.session_downloads_dir,
            )
            self.net_monitor = NetworkMonitor(self.recorder, poll_interval=6.0)

            self.proc_monitor.start()
            self.file_monitor.start()
            self.net_monitor.start()

            logger.info("Session %s logged in on machine %s", self.current_session_id, self.machine_id)
            return self.current_session_id

    def on_user_logout(self, session_id: Optional[str] = None) -> None:
        """
        Concludes user session, flushes all audit trails, and executes cleanup engine.
        """
        with self._lock:
            target_id = session_id or self.current_session_id
            if not target_id:
                return

            logger.info("Ending session %s and executing cleanup...", target_id)
            self.current_state = self.STATE_LOGGED_OUT

            # Record logout event prior to monitor shutdown
            if self.recorder:
                self.recorder.record_event("session_lifecycle", {
                    "action": "logout",
                    "machine_id": self.machine_id,
                    "status": "COMPLETED",
                })

            # Stop child monitors
            if self.proc_monitor:
                self.proc_monitor.stop()
            if self.file_monitor:
                self.file_monitor.stop()
            if self.net_monitor:
                self.net_monitor.stop()

            # Flush remaining events
            if self.recorder:
                self.recorder.flush_to_server()

            # Conclude session with backend
            if self.api_client:
                self.api_client.end_session(target_id)

            # Perform isolation cleanup
            try:
                self.cleanup_engine.perform_full_cleanup(self.session_downloads_dir)
            finally:
                self.session_downloads.restore_browser_download_directories()
                self.session_downloads_dir = None
            if self.api_client:
                self.api_client.sync_quarantine_items(self.machine_id, self.cleanup_engine.quarantine.list_items())

            self.current_session_id = None
            self.recorder = None

    def trigger_panic_lock(self) -> None:
        """
        INSTANT PANIC LOCKDOWN:
        Halts monitors, records the panic event, quarantines cleanup targets,
        and locks the Windows workstation.
        """
        with self._lock:
            logger.warning("PANIC LOCK ACTIVATED! Securing machine %s immediately!", self.machine_id)
            self.current_state = self.STATE_PANIC_LOCKED

            if self.recorder:
                self.recorder.record_event("session_lifecycle", {
                    "action": "panic_lock",
                    "machine_id": self.machine_id,
                    "status": "PANIC_LOCKED",
                })
                self.recorder.flush_to_server()

            # Stop monitors
            if self.proc_monitor:
                self.proc_monitor.stop()
            if self.file_monitor:
                self.file_monitor.stop()
            if self.net_monitor:
                self.net_monitor.stop()

            # Perform immediate cleanup
            try:
                self.cleanup_engine.perform_full_cleanup(self.session_downloads_dir)
            finally:
                self.session_downloads.restore_browser_download_directories()
                self.session_downloads_dir = None
            if self.api_client:
                self.api_client.sync_quarantine_items(self.machine_id, self.cleanup_engine.quarantine.list_items())

            # Lock the Windows workstation
            try:
                ctypes.windll.user32.LockWorkStation()
                logger.info("Windows Workstation locked successfully.")
            except Exception as e:
                logger.error("Failed to execute LockWorkStation: %s", e)

    def check_idle_timeout(self) -> bool:
        """
        Checks if user has been inactive beyond the configured threshold.
        """
        if self.current_state != self.STATE_ACTIVE:
            return False

        idle_secs = self.get_idle_seconds()
        if idle_secs >= self.idle_timeout_seconds:
            logger.warning("Session exceeded idle timeout of %ds (actual: %ds). Logging out.", self.idle_timeout_seconds, idle_secs)
            self.on_user_logout()
            return True
        elif idle_secs > 300 and self.current_state == self.STATE_ACTIVE:
            self.current_state = self.STATE_IDLE
        elif idle_secs < 60 and self.current_state == self.STATE_IDLE:
            self.current_state = self.STATE_ACTIVE
        return False

    def _monitor_loop(self) -> None:
        logger.info("SessionMonitor loop active.")
        flush_counter = 0

        while self._running:
            try:
                # 1. Idle timeout verification
                self.check_idle_timeout()

                # 2. Check for backend commands (e.g. panic lock remotely sent by admin)
                if self.api_client:
                    commands = self.api_client.receive_commands(self.machine_id, self.current_session_id)
                    for cmd in commands:
                        cmd_type = cmd.get("type", "").upper()
                        if cmd_type == "PANIC_LOCK":
                            logger.critical("Remote PANIC_LOCK instruction received from Admin!")
                            self.trigger_panic_lock()
                            break
                        elif cmd_type == "RESTORE_QUARANTINE":
                            item_ids = cmd.get("itemIds", [])
                            self.cleanup_engine.quarantine.restore(item_ids)
                            if self.api_client:
                                self.api_client.sync_quarantine_items(
                                    self.machine_id, self.cleanup_engine.quarantine.list_items()
                                )
                        elif cmd_type == "PERMANENTLY_DELETE_QUARANTINE":
                            item_ids = cmd.get("itemIds", [])
                            self.cleanup_engine.quarantine.permanently_delete(item_ids)
                            if self.api_client:
                                self.api_client.sync_quarantine_items(
                                    self.machine_id, self.cleanup_engine.quarantine.list_items()
                                )
                        elif cmd_type == "END_SESSION":
                            logger.info("Remote END_SESSION instruction received.")
                            self.on_user_logout()
                            break

                # 3. Periodic event flush (every ~10 seconds)
                flush_counter += 1
                if flush_counter >= 5:
                    flush_counter = 0
                    if self.recorder:
                        self.recorder.flush_to_server()
                    if self.api_client:
                        self.api_client.sync_quarantine_items(
                            self.machine_id, self.cleanup_engine.quarantine.list_items()
                        )

            except Exception as e:
                logger.error("Error in SessionMonitor loop: %s", e)

            time.sleep(self.poll_interval)

    def start(self) -> None:
        """Starts the session supervisor thread."""
        if self._running:
            return
        if self.api_client:
            self.api_client.sync_quarantine_items(self.machine_id, self.cleanup_engine.quarantine.list_items())
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, name="SessionMonitorLoop", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stops the session supervisor."""
        self._running = False
        if self.current_state == self.STATE_ACTIVE:
            self.on_user_logout()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3.0)
