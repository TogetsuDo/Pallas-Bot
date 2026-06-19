from __future__ import annotations

import pytest
from packages.who_is_spy import store
from packages.who_is_spy.logic import pick_words


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


def test_pick_words_skips_recent_when_possible(spy_storage_dir) -> None:
    store.WORD_BANK[:] = [("可乐", "雪碧"), ("饺子", "馄饨"), ("拿铁", "美式")]

    store.record_recent_word_pair(999, "可乐", "雪碧", keep=5)
    pair = pick_words(999, avoid_recent=5)
    assert pair != ("可乐", "雪碧")


def test_pick_words_fallback_when_all_recent(spy_storage_dir) -> None:
    store.WORD_BANK[:] = [("可乐", "雪碧"), ("饺子", "馄饨")]

    store.record_recent_word_pair(999, "可乐", "雪碧", keep=5)
    store.record_recent_word_pair(999, "饺子", "馄饨", keep=5)

    pair = pick_words(999, avoid_recent=5)
    assert pair in store.WORD_BANK
