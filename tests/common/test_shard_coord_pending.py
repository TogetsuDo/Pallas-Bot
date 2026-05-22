from __future__ import annotations

import json

from src.common.shard.coord_pending import coord_pending_snapshot_sync


def test_coord_pending_counts(tmp_path, monkeypatch):
    coord = tmp_path / "coord"
    bot_action = coord / "bot_action"
    bot_action.mkdir(parents=True)
    (bot_action / "a.json").write_text(json.dumps({"done": False}), encoding="utf-8")
    (bot_action / "b.json").write_text(json.dumps({"done": True}), encoding="utf-8")
    (coord / "duel_qte").mkdir()
    (coord / "duel_qte" / "q.json").write_text("{}", encoding="utf-8")

    monkeypatch.setattr(
        "src.common.shard.coord_pending._coord_root",
        lambda: coord,
    )
    snap = coord_pending_snapshot_sync()
    assert snap["total_json"] == 3
    assert snap["by_dir"]["bot_action"] == 2
    assert snap["bot_action_open"] == 1
