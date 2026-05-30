from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_command_cross_bot_claim_allows_only_one_bot(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.platform.multi_bot import dedup as dedup_mod
    from src.plugins.help import event_preprocessor

    dedup_mod._cross_bot_claim_owners.clear()
    monkeypatch.setattr(event_preprocessor, "is_plugin_command_plaintext", lambda text: text == "牛牛帮助")

    first = await event_preprocessor.command_cross_bot_claim_won(
        bot_id=111,
        group_id=12345,
        user_id=999,
        plain_text="牛牛帮助",
        message_time=100,
    )
    second = await event_preprocessor.command_cross_bot_claim_won(
        bot_id=222,
        group_id=12345,
        user_id=999,
        plain_text="牛牛帮助",
        message_time=100,
    )
    again = await event_preprocessor.command_cross_bot_claim_won(
        bot_id=111,
        group_id=12345,
        user_id=999,
        plain_text="牛牛帮助",
        message_time=100,
    )

    assert first is True
    assert second is False
    assert again is True


@pytest.mark.asyncio
async def test_command_cross_bot_claim_skips_non_commands(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.platform.multi_bot import dedup as dedup_mod
    from src.plugins.help import event_preprocessor

    dedup_mod._cross_bot_claim_owners.clear()
    monkeypatch.setattr(event_preprocessor, "is_plugin_command_plaintext", lambda _text: False)

    first = await event_preprocessor.command_cross_bot_claim_won(
        bot_id=111,
        group_id=12345,
        user_id=999,
        plain_text="普通聊天",
        message_time=100,
    )
    second = await event_preprocessor.command_cross_bot_claim_won(
        bot_id=222,
        group_id=12345,
        user_id=999,
        plain_text="普通聊天",
        message_time=100,
    )

    assert first is True
    assert second is True
