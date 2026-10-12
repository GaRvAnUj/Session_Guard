"""Reversible storage for files removed during workstation isolation."""

import json
import logging
import os
import shutil
import tempfile
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

logger = logging.getLogger(__name__)


class QuarantineManager:
    def __init__(self, root: Optional[str] = None):
        if root is None:
            local_app_data = os.environ.get("LOCALAPPDATA")
            if not local_app_data:
                local_app_data = tempfile.gettempdir()
            root = os.path.join(local_app_data, "SecureSessionManager", "Quarantine")
        self.root = os.path.abspath(root)
        self.manifest_path = os.path.join(self.root, "manifest.json")
        self._lock = threading.RLock()
        os.makedirs(self.root, exist_ok=True)
        self._items = self._load_manifest()

    def _load_manifest(self) -> Dict[str, Dict[str, Any]]:
        if not os.path.exists(self.manifest_path):
            return {}
        with open(self.manifest_path, "r", encoding="utf-8") as manifest_file:
            data = json.load(manifest_file)
        if not isinstance(data, dict):
            raise ValueError(f"Invalid quarantine manifest: {self.manifest_path}")
        return data

    def _save_manifest(self) -> None:
        temporary_path = f"{self.manifest_path}.{uuid.uuid4().hex}.tmp"
        try:
            with open(temporary_path, "w", encoding="utf-8") as manifest_file:
                json.dump(self._items, manifest_file, indent=2)
                manifest_file.flush()
                os.fsync(manifest_file.fileno())
            os.replace(temporary_path, self.manifest_path)
        finally:
            if os.path.exists(temporary_path):
                os.remove(temporary_path)

    def quarantine_path(
        self, source_path: str, category: str, relative_path: Optional[str] = None
    ) -> Dict[str, Any]:
        source = os.path.abspath(source_path)
        if not os.path.lexists(source):
            raise FileNotFoundError(source)
        if self._is_within(self.root, source):
            raise ValueError("A quarantine item cannot be quarantined again.")

        item_id = uuid.uuid4().hex
        item_dir = os.path.join(self.root, item_id)
        os.makedirs(item_dir)
        destination = os.path.join(item_dir, os.path.basename(os.path.normpath(source)) or "item")
        size_bytes = self._measure_size(source)
        record = {
            "itemId": item_id,
            "fileName": os.path.basename(os.path.normpath(source)) or source,
            "originalPath": source,
            "quarantinedPath": destination,
            "category": category,
            "relativePath": relative_path or os.path.basename(os.path.normpath(source)),
            "sizeBytes": size_bytes,
            "quarantinedAt": datetime.now(timezone.utc).isoformat(),
        }

        try:
            shutil.move(source, destination)
            with self._lock:
                self._items[item_id] = record
                self._save_manifest()
        except Exception:
            if os.path.lexists(destination) and not os.path.lexists(source):
                os.makedirs(os.path.dirname(source), exist_ok=True)
                shutil.move(destination, source)
            if os.path.isdir(item_dir) and not os.listdir(item_dir):
                os.rmdir(item_dir)
            raise

        logger.info("Quarantined %s item %s as %s", category, source, item_id)
        return self._public_record(record)

    def list_items(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [self._public_record(item) for item in self._items.values()]

    def restore(self, item_ids: Iterable[str]) -> List[str]:
        return self._apply(item_ids, restore=True)

    def permanently_delete(self, item_ids: Iterable[str]) -> List[str]:
        return self._apply(item_ids, restore=False)

    def _apply(self, item_ids: Iterable[str], restore: bool) -> List[str]:
        completed: List[str] = []
        with self._lock:
            for item_id in item_ids:
                item = self._items.get(item_id)
                if item is None:
                    logger.warning("Requested quarantine item %s is not in the local manifest.", item_id)
                    continue
                stored_path = os.path.abspath(item["quarantinedPath"])
                if not self._is_within(self.root, stored_path):
                    raise ValueError(f"Quarantine item {item_id} points outside the quarantine store.")

                try:
                    if restore:
                        destination = os.path.abspath(item["originalPath"])
                        if self._is_within(self.root, destination):
                            raise ValueError("A restore target cannot be inside the quarantine store.")
                        if os.path.lexists(destination):
                            raise FileExistsError(f"Restore target already exists: {destination}")
                        os.makedirs(os.path.dirname(destination), exist_ok=True)
                        shutil.move(stored_path, destination)
                        self._items.pop(item_id)
                        try:
                            self._save_manifest()
                        except Exception:
                            self._items[item_id] = item
                            os.makedirs(os.path.dirname(stored_path), exist_ok=True)
                            shutil.move(destination, stored_path)
                            raise
                    else:
                        self._items.pop(item_id)
                        try:
                            self._save_manifest()
                        except Exception:
                            self._items[item_id] = item
                            raise
                        try:
                            if os.path.isdir(stored_path) and not os.path.islink(stored_path):
                                shutil.rmtree(stored_path)
                            elif os.path.lexists(stored_path):
                                os.remove(stored_path)
                        except OSError:
                            self._items[item_id] = item
                            self._save_manifest()
                            raise

                    item_dir = os.path.dirname(stored_path)
                    if os.path.isdir(item_dir) and not os.listdir(item_dir):
                        os.rmdir(item_dir)
                    completed.append(item_id)
                except (OSError, ValueError) as e:
                    logger.error("Could not %s quarantined item %s: %s",
                                 "restore" if restore else "permanently delete", item_id, e)
        return completed

    @staticmethod
    def _measure_size(path: str) -> int:
        if os.path.isfile(path):
            return os.path.getsize(path)
        total = 0
        for root, _, files in os.walk(path):
            for name in files:
                try:
                    total += os.path.getsize(os.path.join(root, name))
                except OSError:
                    logger.warning("Could not measure quarantine item file %s", os.path.join(root, name))
        return total

    @staticmethod
    def _is_within(root: str, path: str) -> bool:
        try:
            return os.path.commonpath([root, path]) == root
        except ValueError:
            return False

    @staticmethod
    def _public_record(item: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "itemId": item["itemId"],
            "fileName": item["fileName"],
            "relativePath": item.get("relativePath", item["fileName"]),
            "category": item["category"],
            "sizeBytes": item["sizeBytes"],
            "quarantinedAt": item["quarantinedAt"],
        }
