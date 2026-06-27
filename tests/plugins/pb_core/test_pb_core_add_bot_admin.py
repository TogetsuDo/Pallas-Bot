from types import SimpleNamespace

import pytest

from packages.pb_core.admins import (
    add_bot_admins,
    format_add_bot_admin_result,
    parse_add_bot_admin_targets,
)


def test_parse_add_bot_admin_single_admin_for_current_bot():
    parsed = parse_add_bot_admin_targets(
        "牛牛添加号主 2777777777",
        [],
        self_id=3888888888,
    )
    assert parsed == (3888888888, [2777777777])


def test_parse_add_bot_admin_explicit_bot_and_admins():
    parsed = parse_add_bot_admin_targets(
        "牛牛添加号主 3888888888 2777777777 2666666666",
        [],
        self_id=3999999999,
    )
    assert parsed == (3888888888, [2777777777, 2666666666])


def test_parse_add_bot_admin_current_bot_prefix():
    parsed = parse_add_bot_admin_targets(
        "牛牛添加号主 3888888888 2777777777",
        [],
        self_id=3888888888,
    )
    assert parsed == (3888888888, [2777777777])


def test_parse_add_bot_admin_supports_at_segment():
    msg = [SimpleNamespace(type="at", data={"qq": "2777777777"})]
    parsed = parse_add_bot_admin_targets("牛牛添加号主", msg, self_id=3888888888)
    assert parsed == (3888888888, [2777777777])


def test_parse_add_bot_admin_rejects_bot_only_without_admin():
    parsed = parse_add_bot_admin_targets(
        "牛牛添加号主 3888888888",
        [],
        self_id=3888888888,
    )
    assert parsed is None


def test_format_add_bot_admin_result_created_and_added():
    text = format_add_bot_admin_result(
        bot_id=3888888888,
        created=True,
        merged=[2777777777],
        added=[2777777777],
    )
    assert "初始化库配置" in text
    assert "2777777777" in text


@pytest.mark.asyncio
async def test_add_bot_admins_creates_row_and_merges(beanie_fixture, monkeypatch):
    monkeypatch.setattr("pallas.core.foundation.db.get_db_backend", lambda: "mongodb")
    from pallas.core.foundation.config import bot_admins_cache as cache

    await cache.reset_bot_admins_cache()
    created, merged, added = await add_bot_admins(88002, [111, 222])
    assert created is True
    assert added == [111, 222]
    assert merged == [111, 222]

    created2, merged2, added2 = await add_bot_admins(88002, [222, 333])
    assert created2 is False
    assert added2 == [333]
    assert merged2 == [111, 222, 333]

    await cache.reset_bot_admins_cache()
