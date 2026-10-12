"""
Unit tests for CleanupEngine.
Validates reversible cleanup and clipboard sanitization.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from client.cleanup_engine import CleanupEngine
from client.quarantine_manager import QuarantineManager


def test_cleanup_engine_uses_reversible_quarantine(tmp_path):
    """Cleanup no longer permanently deletes user data without an admin command."""
    source = tmp_path / "Downloads" / "sensitive_test.dat"
    source.parent.mkdir()
    source.write_text("CONFIDENTIAL STUDENT RECORD DATA 1234567890", encoding="utf-8")
    quarantine = QuarantineManager(str(tmp_path / "quarantine"))
    engine = CleanupEngine(quarantine_manager=quarantine)

    assert engine.sanitize_user_folder(str(source.parent)) == 1
    assert not source.exists()
    item = quarantine.list_items()[0]
    assert item["fileName"] == source.name
    assert quarantine.restore([item["itemId"]]) == [item["itemId"]]
    assert source.read_text(encoding="utf-8") == "CONFIDENTIAL STUDENT RECORD DATA 1234567890"


def test_wipe_clipboard():
    """Verify clipboard wiping does not throw exceptions and clears buffers."""
    engine = CleanupEngine()
    result = engine.wipe_clipboard()
    assert isinstance(result, bool)


def test_browser_directory_files_are_listed_individually_in_quarantine(tmp_path, monkeypatch):
    browser_cache = tmp_path / "profile" / "Google" / "Chrome" / "User Data" / "Default" / "Cache"
    nested = browser_cache / "nested"
    nested.mkdir(parents=True)
    first = browser_cache / "image.bin"
    second = nested / "script.js"
    first.write_bytes(b"image")
    second.write_bytes(b"script")
    local_app_data = tmp_path / "profile"
    monkeypatch.setenv("LOCALAPPDATA", str(local_app_data))
    monkeypatch.setenv("APPDATA", "")
    quarantine = QuarantineManager(str(tmp_path / "quarantine"))
    engine = CleanupEngine(quarantine_manager=quarantine)

    engine.cleanup_browser_data()

    records = quarantine.list_items()
    assert {item["relativePath"] for item in records} >= {"image.bin", os.path.join("nested", "script.js")}
    assert all(item["category"] == "browser-data" for item in records)
    assert not first.exists()
    assert not second.exists()


def test_full_cleanup_quarantines_only_the_session_download_folder(tmp_path, monkeypatch):
    profile = tmp_path / "profile"
    downloads = profile / "Downloads"
    session_downloads = downloads / "SecureSessionManager" / "PC_LAB_01" / "sess_123"
    session_downloads.mkdir(parents=True)
    keep = downloads / "keep-this-file.txt"
    keep.write_text("administrator file", encoding="utf-8")
    client_download = session_downloads / "client-file.pdf"
    client_download.write_text("client download", encoding="utf-8")
    nested_download = session_downloads / "nested" / "another-file.txt"
    nested_download.parent.mkdir()
    nested_download.write_text("nested client download", encoding="utf-8")
    monkeypatch.setenv("USERPROFILE", str(profile))
    monkeypatch.setenv("LOCALAPPDATA", "")
    monkeypatch.setenv("APPDATA", "")
    monkeypatch.setenv("TEMP", "")
    monkeypatch.setenv("TMP", "")

    quarantine = QuarantineManager(str(tmp_path / "quarantine"))
    engine = CleanupEngine(quarantine_manager=quarantine)
    result = engine.perform_full_cleanup(str(session_downloads))

    assert result["quarantined_downloads"] == 2
    assert keep.read_text(encoding="utf-8") == "administrator file"
    assert not client_download.exists()
    assert not session_downloads.exists()
    assert {item["fileName"] for item in quarantine.list_items()} == {
        "client-file.pdf",
        "another-file.txt",
    }


def test_full_cleanup_refuses_download_folder_outside_managed_area(tmp_path, monkeypatch):
    profile = tmp_path / "profile"
    outside_folder = tmp_path / "outside"
    outside_folder.mkdir()
    (outside_folder / "keep.txt").write_text("keep", encoding="utf-8")
    monkeypatch.setenv("USERPROFILE", str(profile))
    monkeypatch.setenv("LOCALAPPDATA", "")
    monkeypatch.setenv("APPDATA", "")
    monkeypatch.setenv("TEMP", "")
    monkeypatch.setenv("TMP", "")

    engine = CleanupEngine(quarantine_manager=QuarantineManager(str(tmp_path / "quarantine")))

    with pytest.raises(ValueError, match="outside the managed session Downloads area"):
        engine.perform_full_cleanup(str(outside_folder))
    assert (outside_folder / "keep.txt").read_text(encoding="utf-8") == "keep"
