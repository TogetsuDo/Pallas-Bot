from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from pallas_plugin_bot_status import bot_monitor as mod


@pytest.mark.asyncio
async def test_get_bot_status_info_prefers_protocol_offline_over_online_ids(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    qq = 1980955989
    mod.offline_bots.clear()
    mod.offline_bots[qq] = {
        "nickname": "测试牛",
        "offline_time": "2026-07-06 13:00:00",
        "source": "napcat_event",
    }

    monkeypatch.setattr(mod, "status_inventory_bot_ids", lambda **_: frozenset({qq}))
    monkeypatch.setattr(mod, "cluster_online_bot_ids", lambda _bots=None: {qq})
    monkeypatch.setattr(mod, "resolve_status_list_mode", lambda: "fleet")
    monkeypatch.setattr(mod, "get_bot_nickname", AsyncMock(return_value="测试牛"))

    online, offline = await mod.get_bot_status_info()

    assert qq not in online
    assert offline.get(qq) == "测试牛"


@pytest.mark.asyncio
async def test_get_bot_status_info_shows_online_when_not_protocol_marked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    qq = 1980955989
    mod.offline_bots.clear()

    monkeypatch.setattr(mod, "status_inventory_bot_ids", lambda **_: frozenset({qq}))
    monkeypatch.setattr(mod, "cluster_online_bot_ids", lambda _bots=None: {qq})
    monkeypatch.setattr(mod, "resolve_status_list_mode", lambda: "fleet")
    monkeypatch.setattr(mod, "get_bot_nickname", AsyncMock(return_value="测试牛"))

    online, offline = await mod.get_bot_status_info()

    assert online.get(qq) == "测试牛"
    assert qq not in offline
