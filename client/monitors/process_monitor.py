"""
Process Monitor for Windows Public Computers.
Uses psutil to monitor running processes, tracking process creation and termination
with resource utilization metrics (CPU/RAM).
"""

import logging
import threading
import time
from typing import Dict, List, Optional, Set

import psutil

logger = logging.getLogger(__name__)


class ProcessMonitor:
    """
    Monitors process life cycle events and reports them to the session recorder.
    """

    DEFAULT_EXCLUDED = {
        "system idle process",
        "system",
        "registry",
        "smss.exe",
        "csrss.exe",
        "wininit.exe",
        "services.exe",
        "lsass.exe",
        "svchost.exe",
        "fontdrvhost.exe",
        "dwm.exe",
    }

    def __init__(
        self,
        recorder,
        poll_interval: float = 3.0,
        excluded_processes: Optional[List[str]] = None,
    ):
        self.recorder = recorder
        self.poll_interval = poll_interval
        self.excluded = set(p.lower() for p in (excluded_processes or [])) | self.DEFAULT_EXCLUDED
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        # Map pid -> process info dict
        self._known_processes: Dict[int, Dict[str, any]] = {}

    def _get_process_info(self, proc: psutil.Process) -> Optional[Dict[str, any]]:
        try:
            pid = proc.pid
            if pid <= 4:
                return None

            name = proc.name()
            if not name or name.lower() in self.excluded:
                return None

            exe = name
            try:
                exe = proc.exe()
            except Exception:
                exe = name

            mem = 0.0
            try:
                mem = proc.memory_info().rss / (1024 * 1024)  # MB
            except Exception:
                mem = 0.0

            return {
                "process_name": name,
                "exe_path": exe,
                "cpu_percent": 0.0,
                "memory_mb": round(mem, 2),
                "pid": pid,
            }
        except Exception:
            return None

    def poll_once(self) -> None:
        """
        Scans currently active processes and generates process_start and process_terminate events.
        """
        current_pids: Set[int] = set()

        for proc in psutil.process_iter(["pid", "name"]):
            pid = proc.info["pid"]
            current_pids.add(pid)

            if pid not in self._known_processes:
                # Newly detected process
                info = self._get_process_info(proc)
                if info:
                    self._known_processes[pid] = info
                    self.recorder.record_event("process_start", {
                        "process_name": info["process_name"],
                        "exe_path": info["exe_path"],
                        "cpu_percent": info["cpu_percent"],
                        "memory_mb": info["memory_mb"],
                    })

        # Check for terminated processes
        terminated_pids = set(self._known_processes.keys()) - current_pids
        for pid in terminated_pids:
            old_info = self._known_processes.pop(pid)
            self.recorder.record_event("process_terminate", {
                "process_name": old_info["process_name"],
                "exe_path": old_info["exe_path"],
                "cpu_percent": 0.0,
                "memory_mb": 0.0,
                "exit_code": 0,
            })

    def _run_loop(self) -> None:
        logger.info("ProcessMonitor thread started (polling every %ss)", self.poll_interval)
        # Initial snapshot without triggering flood of starts if preferred, or trigger initial snapshot
        for proc in psutil.process_iter(["pid"]):
            pid = proc.info["pid"]
            info = self._get_process_info(proc)
            if info:
                self._known_processes[pid] = info

        while not self._stop_event.is_set():
            try:
                self.poll_once()
            except Exception as e:
                logger.error("Error in process monitoring loop: %s", e)
            self._stop_event.wait(self.poll_interval)

        logger.info("ProcessMonitor thread stopped.")

    def start(self) -> None:
        """Starts monitoring in a background daemon thread."""
        if self._running:
            return
        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, name="ProcessMonitorThread", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stops background monitoring."""
        if not self._running:
            return
        self._running = False
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3.0)
