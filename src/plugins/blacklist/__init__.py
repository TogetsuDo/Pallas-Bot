import re

from nonebot import logger, on_command
from nonebot.adapters import Bot, Event
from nonebot.adapters.onebot.v11 import (
    FriendRequestEvent,
    GroupMessageEvent,
    GroupRecallNoticeEvent,
    GroupRequestEvent,
    GroupUploadNoticeEvent,
    MessageEvent,
    PokeNotifyEvent,
    PrivateMessageEvent,
)
from nonebot.exception import IgnoredException
from nonebot.message import event_preprocessor
from nonebot.plugin import PluginMetadata

from src.common.cmd_perm import permission_for_command, satisfies_command_permission
from src.common.config import UserConfig

__plugin_meta__ = PluginMetadata(
    name="牛牛黑名单",
    description="拉黑用户，防止牛牛与被拉黑用户进行交互。",
    usage="""
牛牛拉黑 / 牛牛屏蔽 + qq（可多个，可 @）— 写入全局拉黑
牛牛解禁（别名：牛牛取消屏蔽、牛牛取消拉黑）— 解除拉黑
""".strip(),
    type="application",
    homepage="https://github.com/PallasBot/Pallas-Bot",
    supported_adapters={"~onebot.v11"},
    extra={
        "version": "3.0.0",
        "command_permissions": [
            {"id": "blacklist.add", "label": "牛牛拉黑 / 牛牛屏蔽", "default": "staff"},
            {"id": "blacklist.remove", "label": "牛牛解禁", "default": "staff"},
        ],
        "menu_data": [
            {
                "func": "事件门禁",
                "trigger_method": "event_preprocessor",
                "trigger_condition": "OneBot V11 消息/通知等",
                "brief_des": "已拉黑用户的事件不再进入后续插件",
                "detail_des": "屏蔽来自此用户的所有消息",
            },
            {
                "func": "拉黑与解禁",
                "trigger_method": "命令",
                "trigger_condition": "牛牛拉黑 / 牛牛屏蔽 / 牛牛解禁",
                "command_permissions": ["blacklist.add", "blacklist.remove"],
                "brief_des": "按 QQ 写入或清除全局拉黑",
                "detail_des": "支持正文中的多个 QQ 号或 @；不会拉黑 bot 自身。",
            },
        ],
        "menu_template": "default",
    },
)


def collect_target_qqs_from_plain_and_message(plain_text: str, message) -> list[int]:
    ids: list[int] = []
    for seg in message:
        if seg.type != "at":
            continue
        qq = seg.data.get("qq")
        if qq in (None, "all", "0"):
            continue
        try:
            ids.append(int(qq))
        except (TypeError, ValueError):
            continue
    ids.extend(int(m.group(1)) for m in re.finditer(r"(?<![0-9])([1-9][0-9]{4,14})(?![0-9])", plain_text or ""))
    out: list[int] = []
    seen: set[int] = set()
    for uid in ids:
        if uid not in seen:
            seen.add(uid)
            out.append(uid)
    return out


def event_actor_user_id(event: Event) -> int | None:
    if isinstance(event, MessageEvent):
        uid = getattr(event, "user_id", None)
        return uid if isinstance(uid, int) else None
    if isinstance(event, (PokeNotifyEvent, GroupUploadNoticeEvent, FriendRequestEvent)):
        return event.user_id
    if isinstance(event, GroupRequestEvent):
        return event.user_id
    if isinstance(event, GroupRecallNoticeEvent):
        return event.operator_id
    op = getattr(event, "operator_id", None)
    if isinstance(op, int):
        return op
    uid = getattr(event, "user_id", None)
    return uid if isinstance(uid, int) else None


@event_preprocessor
async def block_globally_banned_users(bot: Bot, event: Event):
    if "onebot.v11" not in type(event).__module__:
        return
    uid = event_actor_user_id(event)
    if uid is None:
        return
    if uid == int(bot.self_id):
        return
    if not await UserConfig(uid).is_banned():
        return

    if isinstance(event, FriendRequestEvent):
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


async def can_manage_blacklist(bot: Bot, event: Event) -> bool:
    if not isinstance(event, (GroupMessageEvent, PrivateMessageEvent)):
        return False
    return await satisfies_command_permission(bot, event, "blacklist.add")


blacklist_add_cmd = on_command(
    "牛牛拉黑",
    aliases={"牛牛屏蔽"},
    priority=5,
    block=True,
    permission=permission_for_command("blacklist.add"),
)

blacklist_remove_cmd = on_command(
    "牛牛解禁",
    aliases={"牛牛取消屏蔽", "牛牛取消拉黑"},
    priority=5,
    block=True,
    permission=permission_for_command("blacklist.remove"),
)


@blacklist_add_cmd.handle()
async def handle_blacklist_add(bot: Bot, event: GroupMessageEvent | PrivateMessageEvent):
    plain = event.get_plaintext()
    targets = collect_target_qqs_from_plain_and_message(plain, event.message)
    targets = [u for u in targets if u != event.self_id]
    if not targets:
        await blacklist_add_cmd.finish("博士，谁将失去米诺斯的眷顾？")
        return
    for uid in targets:
        await UserConfig(uid).ban()
    await blacklist_add_cmd.finish(f"米诺斯不再眷顾这 {len(targets)} 个灵魂：{', '.join(map(str, targets))}")


@blacklist_remove_cmd.handle()
async def handle_blacklist_remove(bot: Bot, event: GroupMessageEvent | PrivateMessageEvent):
    plain = event.get_plaintext()
    targets = collect_target_qqs_from_plain_and_message(plain, event.message)
    targets = [u for u in targets if u != event.self_id]
    if not targets:
        await blacklist_remove_cmd.finish("博士，有哪一些人又获得了米诺斯的眷顾？")
        return
    for uid in targets:
        await UserConfig(uid).unban()
    await blacklist_remove_cmd.finish(f"这 {len(targets)} 个灵魂又获得了米诺斯的眷顾：{', '.join(map(str, targets))}")
