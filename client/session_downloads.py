"""Create session-scoped Downloads folders and configure Chromium download paths."""

import copy
import json
import logging
import os
import re
import tempfile
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class SessionDownloads:
    """Routes Chrome and Edge downloads into a dedicated folder for one session."""

    _DOWNLOAD_KEYS = ("default_directory", "directory_upgrade")

    def __init__(
        self,
        downloads_root: Optional[str] = None,
        local_app_data: Optional[str] = None,
    ):
        user_profile = os.environ.get("USERPROFILE", os.path.expanduser("~"))
        self.downloads_root = os.path.abspath(
            downloads_root or os.path.join(user_profile, "Downloads")
        )
        self.local_app_data = local_app_data or os.environ.get("LOCALAPPDATA", "")
        self._original_download_settings: Dict[str, Dict[str, object]] = {}

    def start_session(self, machine_id: str, session_id: str) -> str:
        machine_folder = self._safe_component(machine_id)
        session_folder = self._safe_component(session_id)
        parent = os.path.join(self.downloads_root, "SecureSessionManager")
        session_path = os.path.abspath(os.path.join(parent, machine_folder, session_folder))
        self._ensure_within_downloads(session_path)
        os.makedirs(session_path, exist_ok=True)

        self._original_download_settings.clear()
        try:
            preferences_paths = self._browser_preferences_paths()
            if not preferences_paths:
                logger.warning(
                    "No Chrome or Edge profiles were found; downloads may not use the session folder %s",
                    session_path,
                )
            for preferences_path in preferences_paths:
                self._set_download_directory(preferences_path, session_path)
        except Exception:
            logger.exception("Could not configure browser download directory for session %s", session_id)
            raise
        return session_path

    def restore_browser_download_directories(self) -> None:
        for preferences_path, original_values in self._original_download_settings.items():
            try:
                preferences = self._read_preferences(preferences_path)
                download_settings = preferences.get("download", {})
                if not isinstance(download_settings, dict):
                    raise ValueError(f"Invalid download preferences in {preferences_path}")

                for key, original in original_values.items():
                    if original["exists"]:
                        download_settings[key] = copy.deepcopy(original["value"])
                    else:
                        download_settings.pop(key, None)

                if download_settings:
                    preferences["download"] = download_settings
                else:
                    preferences.pop("download", None)
                self._write_preferences(preferences_path, preferences)
            except Exception:
                logger.exception("Could not restore browser download preferences at %s", preferences_path)
        self._original_download_settings.clear()

    def _browser_preferences_paths(self):
        if not self.local_app_data:
            return []

        paths = []
        for vendor_path in (
            os.path.join("Google", "Chrome", "User Data"),
            os.path.join("Microsoft", "Edge", "User Data"),
        ):
            user_data = os.path.join(self.local_app_data, vendor_path)
            if not os.path.isdir(user_data):
                continue

            profiles = [
                entry.path
                for entry in os.scandir(user_data)
                if entry.is_dir()
                and (
                    os.path.isfile(os.path.join(entry.path, "Preferences"))
                    or entry.name == "Default"
                )
            ]
            if not profiles:
                profiles = [os.path.join(user_data, "Default")]
                os.makedirs(profiles[0], exist_ok=True)
            paths.extend(os.path.join(profile, "Preferences") for profile in profiles)
        return paths

    def _set_download_directory(self, preferences_path: str, session_path: str) -> None:
        preferences = self._read_preferences(preferences_path)
        download_settings = preferences.get("download", {})
        if not isinstance(download_settings, dict):
            raise ValueError(f"Invalid download preferences in {preferences_path}")

        self._original_download_settings[preferences_path] = {
            key: {
                "exists": key in download_settings,
                "value": copy.deepcopy(download_settings.get(key)),
            }
            for key in self._DOWNLOAD_KEYS
        }
        download_settings["default_directory"] = session_path
        download_settings["directory_upgrade"] = True
        preferences["download"] = download_settings
        self._write_preferences(preferences_path, preferences)
        logger.info("Set browser download directory to %s", session_path)

    @staticmethod
    def _read_preferences(preferences_path: str) -> dict:
        if not os.path.exists(preferences_path):
            return {}
        with open(preferences_path, "r", encoding="utf-8") as preferences_file:
            preferences = json.load(preferences_file)
        if not isinstance(preferences, dict):
            raise ValueError(f"Invalid browser preferences in {preferences_path}")
        return preferences

    @staticmethod
    def _write_preferences(preferences_path: str, preferences: dict) -> None:
        os.makedirs(os.path.dirname(preferences_path), exist_ok=True)
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=os.path.dirname(preferences_path),
                delete=False,
            ) as preferences_file:
                temporary_path = preferences_file.name
                json.dump(preferences, preferences_file, indent=2)
                preferences_file.flush()
                os.fsync(preferences_file.fileno())
            os.replace(temporary_path, preferences_path)
        finally:
            if temporary_path and os.path.exists(temporary_path):
                os.remove(temporary_path)

    def _ensure_within_downloads(self, session_path: str) -> None:
        real_root = os.path.realpath(self.downloads_root)
        real_session_path = os.path.realpath(session_path)
        try:
            if os.path.commonpath([real_root, real_session_path]) != real_root:
                raise ValueError("Session Downloads folder must stay inside the user's Downloads folder.")
        except ValueError as error:
            raise ValueError("Session Downloads folder must stay inside the user's Downloads folder.") from error

    @staticmethod
    def _safe_component(value: str) -> str:
        component = re.sub(r"[^A-Za-z0-9_-]", "_", value).strip("_")
        return component[:80] or "session"
