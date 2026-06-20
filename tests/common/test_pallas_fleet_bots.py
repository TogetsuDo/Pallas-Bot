from __future__ import annotations

import json

from src.platform.multi_bot import fleet as mod


def test_load_enabled_account_qq(tmp_path, monkeypatch):
    proto = tmp_path / "pallas_protocol"
    proto.mkdir()
    acc = {
        "100": {"qq": "100", "enabled": False},
        "200": {"qq": "200", "enabled": True},
    }
    (proto / "accounts.json").write_text(json.dumps(acc), encoding="utf-8")

    monkeypatch.setattr(
        mod,
        "plugin_data_dir",
        lambda name: proto if name == "pallas_protocol" else tmp_path,
    )
    monkeypatch.setattr(mod, "is_sharding_active", lambda: False)
    mod.invalidate_fleet_bot_cache()
    ids = mod._load_fleet_bot_ids()
    assert 200 in ids
    assert 100 not in ids


def test_session_connected_merged_when_sharding(monkeypatch):
    monkeypatch.setattr(mod, "is_sharding_active", lambda: True)
    monkeypatch.setattr(mod, "_load_enabled_account_qq", lambda: set())
    mod._session_connected.clear()
    mod.invalidate_fleet_bot_cache()
    mod.note_fleet_bot_session_connected(424242)
    ids = mod._load_fleet_bot_ids()
    assert 424242 in ids
    mod._session_connected.clear()
    mod.invalidate_fleet_bot_cache()


def test_get_catalog_bot_ids_non_shard_uses_block(monkeypatch):
    class FakeCfg:
        bots = {111, 222}

    monkeypatch.setattr(mod, "is_sharding_active", lambda: False)

    import src.plugins.block as block_mod

    monkeypatch.setattr(block_mod, "plugin_config", FakeCfg())
    assert mod.get_catalog_bot_ids() == frozenset({111, 222})


def test_registry_ghost_excluded_without_account_or_session(tmp_path, monkeypatch):
    shard_dir = tmp_path / "pallas_shard"
    proto = tmp_path / "pallas_protocol"
    shard_dir.mkdir()
    proto.mkdir()
    (proto / "accounts.json").write_text(
        json.dumps({"200": {"qq": "200", "enabled": True}}),
        encoding="utf-8",
    )
    (shard_dir / "registry.json").write_text(
        json.dumps({
            "assignments": {"100": 0, "200": 0},
            "shards": [{"id": 0, "port": 7970, "bot_ids": ["100", "200"], "role": "normal"}],
        }),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        mod,
        "plugin_data_dir",
        lambda name, create=False: (
            proto if name == "pallas_protocol" else shard_dir if name == "pallas_shard" else tmp_path
        ),
    )
    monkeypatch.setattr(mod, "is_sharding_active", lambda: True)
    mod._session_connected.clear()
    mod.invalidate_fleet_bot_cache()

    ids = mod._load_fleet_bot_ids()
    assert 200 in ids
    assert 100 not in ids
    mod._session_connected.clear()
    mod.invalidate_fleet_bot_cache()
