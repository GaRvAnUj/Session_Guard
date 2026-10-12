"""
Unit tests for APIClient.
"""

import base64
import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from client.api_client import APIClient


def test_api_client_initialization():
    client = APIClient(
        base_url="http://localhost:8443",
        api_key="test-key-123",
        timeout=5,
    )
    assert client.base_url == "http://localhost:8443"
    assert client.api_key == "test-key-123"
    assert client.session.headers["X-API-KEY"] == "test-key-123"


def test_api_client_send_empty_events():
    client = APIClient()
    # Sending empty batch returns True immediately without making network calls
    assert client.send_events("test_sess", []) is True
