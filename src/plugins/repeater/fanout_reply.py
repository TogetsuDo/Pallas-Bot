"""多牛同群：判定可接话时由舰队内各牛各自发送（分片跨 worker）；context 只查一次。"""

from __future__ import annotations

import asyncio
import random
from typing import TYPE_CHECKING, Any

from nonebot import get_bot, get_bots, logger
from nonebot.exception import ActionFailed

if TYPE_CHECKING:
    from nonebot.adapters.onebot.v11 import GroupMessageEvent

from src.common.bot_runtime.send_unavailable import BOT_SEND_UNAVAILABLE_ERRORS, log_bot_send_unavailable
from src.common.config import BotConfig
from src.common.multi_bot.dedup import try_claim_cross_bot_message
from src.common.shard.registry.config import is_sharding_active

from .model import Chat, ChatData
from .responder import ReplyBundle, Responder

_FANOUT_PLUGIN = "repeater_fanout"


def repeater_fanout_enabled() -> bool:
    if is_sharding_active():
        return True
    return len(get_bots()) > 1


def fanout_payload_from_event(event: GroupMessageEvent, bundle: ReplyBundle) -> dict[str, Any]:
    return {
        "group_id": int(event.group_id),
        "user_id": int(event.user_id),
        "raw_message": event.raw_message,
        "plain_text": (event.get_plaintext() or "").strip(),
        "time": int(event.time),
        "reply_bundle": {
            "answer_list": list(bundle.answer_list),
            "answer_keywords": bundle.answer_keywords,
            "message_pool": list(bundle.message_pool),
        },
    }


def bundle_from_payload(payload: dict[str, Any]) -> ReplyBundle | None:
    raw = payload.get("reply_bundle")
    if not isinstance(raw, dict):
        return None
    answer_list = raw.get("answer_list")
    if not isinstance(answer_list, list) or not answer_list:
        return None
    keywords = str(raw.get("answer_keywords") or "")
    pool = raw.get("message_pool")
    if not isinstance(pool, list) or not pool:
        pool = list(answer_list)
    return ReplyBundle(
        answer_list=[str(x) for x in answer_list],
        answer_keywords=keywords,
        message_pool=[str(x) for x in pool],
    )


async def bot_may_repeater_reply(bot_id: int, group_id: int) -> bool:
    cfg = BotConfig(bot_id, group_id)
    if await cfg.is_sleep():
        return False
    try:
        from src.plugins.help.plugin_manager import is_plugin_disabled

        if await is_plugin_disabled("repeater", group_id, bot_id):
            return False
    except Exception:
        pass
    return True


async def list_fanout_bot_ids(group_id: int) -> list[int]:
    from src.plugins.duel.duel_bots import list_group_online_bot_ids

    ids = await list_group_online_bot_ids(group_id)
    if not ids:
        return []
    allowed = await asyncio.gather(*(bot_may_repeater_reply(bid, group_id) for bid in ids))
    return [bid for bid, ok in zip(ids, allowed, strict=True) if ok]


async def send_repeater_answers(bot_id: int, group_id: int, answers) -> None:
    from src.plugins.repeater import post_proc

    from .model import Chat

    config = BotConfig(bot_id, group_id)
    await config.refresh_cooldown("repeat")
    delay = random.randint(2, 5)
    bot = get_bot(str(bot_id))
    async for item in answers:
        msg = await post_proc(item, bot_id, group_id)
        logger.info(f"bot [{bot_id}] ready to send [{str(msg)[:30]}] to group [{group_id}] (fanout)")
        await asyncio.sleep(delay)
        await config.refresh_cooldown("repeat")
        try:
            await bot.send_group_msg(group_id=group_id, message=msg)
        except BOT_SEND_UNAVAILABLE_ERRORS as e:
            log_bot_send_unavailable(e, context="repeater_fanout", bot=bot_id, group=group_id)
            return
        except ActionFailed:
            if not await BotConfig(bot_id).security():
                continue
            from src.plugins.repeater import is_shutup

            shutup = await is_shutup(bot_id, group_id)
            if not shutup:
                logger.info(f"bot [{bot_id}] ready to ban [{str(item)}] in group [{group_id}] (fanout)")
                await Chat.ban(group_id, bot_id, str(item), "ActionFailed")
                break
        delay = random.randint(1, 3)


async def run_repeater_reply_for_bot(bot_id: int, payload: dict[str, Any]) -> None:
    group_id = int(payload["group_id"])
    if not await bot_may_repeater_reply(bot_id, group_id):
        return
    config = BotConfig(bot_id, group_id)
    if not await config.is_cooldown("repeat"):
        return
    bundle = bundle_from_payload(payload)
    if bundle is None:
        return
    chat_data = ChatData(
        group_id=group_id,
        user_id=int(payload["user_id"]),
        raw_message=str(payload["raw_message"]),
        plain_text=str(payload["plain_text"]),
        time=int(payload["time"]),
        bot_id=bot_id,
    )
    plan = Responder.pick_fanout_plan(bundle)
    chat = Chat(chat_data)
    answers = await chat.answer_from_bundle(bundle, plan=plan)
    if not answers:
        return
    await send_repeater_answers(bot_id, group_id, answers)


async def dispatch_repeater_fanout(event: GroupMessageEvent, bot_ids: list[int], bundle: ReplyBundle) -> None:
    payload = fanout_payload_from_event(event, bundle)
    group_id = int(event.group_id)
    stagger = 0.35
    for i, bid in enumerate(bot_ids):
        from src.common.shard.presence import bot_has_local_connection

        delay = i * stagger
        if bot_has_local_connection(bid):
            asyncio.create_task(
                _delayed_local_reply(delay, bid, payload),
                name=f"repeater_fanout_{bid}_{group_id}",
            )
        elif is_sharding_active():
            asyncio.create_task(
                _delayed_remote_reply(delay, bid, payload),
                name=f"repeater_fanout_remote_{bid}_{group_id}",
            )


async def _delayed_local_reply(delay: float, bot_id: int, payload: dict[str, Any]) -> None:
    if delay > 0:
        await asyncio.sleep(delay)
    await run_repeater_reply_for_bot(bot_id, payload)


async def _delayed_remote_reply(delay: float, bot_id: int, payload: dict[str, Any]) -> None:
    if delay > 0:
        await asyncio.sleep(delay)
    from src.common.shard.coord.bot_action import invoke_bot_action

    await invoke_bot_action(
        "repeater_fanout_reply",
        int(bot_id),
        payload,
        timeout_sec=45.0,
    )


async def maybe_orchestrate_repeater_fanout(event: GroupMessageEvent, bundle: ReplyBundle | None) -> bool:
    """返回 True 表示已走 fanout，调用方勿再单牛发送。"""
    if not repeater_fanout_enabled() or bundle is None:
        return False
    bot_ids = await list_fanout_bot_ids(int(event.group_id))
    if len(bot_ids) < 2:
        return False
    if not await try_claim_cross_bot_message(
        _FANOUT_PLUGIN,
        event.group_id,
        event.user_id,
        event.get_plaintext(),
        event.time,
        int(event.self_id),
        use_plaintext=True,
    ):
        return True
    await dispatch_repeater_fanout(event, bot_ids, bundle)
    return True
