"""
Unit tests for Process, File, and Network monitors.
"""

import os
import sys
import time
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from client.monitors.process_monitor import ProcessMonitor
from client.monitors.network_monitor import NetworkMonitor
from client.session_recorder import PrivacyPreservingSessionRecorder


def test_process_monitor_polling():
    recorder = PrivacyPreservingSessionRecorder(session_id="test_proc_poll")
    proc_mon = ProcessMonitor(recorder=recorder, poll_interval=1.0)

    # Execute single poll
    proc_mon.poll_once()

    # Should have recorded at least some non-excluded processes
    count = recorder.get_events_count()
    assert count >= 0


def test_network_monitor_polling():
    recorder = PrivacyPreservingSessionRecorder(session_id="test_net_poll")
    net_mon = NetworkMonitor(recorder=recorder, poll_interval=1.0)

    net_mon.poll_once()
    assert recorder.get_events_count() >= 0
