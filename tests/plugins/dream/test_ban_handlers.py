from unittest.mock import AsyncMock, MagicMock

import pytest
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message


def _make_group_event(
    *,
    self_id: int = 2927116873,
    body: str = "[reply:id=101092384][at:qq=2927116873] 不可以",
    raw_message: str | None = None,
    to_me: bool = False,
) -> GroupMessageEvent:
    return GroupMessageEvent.model_construct(
        time=1,
        self_id=self_id,
        post_type="message",
        message_type="group",
        sub_type="normal",
        user_id=3023094357,
        group_id=733291779,
        message_id=793696852,
        message=Message(body),
        raw_message=raw_message or body,
        reply=None,
        to_me=to_me,
    )


@pytest.mark.asyncio
async def test_is_dream_ban_trigger_matches_raw_at_self_when_to_me_false():
    from src.plugins.dream.ban_handlers import is_dream_ban_trigger

    event = _make_group_event()

    assert await is_dream_ban_trigger(event) is True


@pytest.mark.asyncio
async def test_resolve_dream_ban_reply_raw_falls_back_to_get_msg_when_reply_missing():
    from src.plugins.dream.ban_handlers import resolve_dream_ban_reply_raw

    event = _make_group_event()

    bot = MagicMock()
    bot.get_msg = AsyncMock(return_value={"message": "梦库播报内容"})

    assert await resolve_dream_ban_reply_raw(bot, event) == "梦库播报内容"
    bot.get_msg.assert_awaited_once_with(message_id=101092384)
