from __future__ import annotations

import re

from nonebot import logger, on_message, on_notice
from nonebot.adapters import Bot  # noqa: TC002
from nonebot.adapters.onebot.v11 import GroupMessageEvent, GroupRecallNoticeEvent, Message, permission
from nonebot.exception import ActionFailed
from nonebot.permission import SUPERUSER, Permission
from nonebot.rule import Rule, keyword, to_me

from src.common.config import BotConfig
from src.common.utils.array2cqcode import try_convert_to_cqcode
from src.plugins.repeater.ban_state import REPEATER_BAN_ACK_SENT_STATE_KEY

from .ban_cleanup import delete_dream_messages_from_ban_reply

_BAN_ACK_TEXT = "这对角可能会不小心撞倒些家具，我会尽量小心。"


async def is_config_admin_dream(event: GroupMessageEvent) -> bool:
    return await BotConfig(event.self_id).is_admin_of_bot(event.user_id)


IsAdminDream = permission.GROUP_OWNER | permission.GROUP_ADMIN | SUPERUSER | Permission(is_config_admin_dream)


async def is_reply_for_ban(event: GroupMessageEvent) -> bool:
    return bool(event.reply)


dream_ban_cleanup_msg = on_message(
    rule=to_me() & keyword("不可以") & Rule(is_reply_for_ban),
    priority=6,
    block=False,
    permission=IsAdminDream,
)


@dream_ban_cleanup_msg.handle()
async def _(_bot: Bot, event: GroupMessageEvent):
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
        logger.info("bot [{}] removed {} dream record(s) via 不可以 (dream plugin)", event.self_id, n)
        if not event.state.get(REPEATER_BAN_ACK_SENT_STATE_KEY):
            try:
                await dream_ban_cleanup_msg.send(_BAN_ACK_TEXT)
            except ActionFailed as e:
                logger.debug("dream ban_cleanup_msg send ack failed: {}", e)


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
    priority=6,
    block=False,
)


@dream_ban_cleanup_recall.handle()
async def _(bot: Bot, event: GroupRecallNoticeEvent):
    try:
        msg = await bot.get_msg(message_id=event.message_id)
    except ActionFailed:
        logger.warning("bot [{}] dream ban recall: get_msg failed [{}]", event.self_id, event.message_id)
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
        logger.info("bot [{}] removed {} dream record(s) via recall (dream plugin)", event.self_id, n)
        if not event.state.get(REPEATER_BAN_ACK_SENT_STATE_KEY):
            try:
                await bot.send_group_msg(group_id=event.group_id, message=_BAN_ACK_TEXT)
            except ActionFailed as e:
                logger.debug("dream ban_cleanup_recall send ack failed: {}", e)
