from __future__ import annotations

import re

from nonebot import logger, on_message, on_notice
from nonebot.adapters import Bot  # noqa: TC002
from nonebot.adapters.onebot.v11 import GroupMessageEvent, GroupRecallNoticeEvent, Message, permission
from nonebot.exception import ActionFailed
from nonebot.permission import SUPERUSER, Permission
from nonebot.rule import Rule, keyword, to_me
from nonebot.typing import T_State  # noqa: TC002

from src.common.config import user_is_bot_admin
from src.common.utils.array2cqcode import try_convert_to_cqcode

from .ban_ack_state import DREAM_BAN_ACK_SENT_STATE_KEY
from .ban_cleanup import delete_dream_messages_from_ban_reply

_BAN_ACK_TEXT = "这对角可能会不小心撞倒些家具，我会尽量小心。"


async def is_config_admin_dream(event: GroupMessageEvent) -> bool:
    return await user_is_bot_admin(event.self_id, event.user_id)


IsAdminDream = permission.GROUP_OWNER | permission.GROUP_ADMIN | SUPERUSER | Permission(is_config_admin_dream)


async def is_reply_for_ban(event: GroupMessageEvent) -> bool:
    return bool(event.reply)


dream_ban_cleanup_msg = on_message(
    rule=to_me() & keyword("不可以") & Rule(is_reply_for_ban),
    priority=4,
    block=False,
    permission=IsAdminDream,
)


@dream_ban_cleanup_msg.handle()
async def _(_bot: Bot, event: GroupMessageEvent, state: T_State):
    if "[CQ:reply," not in try_convert_to_cqcode(event.raw_message):
        return
    raw_message = ""
    for item in event.reply.message:  # type: ignore
        raw_reply = str(item)
        raw_message += re.sub(r"(\[CQ\:.+)(?:,url=*)(\])", r"\1\2", raw_reply)
    reply_plain = ""
    try:
        if event.reply and getattr(event.reply, "message", None):
            reply_plain = event.reply.message.extract_plain_text()
    except Exception:
        pass
    n = await delete_dream_messages_from_ban_reply(
        bot_id=event.self_id,
        reply_cq_raw=raw_message,
        reply_plain=reply_plain,
    )
    if n:
        logger.info(
            f"bot [{event.self_id}] removed {n} dream record(s) via admin ban reply in group [{event.group_id}]"
        )
        state[DREAM_BAN_ACK_SENT_STATE_KEY] = True
        try:
            await dream_ban_cleanup_msg.send(_BAN_ACK_TEXT)
        except ActionFailed as e:
            logger.debug(f"bot [{event.self_id}] dream ban cleanup send ack failed in group [{event.group_id}]: {e}")


async def is_admin_recall_dream_cleanup(bot: Bot, event: GroupRecallNoticeEvent) -> bool:
    self_id = event.self_id
    user_id = event.user_id
    group_id = event.group_id
    operator_id = event.operator_id
    if self_id != user_id:
        return False
    if operator_id == self_id:
        return False
    operator_info = await bot.get_group_member_info(group_id=group_id, user_id=operator_id)
    return operator_info["role"] == "owner" or operator_info["role"] == "admin"


dream_ban_cleanup_recall = on_notice(
    rule=Rule(is_admin_recall_dream_cleanup),
    priority=4,
    block=False,
)


@dream_ban_cleanup_recall.handle()
async def _(bot: Bot, event: GroupRecallNoticeEvent, state: T_State):
    try:
        msg = await bot.get_msg(message_id=event.message_id)
    except ActionFailed:
        logger.warning(
            f"bot [{event.self_id}] dream recall get_msg failed in group [{event.group_id}] "
            f"for msg_id [{event.message_id}]"
        )
        return

    raw_message = ""
    for item in re.compile(r"\[[^\]]*\]|\w+").findall(try_convert_to_cqcode(msg["message"])):
        raw_reply = str(item)
        raw_message += re.sub(r"(\[CQ\:.+)(?:,url=*)(\])", r"\1\2", raw_reply)

    reply_plain = ""
    try:
        reply_plain = Message(msg["message"]).extract_plain_text()
    except Exception:
        pass
    n = await delete_dream_messages_from_ban_reply(
        bot_id=event.self_id,
        reply_cq_raw=raw_message,
        reply_plain=reply_plain,
    )
    if n:
        logger.info(f"bot [{event.self_id}] removed {n} dream record(s) via admin recall in group [{event.group_id}]")
        state[DREAM_BAN_ACK_SENT_STATE_KEY] = True
        try:
            await bot.send_group_msg(group_id=event.group_id, message=_BAN_ACK_TEXT)
        except ActionFailed as e:
            logger.debug(
                f"bot [{event.self_id}] dream ban cleanup recall send ack failed in group [{event.group_id}]: {e}"
            )
