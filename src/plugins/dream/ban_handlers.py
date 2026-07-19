from __future__ import annotations

import re

from nonebot import logger, on_message, on_notice
from nonebot.adapters import Bot  # noqa: TC002
from nonebot.adapters.onebot.v11 import GroupMessageEvent, GroupRecallNoticeEvent, Message
from nonebot.exception import ActionFailed
from nonebot.rule import Rule
from nonebot.typing import T_State  # noqa: TC002

from src.features.cmd_perm import group_message_permission_for_command
from src.shared.reply_command_rule import event_has_reply_target, event_targets_self, extract_reply_id_from_raw_message
from src.shared.utils.array2cqcode import try_convert_to_cqcode

from .ban_ack_state import DREAM_BAN_ACK_SENT_STATE_KEY
from .ban_cleanup import delete_dream_messages_from_ban_reply

_BAN_ACK_TEXT = "这对角可能会不小心撞倒些家具，我会尽量小心。"


async def is_reply_for_ban(event: GroupMessageEvent) -> bool:
    return event_has_reply_target(event)


async def is_dream_ban_trigger(event: GroupMessageEvent) -> bool:
    if "不可以" not in event.get_plaintext():
        return False
    if not await is_reply_for_ban(event):
        return False
    return event_targets_self(event)


def extract_dream_ban_reply_raw_from_message(message: Message | str) -> str:
    if isinstance(message, str):
        return message

    raw_message = ""
    for item in message:
        raw_reply = str(item)
        raw_message += re.sub(r"(\[CQ\:.+)(?:,url=*)(\])", r"\1\2", raw_reply)
    if not raw_message.strip():
        raw_message = message.extract_plain_text()
    return raw_message


async def resolve_dream_ban_reply_raw(bot: Bot, event: GroupMessageEvent) -> str:
    if event.reply and getattr(event.reply, "message", None):
        return extract_dream_ban_reply_raw_from_message(event.reply.message)

    reply_id = extract_reply_id_from_raw_message(event.raw_message)
    if reply_id is None:
        return ""

    try:
        msg = await bot.get_msg(message_id=reply_id)
    except ActionFailed:
        logger.warning(
            f"bot [{event.self_id}] dream ban cleanup get_msg failed in group [{event.group_id}] "
            f"for reply_id [{reply_id}]"
        )
        return ""

    return extract_dream_ban_reply_raw_from_message(Message(msg["message"]))


dream_ban_cleanup_msg = on_message(
    rule=Rule(is_dream_ban_trigger),
    priority=4,
    block=False,
    permission=group_message_permission_for_command("dream.ban_cleanup"),
)


@dream_ban_cleanup_msg.handle()
async def _(_bot: Bot, event: GroupMessageEvent, state: T_State):
    raw_message = await resolve_dream_ban_reply_raw(_bot, event)
    if not raw_message.strip():
        return
    reply_plain = ""
    try:
        if event.reply and getattr(event.reply, "message", None):
            reply_plain = event.reply.message.extract_plain_text()
        elif raw_message:
            reply_plain = Message(raw_message).extract_plain_text()
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
