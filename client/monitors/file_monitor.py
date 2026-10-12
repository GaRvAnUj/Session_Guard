"""
File System Monitor for Windows Public Computers.
Uses watchdog to observe file operations (create, modify, delete) in user spaces
(Downloads, Desktop, Documents) and dispatches privacy-preserving metadata events.
"""

import logging
import os
import threading
from typing import List, Optional

from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers import Observer

logger = logging.getLogger(__name__)


class _SessionFileEventHandler(FileSystemEventHandler):
    """Internal watchdog event handler."""

    def __init__(self, recorder):
        super().__init__()
        self.recorder = recorder

    def _dispatch_file_event(self, operation: str, src_path: str):
        if not src_path or os.path.isdir(src_path):
            return

        # Ignore temporary hidden lockfiles often created by Office or Windows
        basename = os.path.basename(src_path)
        if basename.startswith("~$") or basename.startswith("."):
            return

        size_bytes = 0
        if operation != "delete":
            try:
                if os.path.exists(src_path):
                    size_bytes = os.path.getsize(src_path)
            except (OSError, PermissionError):
                size_bytes = 0

        ext = os.path.splitext(src_path)[1].lower()

        # Submit to recorder (recorder privacy filter will hash path and extract only extension & size)
        self.recorder.record_event("file_operation", {
            "operation": operation,
            "path": src_path,
            "extension": ext if ext else "none",
            "size_bytes": size_bytes,
        })

    def on_created(self, event: FileSystemEvent):
        self._dispatch_file_event("create", event.src_path)

    def on_modified(self, event: FileSystemEvent):
        self._dispatch_file_event("write", event.src_path)

    def on_deleted(self, event: FileSystemEvent):
        self._dispatch_file_event("delete", event.src_path)


class FileSystemMonitor:
    """
    Manages filesystem watchers over user directories.
    """

    def __init__(
        self,
        recorder,
        watch_paths: Optional[List[str]] = None,
        session_downloads_dir: Optional[str] = None,
    ):
        self.recorder = recorder
        self.watch_paths = watch_paths or self._default_paths(session_downloads_dir)
        self._observer: Optional[Observer] = None
        self._running = False

    def _default_paths(self, session_downloads_dir: Optional[str] = None) -> List[str]:
        user_profile = os.environ.get("USERPROFILE", os.path.expanduser("~"))
        candidates = [
            session_downloads_dir or os.path.join(user_profile, "Downloads"),
            os.path.join(user_profile, "Desktop"),
            os.path.join(user_profile, "Documents"),
        ]
        return [p for p in candidates if os.path.isdir(p)]

    def start(self) -> None:
        """Starts watchdog observers across configured paths."""
        if self._running:
            return

        resolved_paths = []
        for path in self.watch_paths:
            expanded = os.path.expandvars(path)
            if os.path.isdir(expanded):
                resolved_paths.append(expanded)

        if not resolved_paths:
            logger.warning("No valid watch paths found for FileSystemMonitor.")
            return

        event_handler = _SessionFileEventHandler(self.recorder)
        self._observer = Observer()
        for p in resolved_paths:
            logger.info("FileSystemMonitor watching path: %s", p)
            self._observer.schedule(event_handler, path=p, recursive=True)

        self._observer.start()
        self._running = True

    def stop(self) -> None:
        """Stops watchdog observer."""
        if not self._running or not self._observer:
            return
        self._running = False
        try:
            self._observer.stop()
            self._observer.join(timeout=3.0)
        except Exception as e:
            logger.error("Error stopping file system observer: %s", e)
