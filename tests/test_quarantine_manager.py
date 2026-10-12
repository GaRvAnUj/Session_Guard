from client.quarantine_manager import QuarantineManager


def test_quarantine_and_restore_preserves_file_contents(tmp_path):
    downloads = tmp_path / "Downloads"
    downloads.mkdir()
    source = downloads / "report.txt"
    source.write_text("keep this file", encoding="utf-8")
    manager = QuarantineManager(str(tmp_path / "quarantine"))

    item = manager.quarantine_path(str(source), "downloads")

    assert not source.exists()
    assert item["fileName"] == "report.txt"
    assert "originalPath" not in item
    assert manager.list_items() == [item]

    assert manager.restore([item["itemId"]]) == [item["itemId"]]
    assert source.read_text(encoding="utf-8") == "keep this file"
    assert manager.list_items() == []


def test_permanent_delete_requires_selected_quarantine_item(tmp_path):
    source = tmp_path / "sensitive.txt"
    source.write_text("delete only with admin command", encoding="utf-8")
    manager = QuarantineManager(str(tmp_path / "quarantine"))
    item = manager.quarantine_path(str(source), "downloads")

    assert manager.permanently_delete([item["itemId"]]) == [item["itemId"]]
    assert not source.exists()
    assert manager.list_items() == []


def test_restore_does_not_overwrite_existing_file(tmp_path):
    source = tmp_path / "report.txt"
    source.write_text("quarantined version", encoding="utf-8")
    manager = QuarantineManager(str(tmp_path / "quarantine"))
    item = manager.quarantine_path(str(source), "downloads")
    source.write_text("new file", encoding="utf-8")

    assert manager.restore([item["itemId"]]) == []

    assert source.read_text(encoding="utf-8") == "new file"
    assert len(manager.list_items()) == 1


def test_manifest_survives_manager_restart(tmp_path):
    source = tmp_path / "kept.txt"
    source.write_text("persistent quarantine", encoding="utf-8")
    quarantine_root = tmp_path / "quarantine"
    first_manager = QuarantineManager(str(quarantine_root))
    item = first_manager.quarantine_path(str(source), "downloads")

    restarted_manager = QuarantineManager(str(quarantine_root))

    assert restarted_manager.list_items() == [item]
    assert restarted_manager.restore([item["itemId"]]) == [item["itemId"]]
    assert source.read_text(encoding="utf-8") == "persistent quarantine"
