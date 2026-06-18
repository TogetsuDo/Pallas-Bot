from nonebot import logger
from nonebot.adapters import Bot, Event
from nonebot.adapters.onebot.v11 import FriendRequestEvent, GroupRequestEvent
from nonebot.exception import IgnoredException
from nonebot.message import event_preprocessor
from nonebot.utils import run_coro_with_shield

from .ban_gate import query_group_ban_status_for_gate, query_group_blocked_for_gate, query_user_ban_status_for_gate
from .helpers import event_actor_user_id, event_group_id


@event_preprocessor
async def block_globally_banned_users(bot: Bot, event: Event):
    if "onebot.v11" not in type(event).__module__:
        return

    gid = event_group_id(event)
    if gid is not None:
        group_banned = await run_coro_with_shield(query_group_ban_status_for_gate(gid))
        if group_banned:
            logger.debug(f"drop event in banned group [{gid}]")
            raise IgnoredException("banned group")

    uid = event_actor_user_id(event)
    if uid is None:
        return
    if uid == int(bot.self_id):
        return

    async def resolve_ban_gate() -> tuple[bool, bool]:
        global_banned = await query_user_ban_status_for_gate(uid)
        group_blocked = await query_group_blocked_for_gate(gid, uid) if gid is not None else False
        return global_banned, group_blocked

    global_banned, group_blocked = await run_coro_with_shield(resolve_ban_gate())

    if not global_banned and not group_blocked:
        return

    if isinstance(event, FriendRequestEvent):
        if not global_banned:
            return
        try:
            await event.reject(bot)
        except Exception as e:
            logger.warning(f"reject friend request from banned user [{uid}] failed: {e}")
        raise IgnoredException("banned user")

    if isinstance(event, GroupRequestEvent) and event.sub_type == "invite":
        try:
            await event.reject(bot)
        except Exception as e:
            logger.warning(f"reject group invite from banned user [{uid}] failed: {e}")
        raise IgnoredException("banned user")

    logger.debug(f"drop event [{type(event).__name__}] from banned user [{uid}]")
    raise IgnoredException("banned user")
