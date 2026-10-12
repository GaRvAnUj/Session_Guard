import json
import os

from client.session_downloads import SessionDownloads


def test_session_downloads_configure_and_restore_chromium_profiles(tmp_path):
    downloads_root = tmp_path / "Downloads"
    local_app_data = tmp_path / "LocalAppData"
    chrome_preferences = (
        local_app_data / "Google" / "Chrome" / "User Data" / "Default" / "Preferences"
    )
    edge_preferences = (
        local_app_data / "Microsoft" / "Edge" / "User Data" / "Profile 1" / "Preferences"
    )
    chrome_preferences.parent.mkdir(parents=True)
    edge_preferences.parent.mkdir(parents=True)
    chrome_preferences.write_text(
        json.dumps({"download": {"default_directory": "C:/old-downloads", "directory_upgrade": False}}),
        encoding="utf-8",
    )
    edge_preferences.write_text(json.dumps({"profile": {"name": "Lab"}}), encoding="utf-8")

    manager = SessionDownloads(str(downloads_root), str(local_app_data))
    session_directory = manager.start_session("PC/01", "session:abc")

    expected_directory = os.path.join(str(downloads_root), "SecureSessionManager", "PC_01", "session_abc")
    assert session_directory == expected_directory
    assert os.path.isdir(session_directory)
    assert json.loads(chrome_preferences.read_text(encoding="utf-8"))["download"] == {
        "default_directory": session_directory,
        "directory_upgrade": True,
    }
    edge = json.loads(edge_preferences.read_text(encoding="utf-8"))
    assert edge["download"]["default_directory"] == session_directory
    assert edge["profile"]["name"] == "Lab"

    manager.restore_browser_download_directories()

    assert json.loads(chrome_preferences.read_text(encoding="utf-8"))["download"] == {
        "default_directory": "C:/old-downloads",
        "directory_upgrade": False,
    }
    assert json.loads(edge_preferences.read_text(encoding="utf-8")) == {"profile": {"name": "Lab"}}


def test_session_download_folder_identifiers_cannot_escape_downloads(tmp_path):
    downloads_root = tmp_path / "Downloads"
    manager = SessionDownloads(str(downloads_root), str(tmp_path / "LocalAppData"))

    session_directory = manager.start_session("..\\..\\outside", "..\\session")

    assert os.path.commonpath([str(downloads_root), session_directory]) == str(downloads_root)
    assert os.path.isdir(session_directory)
