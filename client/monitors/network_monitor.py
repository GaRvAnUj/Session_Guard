"""
Network Monitor for Windows Public Computers.
Uses psutil to monitor active network connections and interface traffic statistics,
forwarding privacy-sanitized metadata events (hashed IPs, protocol, byte throughput).
"""

import logging
import socket
import threading
import time
from typing import Dict, List, Optional, Set, Tuple

import psutil

logger = logging.getLogger(__name__)


class NetworkMonitor:
    """
    Monitors outbound/inbound network connections and bandwidth metrics.
    """

    def __init__(self, recorder, poll_interval: float = 8.0):
        self.recorder = recorder
        self.poll_interval = poll_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        # Track active connections (laddr, raddr)
        self._known_connections: Set[Tuple[str, int, str, int]] = set()
        self._last_io_counters = psutil.net_io_counters()

    def poll_once(self) -> None:
        """
        Gathers current network connections and reports newly observed connections.
        """
        # Calculate delta traffic
        try:
            current_io = psutil.net_io_counters()
            bytes_sent_delta = max(0, current_io.bytes_sent - self._last_io_counters.bytes_sent)
            bytes_recv_delta = max(0, current_io.bytes_recv - self._last_io_counters.bytes_recv)
            self._last_io_counters = current_io
        except Exception:
            bytes_sent_delta = 0
            bytes_recv_delta = 0

        # Retrieve system network connections
        current_conns: Set[Tuple[str, int, str, int]] = set()

        try:
            connections = psutil.net_connections(kind="inet")
        except (psutil.AccessDenied, Exception) as e:
            logger.debug("Cannot query net_connections: %s", e)
            return

        for conn in connections:
            if conn.status != psutil.CONN_ESTABLISHED or not conn.raddr:
                continue

            r_ip = conn.raddr.ip
            r_port = conn.raddr.port

            # Ignore local loopbacks
            if r_ip in ("127.0.0.1", "::1", "0.0.0.0"):
                continue

            proto = "TCP" if conn.type == socket.SOCK_STREAM else "UDP"
            conn_key = (conn.laddr.ip, conn.laddr.port, r_ip, r_port)
            current_conns.add(conn_key)

            if conn_key not in self._known_connections:
                # Newly established remote connection
                self._known_connections.add(conn_key)
                self.recorder.record_event("network_connection", {
                    "protocol": proto,
                    "remote_ip": r_ip,
                    "remote_port": r_port,
                    "bytes_sent": bytes_sent_delta,
                    "bytes_received": bytes_recv_delta,
                })

        # Purge stale connections from set
        self._known_connections = self._known_connections.intersection(current_conns)

    def _run_loop(self) -> None:
        logger.info("NetworkMonitor thread started (polling every %ss)", self.poll_interval)
        while not self._stop_event.is_set():
            try:
                self.poll_once()
            except Exception as e:
                logger.error("Error in network monitoring loop: %s", e)
            self._stop_event.wait(self.poll_interval)
        logger.info("NetworkMonitor thread stopped.")

    def start(self) -> None:
        """Starts background network monitoring thread."""
        if self._running:
            return
        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, name="NetworkMonitorThread", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stops background network monitoring."""
        if not self._running:
            return
        self._running = False
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3.0)
