import asyncio
import random

from nonebot import logger, on_message
from nonebot.adapters.onebot.v11 import GroupMessageEvent, permission
from nonebot.exception import ActionFailed
from nonebot.plugin import PluginMetadata
from nonebot.rule import Rule

from src.common.config import BotConfig, GroupConfig

from . import ban_handlers as _dream_ban_handlers  # noqa: F401 — 注册梦库「不可以」/撤回清理
from .http_utils import download_image_url
from .payload import DriftPayload
from .runtime import (
    broadcast_drift,
    launch_dream_worker,
    log_dream_chat_to_db,
    stop_dream_worker,
)

__plugin_meta__ = PluginMetadata(
    name="牛牛做梦",
    description=(
        "牛牛的梦话：多群同时做梦时漂流互通，随机间隔推送历史梦、归档画或已学句。与复读共用管理员「不可以」触发方式，"
    ),
    usage="""
指令：
- 牛牛做梦 — 进入做梦（持续约 5～15 分钟；推送间隔约 20～45s）
- 牛牛醒梦 / 牛牛别做梦 — 结束本群做梦

做梦中会自动采集群消息入梦库，并向其它做梦群漂流（图/文有上限）。

管理员（与复读相同权限）：回复牛牛消息后 发送「不可以」，或撤回牛牛消息 —
会从梦库删除与所针对内容匹配的消息
    """.strip(),
    type="application",
    homepage="https://github.com/PallasBot",
    supported_adapters={"~onebot.v11"},
    extra={
        "version": "3.0.0",
        "menu_data": [
            {
                "func": "牛牛做梦",
                "trigger_method": "on_message",
                "trigger_condition": "牛牛做梦",
                "brief_des": "进入做梦漂流状态",
                "detail_des": (
                    "进梦后可收到他群漂流、历史梦、牛牛画画归档图或已学句；同一场梦内已发过的正文/图片不重复投放。"
                    "多 Bot 同群时有群级冷却，避免同时抢触发。"
                ),
            },
            {
                "func": "牛牛醒梦",
                "trigger_method": "on_message",
                "trigger_condition": "牛牛醒梦/牛牛别做梦",
                "brief_des": "结束做梦",
                "detail_des": "立即结束本群的做梦状态并停止后台推送。",
            },
            {
                "func": "梦话采集",
                "trigger_method": "on_message",
                "trigger_condition": "本群处于做梦中",
                "brief_des": "群聊写入梦库并可跨群漂流",
                "detail_des": (
                    "做梦期间群友消息异步写入 message（is_dream）；"
                    "纯文本与少量图片可随机投递到同 Bot 其它正在做梦的群。"
                ),
            },
            {
                "func": "梦库清理（不可以）",
                "trigger_method": "on_message",
                "trigger_condition": "回复消息后 @牛牛 发送不可以",
                "brief_des": "按所回复内容删除梦库记录",
                "detail_des": ("与复读「不可以」操作方式相同"),
            },
            {
                "func": "梦库清理（撤回）",
                "trigger_method": "on_notice",
                "trigger_condition": "管理员撤回牛牛消息",
                "brief_des": "按被撤回消息删除梦库记录",
                "detail_des": ("与复读撤回封禁同一触发场景；删到梦库且复读未 finish 时才发确认句。"),
            },
        ],
        "menu_template": "default",
    },
)

_PLAIN_TRIGGERS = frozenset({"牛牛做梦", "牛牛醒梦", "牛牛别做梦"})
DREAM_GROUP_COOLDOWN_KEY = "dream"
DREAM_GROUP_COOLDOWN_SEC = 10


async def is_dream_start(event: GroupMessageEvent) -> bool:
    return event.get_plaintext().strip() == "牛牛做梦"


dream_start = on_message(
    rule=Rule(is_dream_start),
    priority=5,
    block=True,
    permission=permission.GROUP,
)


@dream_start.handle()
async def _(event: GroupMessageEvent):
    config = BotConfig(event.self_id, event.group_id, cooldown=3)
    if not await config.is_cooldown("dream"):
        return
    group_cfg = GroupConfig(event.group_id, cooldown=DREAM_GROUP_COOLDOWN_SEC)
    if not await group_cfg.is_cooldown(DREAM_GROUP_COOLDOWN_KEY):
        return
    await group_cfg.refresh_cooldown(DREAM_GROUP_COOLDOWN_KEY)
    await config.refresh_cooldown("dream")
    duration = random.randint(300, 900)
    try:
        await dream_start.send("博士，只要相信，梦就会成为现实。")
    except ActionFailed:
        pass
    await launch_dream_worker(event.self_id, event.group_id, duration)
    logger.info("bot [{}] dream started in group [{}] for {}s", event.self_id, event.group_id, duration)


async def is_dream_wake(event: GroupMessageEvent) -> bool:
    return event.get_plaintext().strip() in {"牛牛醒梦", "牛牛别做梦"}


dream_wake = on_message(
    rule=Rule(is_dream_wake),
    priority=5,
    block=True,
    permission=permission.GROUP,
)


@dream_wake.handle()
async def _(event: GroupMessageEvent):
    config = BotConfig(event.self_id, event.group_id)
    if not await config.is_dreaming():
        return
    await config.stop_dream()
    await stop_dream_worker(event.self_id, event.group_id)
    try:
        await dream_wake.send("……梦醒了。")
    except ActionFailed:
        pass


async def is_dream_capture(event: GroupMessageEvent) -> bool:
    if event.user_id == event.self_id:
        return False
    cfg = BotConfig(event.self_id, event.group_id)
    return await cfg.is_dreaming()


dream_capture = on_message(
    rule=Rule(is_dream_capture),
    priority=18,
    block=False,
    permission=permission.GROUP,
)


@dream_capture.handle()
async def _(event: GroupMessageEvent):
    plain = event.get_plaintext().strip()
    if plain in _PLAIN_TRIGGERS:
        return

    async def job():
        try:
            await log_dream_chat_to_db(event)
            nick = (event.sender.card or event.sender.nickname or str(event.user_id)).strip() or str(event.user_id)
            img_n = 0
            for seg in event.message:
                if seg.type != "image":
                    continue
                if img_n >= 2:
                    break
                url = (seg.data.get("url") or seg.data.get("file") or "").strip()
                if not url:
                    continue
                data = await download_image_url(url)
                if data:
                    await broadcast_drift(
                        event.self_id,
                        event.group_id,
                        DriftPayload(nickname=nick, image_bytes=data),
                    )
                    img_n += 1
            if plain and len(plain) <= 800:
                await broadcast_drift(event.self_id, event.group_id, DriftPayload(nickname=nick, text=plain))
        except Exception as e:
            logger.debug("dream capture job failed: {}", e)

    asyncio.create_task(job())
