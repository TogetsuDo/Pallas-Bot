from __future__ import annotations

import json

import pytest
from packages.who_is_spy import store


def test_merge_word_pairs_deduplicates() -> None:
    merged = store.merge_word_pairs(
        [("可乐", "雪碧"), ("饺子", "馄饨")],
        [("可乐", "雪碧"), ("拿铁", "美式")],
    )
    assert merged == [("可乐", "雪碧"), ("饺子", "馄饨"), ("拿铁", "美式")]


def test_sync_word_file_merges_resource(tmp_path, monkeypatch) -> None:
    resource = tmp_path / "resource.json"
    data = tmp_path / "data.json"
    resource.write_text(json.dumps([["可乐", "雪碧"], ["拿铁", "美式"]]), encoding="utf-8")
    data.write_text(json.dumps([["可乐", "雪碧"]]), encoding="utf-8")

    monkeypatch.setattr(store, "DEFAULT_WORD_FILE", resource)
    monkeypatch.setattr(store, "WORD_FILE", data)
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)

    count = store.sync_word_file()
    assert count == 2
    saved = json.loads(data.read_text(encoding="utf-8"))
    assert saved == [["可乐", "雪碧"], ["拿铁", "美式"]]


@pytest.fixture
def spy_storage_dir(tmp_path, monkeypatch):
    root = tmp_path / "who_is_spy"
    root.mkdir()
    monkeypatch.setattr(store, "DATA_DIR", root)
    monkeypatch.setattr(store, "RECENT_WORDS_FILE", root / "recent_word_pairs.json")
    monkeypatch.setattr(
        "pallas.core.storage.deploy_store.plugin_data_dir",
        lambda name, create=True: root if name == "who_is_spy" else tmp_path / name,
    )
    return root


def test_recent_word_pairs_roundtrip(spy_storage_dir) -> None:
    store.record_recent_word_pair(123, "可乐", "雪碧", keep=2)
    store.record_recent_word_pair(123, "饺子", "馄饨", keep=2)
    store.record_recent_word_pair(123, "拿铁", "美式", keep=2)

    recent = store.load_recent_word_keys(123, limit=2)
    assert recent == {store.word_pair_key("饺子", "馄饨"), store.word_pair_key("拿铁", "美式")}
    assert (spy_storage_dir / "plugin_storage.json").is_file()


def test_recent_word_pairs_migrates_legacy_json(spy_storage_dir) -> None:
    legacy = spy_storage_dir / "recent_word_pairs.json"
    legacy.write_text(
        json.dumps({"123": [["可乐", "雪碧"], ["饺子", "馄饨"]]}),
        encoding="utf-8",
    )

    recent = store.load_recent_word_keys(123, limit=5)
    assert recent == {store.word_pair_key("可乐", "雪碧"), store.word_pair_key("饺子", "馄饨")}
    assert legacy.with_suffix(".json.migrated").is_file()
    assert not legacy.is_file()
