from __future__ import annotations

import json
import time

from src.common.shard import presence as mod


def test_presence_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "plugin_data_dir", lambda name, create=True: tmp_path / name)
    monkeypatch.setattr(mod, "is_sharding_active", lambda: True)

    mod.note_worker_bot_connected_sync(qq=111, connection_key="111", adapter="OneBot V11", shard_id=0)
    mod.note_worker_bot_connected_sync(qq=222, connection_key="222", adapter="OneBot V11", shard_id=1)

    online = mod.get_cluster_online_bot_ids()
    assert 111 in online and 222 in online

    rows = mod.list_connected_bots_for_webui()
    assert len(rows) == 2
    assert {r["self_id"] for r in rows} == {"111", "222"}

    mod.note_worker_bot_disconnected_sync(qq=111)
    assert 111 not in mod.get_cluster_online_bot_ids()


def test_presence_stale_pruned(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "plugin_data_dir", lambda name, create=True: tmp_path / name)
    monkeypatch.setattr(mod, "is_sharding_active", lambda: True)

    mod.note_worker_bot_connected_sync(qq=333, connection_key="333", adapter="OneBot V11", shard_id=0)
    path = mod._presence_path()
    data = json.loads(path.read_text(encoding="utf-8"))
    data["bots"]["333"]["last_seen_at"] = time.time() - 9999
    path.write_text(json.dumps(data), encoding="utf-8")

    assert 333 not in mod.get_cluster_online_bot_ids()
