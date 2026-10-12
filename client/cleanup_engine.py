"""Quarantines removable user artifacts and clears the Windows clipboard."""

import ctypes
import glob
import logging
import os
from typing import Any, Dict, List, Optional

from client.quarantine_manager import QuarantineManager

logger = logging.getLogger(__name__)


class CleanupEngine:
    """Moves removable user artifacts to admin-managed quarantine."""

    def __init__(self, quarantine_manager: Optional[QuarantineManager] = None):
        self.quarantine = quarantine_manager or QuarantineManager()

    def cleanup_temp_files(self) -> int:
        """
        Moves files from Windows %TEMP% and user temp directories into quarantine.
        Returns the number of files moved.
        """
        cleaned_count = 0
        temp_dirs = [
            os.environ.get("TEMP", ""),
            os.environ.get("TMP", ""),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Temp"),
        ]

        for temp_dir in filter(None, temp_dirs):
            if not os.path.isdir(temp_dir):
                continue
            for root, dirs, files in os.walk(temp_dir, topdown=False):
                for f in files:
                    fp = os.path.join(root, f)
                    try:
                        self.quarantine.quarantine_path(
                            fp, "temporary", os.path.relpath(fp, temp_dir)
                        )
                        cleaned_count += 1
                    except Exception as e:
                        logger.warning("Could not quarantine temporary file %s: %s", fp, e)
                for d in dirs:
                    dp = os.path.join(root, d)
                    try:
                        os.rmdir(dp)
                    except OSError:
                        logger.debug("Temporary directory is not empty or could not be removed: %s", dp)
        logger.info("Moved %d temporary files into quarantine.", cleaned_count)
        return cleaned_count

    def cleanup_recent_documents(self) -> int:
        """
        Quarantines Windows recent document shortcuts and jump lists.
        """
        cleaned_count = 0
        appdata = os.environ.get("APPDATA", "")
        if not appdata:
            return 0

        recent_paths = [
            os.path.join(appdata, "Microsoft", "Windows", "Recent"),
            os.path.join(appdata, "Microsoft", "Windows", "Recent", "AutomaticDestinations"),
            os.path.join(appdata, "Microsoft", "Windows", "Recent", "CustomDestinations"),
        ]

        for p in recent_paths:
            if not os.path.isdir(p):
                continue
            for item in os.listdir(p):
                target = os.path.join(p, item)
                try:
                    if os.path.isfile(target) or os.path.islink(target):
                        self.quarantine.quarantine_path(target, "recent-items", item)
                        cleaned_count += 1
                except Exception as e:
                    logger.warning("Could not quarantine recent item %s: %s", target, e)

        logger.info("Moved %d recent-document entries into quarantine.", cleaned_count)
        return cleaned_count

    def cleanup_browser_data(self) -> None:
        """
        Quarantines configured caches, history, cookies, and session data for supported browsers.
        """
        local_app = os.environ.get("LOCALAPPDATA", "")
        app_data = os.environ.get("APPDATA", "")

        browser_targets: List[str] = []

        if local_app:
            # Google Chrome
            browser_targets.extend([
                os.path.join(local_app, "Google", "Chrome", "User Data", "Default", "Cache"),
                os.path.join(local_app, "Google", "Chrome", "User Data", "Default", "Cookies"),
                os.path.join(local_app, "Google", "Chrome", "User Data", "Default", "History"),
                os.path.join(local_app, "Google", "Chrome", "User Data", "Default", "Login Data"),
                os.path.join(local_app, "Google", "Chrome", "User Data", "Default", "Web Data"),
            ])
            # Microsoft Edge
            browser_targets.extend([
                os.path.join(local_app, "Microsoft", "Edge", "User Data", "Default", "Cache"),
                os.path.join(local_app, "Microsoft", "Edge", "User Data", "Default", "Cookies"),
                os.path.join(local_app, "Microsoft", "Edge", "User Data", "Default", "History"),
                os.path.join(local_app, "Microsoft", "Edge", "User Data", "Default", "Login Data"),
            ])

        if app_data:
            # Mozilla Firefox
            firefox_profiles = glob.glob(os.path.join(app_data, "Mozilla", "Firefox", "Profiles", "*"))
            for prof in firefox_profiles:
                browser_targets.extend([
                    os.path.join(prof, "places.sqlite"),
                    os.path.join(prof, "cookies.sqlite"),
                    os.path.join(prof, "formhistory.sqlite"),
                    os.path.join(prof, "logins.json"),
                ])

        quarantined = 0
        for target in browser_targets:
            if not os.path.exists(target):
                continue
            try:
                quarantined += self._quarantine_browser_target(target)
            except Exception as e:
                logger.warning("Could not quarantine browser path %s: %s", target, e)

        logger.info("Moved %d browser data targets into quarantine.", quarantined)

    def wipe_clipboard(self) -> bool:
        """
        Clears the Windows system clipboard to prevent credential leakage.
        """
        try:
            # Try via pywin32 if available
            import win32clipboard
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.CloseClipboard()
            logger.info("Windows clipboard successfully emptied.")
            return True
        except Exception:
            # Fallback using ctypes user32 directly
            try:
                user32 = ctypes.windll.user32
                if user32.OpenClipboard(0):
                    user32.EmptyClipboard()
                    user32.CloseClipboard()
                    logger.info("Windows clipboard emptied via ctypes user32.")
                    return True
            except Exception as e:
                logger.warning("Failed to wipe clipboard: %s", e)
        return False

    def sanitize_user_folder(self, folder_path: str) -> int:
        """
        Moves files within a user folder (e.g., Downloads) into quarantine.
        """
        expanded = os.path.expandvars(folder_path)
        if not os.path.isdir(expanded):
            return 0

        quarantined_count = 0
        for root, _, files in os.walk(expanded):
            for file in files:
                fp = os.path.join(root, file)
                try:
                    self.quarantine.quarantine_path(
                        fp, "downloads", os.path.relpath(fp, expanded)
                    )
                    quarantined_count += 1
                except OSError as e:
                    logger.warning("Could not quarantine user file %s: %s", fp, e)
        return quarantined_count

    def _quarantine_browser_target(self, target: str) -> int:
        if not os.path.isdir(target) or os.path.islink(target):
            self.quarantine.quarantine_path(target, "browser-data")
            return 1

        moved = 0
        for root, directories, files in os.walk(target, topdown=False):
            for filename in files:
                path = os.path.join(root, filename)
                try:
                    relative = os.path.relpath(path, target)
                    self.quarantine.quarantine_path(path, "browser-data", relative)
                    moved += 1
                except Exception as e:
                    logger.warning("Could not quarantine browser file %s: %s", path, e)

            for directory in directories:
                path = os.path.join(root, directory)
                if os.path.islink(path):
                    try:
                        self.quarantine.quarantine_path(
                            path, "browser-data", os.path.relpath(path, target)
                        )
                        moved += 1
                    except Exception as e:
                        logger.warning("Could not quarantine browser link %s: %s", path, e)
                else:
                    try:
                        os.rmdir(path)
                    except OSError:
                        logger.debug("Browser directory is not empty after quarantine: %s", path)

            try:
                os.rmdir(root)
            except OSError:
                logger.debug("Browser directory could not be removed after quarantine: %s", root)

        if moved == 0 and os.path.isdir(target):
            self.quarantine.quarantine_path(target, "browser-data")
            moved = 1
        return moved

    def perform_full_cleanup(self, session_downloads_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Quarantines removable files and clears the clipboard.
        """
        managed_root = None
        if session_downloads_dir:
            downloads_root = os.path.abspath(os.path.join(
                os.environ.get("USERPROFILE", os.path.expanduser("~")), "Downloads"
            ))
            managed_root = os.path.realpath(os.path.join(downloads_root, "SecureSessionManager"))
            absolute_session_path = os.path.abspath(session_downloads_dir)
            session_downloads_dir = os.path.realpath(absolute_session_path)
            try:
                relative_parts = os.path.relpath(session_downloads_dir, managed_root).split(os.sep)
                is_managed_session_folder = (
                    os.path.commonpath([managed_root, session_downloads_dir]) == managed_root
                    and session_downloads_dir != managed_root
                    and len(relative_parts) == 2
                    and os.path.normcase(absolute_session_path) == os.path.normcase(session_downloads_dir)
                )
            except ValueError:
                is_managed_session_folder = False
            if not is_managed_session_folder:
                raise ValueError("Refusing to clean a folder outside the managed session Downloads area.")

        logger.info("Commencing session cleanup and quarantine...")
        self.wipe_clipboard()
        self.cleanup_browser_data()
        temp_quarantined = self.cleanup_temp_files()
        recent_quarantined = self.cleanup_recent_documents()

        quarantined_downloads = 0
        if session_downloads_dir:
            quarantined_downloads = self.sanitize_user_folder(session_downloads_dir)
            self._remove_empty_session_download_folders(session_downloads_dir, managed_root)

        result = {
            "status": "success",
            "temp_quarantined": temp_quarantined,
            "recent_quarantined": recent_quarantined,
            "quarantined_downloads": quarantined_downloads,
            "session_downloads_dir": session_downloads_dir,
            "quarantined_items": len(self.quarantine.list_items()),
            "clipboard_cleared": True,
        }
        logger.info("Full session cleanup completed: %s", result)
        return result

    @staticmethod
    def _remove_empty_session_download_folders(session_path: str, managed_root: str) -> None:
        for root, directories, _ in os.walk(session_path, topdown=False):
            for directory in directories:
                try:
                    os.rmdir(os.path.join(root, directory))
                except OSError:
                    logger.debug("Nested session download folder could not be removed: %s", directory)
            try:
                os.rmdir(root)
            except OSError:
                logger.debug("Session download folder could not be removed: %s", root)

        machine_path = os.path.dirname(session_path)
        for path in (machine_path, managed_root):
            try:
                os.rmdir(path)
            except OSError:
                break
