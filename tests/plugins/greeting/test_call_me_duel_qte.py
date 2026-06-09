from __future__ import annotations

import asyncio
import time
from types import SimpleNamespace

from src.plugins.duel import duel_qte as qte_mod


def test_duel_qte_active_in_group_race() -> None:
    gid = 4242
    loop = asyncio.new_event_loop()
    fut: asyncio.Future[str | None] = loop.create_future()
    qte_mod._race_sessions.clear()
    qte_mod._sessions.clear()
    gid_s = str(gid)
    qte_mod._race_sessions[gid_s] = qte_mod._DuelRaceQteSession(
        future=fut,
        required_key="帕拉斯",
        deadline=time.time() + 10.0,
        challenger_id="100",
        defender_id="200",
    )
    qte_mod.sync_active_qte_group(gid_s)
    try:
        assert qte_mod.duel_qte_active_in_group(gid) is True
        fut.set_result("100")
        qte_mod.sync_active_qte_group(gid_s)
        assert qte_mod.duel_qte_active_in_group(gid) is False
    finally:
        qte_mod._race_sessions.clear()
        qte_mod._active_qte_groups.clear()
        qte_mod._active_qte_users_by_group.clear()
        loop.close()


def test_duel_qte_active_in_group_single() -> None:
    gid = 5252
    uid = "9001"
    loop = asyncio.new_event_loop()
    fut: asyncio.Future[bool] = loop.create_future()
    qte_mod._race_sessions.clear()
    qte_mod._sessions.clear()
    gid_s = str(gid)
    qte_mod._sessions[(gid_s, uid)] = qte_mod._DuelQteSession(
        future=fut,
        required_key="牛牛",
        deadline=time.time() + 10.0,
    )
    qte_mod.sync_active_qte_group(gid_s)
    try:
        assert qte_mod.duel_qte_active_in_group(gid) is True
        assert qte_mod.duel_qte_active_in_group(gid + 1) is False
    finally:
        qte_mod._sessions.clear()
        qte_mod._active_qte_groups.clear()
        qte_mod._active_qte_users_by_group.clear()
        loop.close()


def test_complete_duel_qte_clears_active_group_immediately() -> None:
    gid = 6262
    uid = "9002"
    loop = asyncio.new_event_loop()
    fut: asyncio.Future[bool] = loop.create_future()
    qte_mod._race_sessions.clear()
    qte_mod._sessions.clear()
    gid_s = str(gid)
    qte_mod._sessions[(gid_s, uid)] = qte_mod._DuelQteSession(
        future=fut,
        required_key="帕拉斯",
        deadline=time.time() + 10.0,
    )
    qte_mod.sync_active_qte_group(gid_s)
    try:
        assert qte_mod.duel_qte_active_in_group(gid) is True
        event = SimpleNamespace(
            group_id=gid,
            get_user_id=lambda: uid,
            get_plaintext=lambda: "帕拉斯",
        )
        qte_mod.complete_duel_qte(event)
        assert qte_mod.duel_qte_active_in_group(gid) is False
    finally:
        qte_mod._sessions.clear()
        qte_mod._active_qte_groups.clear()
        qte_mod._active_qte_users_by_group.clear()
        loop.close()


def test_duel_qte_active_in_group_prunes_expired_session() -> None:
    gid = 7272
    uid = "9003"
    loop = asyncio.new_event_loop()
    fut: asyncio.Future[bool] = loop.create_future()
    qte_mod._race_sessions.clear()
    qte_mod._sessions.clear()
    gid_s = str(gid)
    qte_mod._sessions[(gid_s, uid)] = qte_mod._DuelQteSession(
        future=fut,
        required_key="牛牛",
        deadline=time.time() - 1.0,
    )
    qte_mod._active_qte_groups.add(gid_s)
    try:
        assert qte_mod.duel_qte_active_in_group(gid) is False
    finally:
        qte_mod._sessions.clear()
        qte_mod._active_qte_groups.clear()
        qte_mod._active_qte_users_by_group.clear()
        loop.close()


def test_call_me_rule_skips_when_duel_qte_active(monkeypatch) -> None:
    import src.plugins.greeting as greeting_mod

    monkeypatch.setattr(
        greeting_mod,
        "duel_qte_blocks_greeting_user",
        lambda group_id, user_id: group_id == 777 and str(user_id) == "100",
    )
    event = SimpleNamespace(raw_message="帕拉斯", group_id=777, user_id=100)
    assert greeting_mod.call_me_message_rule(event) is False

    event_other = SimpleNamespace(raw_message="帕拉斯", group_id=888, user_id=100)
    assert greeting_mod.call_me_message_rule(event_other) is True

    event_niu = SimpleNamespace(raw_message="牛牛", group_id=777, user_id=100)
    assert greeting_mod.call_me_message_rule(event_niu) is False

    spectator = SimpleNamespace(raw_message="帕拉斯", group_id=777, user_id=200)
    assert greeting_mod.call_me_message_rule(spectator) is True
