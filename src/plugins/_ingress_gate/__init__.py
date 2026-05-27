"""分片 worker 专用预处理器：fleet 识别、@ 定向、全局 claim、fanout。"""

from __future__ import annotations

from nonebot import get_driver, logger
from nonebot.adapters.onebot.v11 import GroupMessageEvent
from nonebot.exception import IgnoredException
from nonebot.message import event_preprocessor
from nonebot.plugin import PluginMetadata

from src.features.cmd_perm.metadata_defaults import (
    PLUGIN_EXTRA_VERSION,
    PLUGIN_HOMEPAGE,
    PLUGIN_MENU_TEMPLATE,
)
from src.platform.bot_runtime.roles import is_hub_role
from src.platform.federate.ingress import claim_federate_group_message_ingress
from src.platform.ingress.cage_plaintext import is_cage_plaintext
from src.platform.ingress.drink_plaintext import is_drink_plaintext
from src.platform.ingress.roulette_plaintext import is_roulette_plaintext
from src.platform.multi_bot.dedup import try_claim_cross_bot_message, try_claim_cross_shard_message
from src.platform.multi_bot.fleet import fleet_bot_ids_contains, get_fleet_bot_ids
from src.platform.shard.coord.bot_count import should_skip_ingress_claim_for_shard_bot_count
from src.platform.shard.ingress_fanout import is_ingress_fanout_plaintext
from src.platform.shard.ingress_metrics import (
    record_ingress_claim,
    record_ingress_early_discard,
    record_ingress_event,
    record_ingress_fanout_bypass,
    should_record_ingress_metrics,
)
from src.platform.shard.registry.config import get_shard_registry_settings, is_sharding_active

INGRESS_CLAIM_PLUGIN = "ingress_gate"
INGRESS_SHARD_CLAIM_PLUGIN = "ingress_gate_shard"
driver = get_driver()

__plugin_meta__ = PluginMetadata(
    name="分片入站网关",
    description=(
        "Worker 群消息预处理：牛牛舰队识别、@ 定向、跨 Bot/分片 claim、"
        "问候与报数 fanout，避免同条消息被多个进程重复处理。"
    ),
    usage="（内部）无用户命令；分片 Worker 启动时自动注册 event_preprocessor。",
    type="application",
    homepage=PLUGIN_HOMEPAGE,
    supported_adapters={"~onebot.v11"},
    extra={
        "version": PLUGIN_EXTRA_VERSION,
        "menu_template": PLUGIN_MENU_TEMPLATE,
        "help_audience": "maintainer",
    },
)


def ingress_gate_active() -> bool:
    if is_hub_role():
        return False
    return True


def group_at_qq_ids(event: GroupMessageEvent) -> frozenset[int]:
    out: set[int] = set()
    for seg in event.message:
        if seg.type != "at":
            continue
        qq = seg.data.get("qq")
        if qq is None or str(qq) in ("all", "0"):
            continue
        try:
            out.add(int(qq))
        except (TypeError, ValueError):
            continue
    return frozenset(out)


@event_preprocessor
async def ingress_group_message_gate(bot, event) -> None:
    if not ingress_gate_active():
        return
    if not isinstance(event, GroupMessageEvent):
        return

    self_id = int(bot.self_id)
    user_id = int(event.user_id)
    metrics = should_record_ingress_metrics(self_id)

    if metrics:
        record_ingress_event()

    if fleet_bot_ids_contains(user_id) and user_id != self_id:
        if metrics:
            record_ingress_early_discard("fleet")
        raise IgnoredException("fleet bot message")

    ats = group_at_qq_ids(event)
    if ats:
        fleet = get_fleet_bot_ids()
        pallas_ats = ats & fleet
        if pallas_ats and self_id not in pallas_ats:
            if metrics:
                record_ingress_early_discard("not_at_target")
            raise IgnoredException("not at-target bot")

    plain = (event.get_plaintext() or "").strip()
    body = plain or event.raw_message
    if not await claim_federate_group_message_ingress(event):
        if metrics:
            record_ingress_early_discard("federate")
        raise IgnoredException("federate ingress claim lost")

    if is_sharding_active() and (
        is_ingress_fanout_plaintext(plain)
        or should_skip_ingress_claim_for_shard_bot_count(plain)
        or is_cage_plaintext(plain)
        or is_drink_plaintext(plain)
        or is_roulette_plaintext(plain)
    ):
        if metrics:
            record_ingress_fanout_bypass()
        return

    if is_sharding_active():
        shard_id = get_shard_registry_settings().shard_id
        # 不传 bot_id：避免「代表牛」不在群内时非代表牛永远无法通过文件 claim（如群内发牛牛网关）
        if not await try_claim_cross_shard_message(
            INGRESS_SHARD_CLAIM_PLUGIN,
            event.group_id,
            user_id,
            body,
            event.time,
            shard_id,
            use_plaintext=True,
            include_message_time=True,
        ):
            if metrics:
                record_ingress_claim(won=False)
            raise IgnoredException("ingress shard claim lost")
        if not await try_claim_cross_bot_message(
            INGRESS_CLAIM_PLUGIN,
            event.group_id,
            user_id,
            body,
            event.time,
            self_id,
            use_plaintext=True,
            include_message_time=True,
        ):
            if metrics:
                record_ingress_claim(won=False)
            raise IgnoredException("ingress bot claim lost")
        if metrics:
            record_ingress_claim(won=True)
        return

    if not await try_claim_cross_bot_message(
        INGRESS_CLAIM_PLUGIN,
        event.group_id,
        user_id,
        body,
        event.time,
        self_id,
        use_plaintext=True,
        include_message_time=True,
    ):
        if metrics:
            record_ingress_claim(won=False)
        raise IgnoredException("ingress claim lost")
    if metrics:
        record_ingress_claim(won=True)


@driver.on_startup
async def _log_ingress_gate() -> None:
    if not ingress_gate_active():
        return
    from src.platform.federate.config import federate_ingress_active, resolved_federate_id

    n = len(get_fleet_bot_ids())
    mode = "shard" if is_sharding_active() else "unified"
    fed = "on" if federate_ingress_active() else "off"
    logger.info(
        "ingress_gate: active mode={} fleet_bots={} federate_ingress={} federate_id={}",
        mode,
        n,
        fed,
        resolved_federate_id() or "-",
    )
