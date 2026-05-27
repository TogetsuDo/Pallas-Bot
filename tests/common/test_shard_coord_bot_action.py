from __future__ import annotations

import asyncio
import json
import time

from src.platform.shard.coord import bot_action as mod


def test_bot_action_request_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "_coord_dir", lambda: tmp_path)

    request_id = mod._publish_request(
        action="set_group_card",
        bot_qq=300,
        payload={"group_id": 1, "user_id": 2, "card": "test"},
        timeout_sec=5.0,
    )
    path = mod._request_path(request_id)
    mod._finish_request(path, ok=True, result=None)

    async def run() -> None:
        ok, result = await mod._wait_request(request_id, deadline=time.time() + 2.0)
        assert ok is True
        assert result is None

    asyncio.run(run())


def test_prune_stale_bot_action_removes_overdue_open(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "_coord_dir", lambda: tmp_path)
    now = time.time()
    path = tmp_path / "overdue.json"
    path.write_text(
        json.dumps({
            "request_id": "overdue",
            "action": "send_group_msg",
            "bot_qq": 1,
            "done": False,
            "deadline": now - 30,
            "created_at": now - 40,
        }),
        encoding="utf-8",
    )
    done_path = tmp_path / "old_done.json"
    done_path.write_text(
        json.dumps({
            "request_id": "old",
            "done": True,
            "created_at": now - mod._DONE_RETAIN_SEC - 10,
        }),
        encoding="utf-8",
    )

    async def run() -> None:
        stats = await mod.prune_stale_bot_action_files()
        assert stats["removed_overdue_open"] == 1
        assert stats["removed_done"] == 1
        assert not path.is_file()
        assert not done_path.is_file()

    asyncio.run(run())
