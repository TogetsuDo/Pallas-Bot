"""号主入库：解析参数并写入 bot_config.admins。"""

from __future__ import annotations

import re

from pallas.core.foundation.command_prefix import extract_command_tail
from pallas.core.foundation.db import make_bot_config_repository

ADD_BOT_ADMIN_COMMAND = "牛牛添加号主"

_QQ_RE = re.compile(r"(?<![0-9])([1-9][0-9]{4,14})(?![0-9])")


def collect_qq_ids_from_plain_and_message(plain_text: str, message) -> list[int]:
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
    ids.extend(int(m.group(1)) for m in _QQ_RE.finditer(plain_text or ""))
    out: list[int] = []
    seen: set[int] = set()
    for uid in ids:
        if uid not in seen:
            seen.add(uid)
            out.append(uid)
    return out


def parse_add_bot_admin_targets(plain_text: str, message, *, self_id: int) -> tuple[int, list[int]] | None:
    """
    解析「牛牛添加号主」目标。

    - 仅 1 个 QQ：视为当前牛的号主。
    - 首个 QQ 等于当前牛 QQ：其余为号主。
    - 首个 QQ 不等于当前牛 QQ：首个为牛牛 QQ，其余为号主。
    """
    tail = extract_command_tail(plain_text, ADD_BOT_ADMIN_COMMAND)
    if not tail:
        source = plain_text or ""
    else:
        source = tail
    ids = collect_qq_ids_from_plain_and_message(source, message)
    if not ids:
        return None
    bot_id = int(self_id)
    if len(ids) == 1:
        if ids[0] == bot_id:
            return None
        return bot_id, ids
    if ids[0] == bot_id:
        bot_id = int(self_id)
        admin_ids = ids[1:]
    else:
        bot_id = ids[0]
        admin_ids = ids[1:]
    admins = [uid for uid in admin_ids if uid != bot_id]
    if not admins:
        return None
    return bot_id, admins


async def add_bot_admins(bot_id: int, admin_ids: list[int]) -> tuple[bool, list[int], list[int]]:
    """
    确保 bot_config 行存在，并合并号主 QQ。

    返回 (是否新建行, 合并后的 admins, 本次新增 QQ)。
    """
    from pallas.core.foundation.config.bot_admins_cache import invalidate_bot_admins_cache

    repo = make_bot_config_repository()
    _, created = await repo.get_or_create(bot_id, disabled_plugins=[])
    doc = await repo.get(bot_id, ignore_cache=True)
    current = list(doc.admins or []) if doc else []
    merged = list(current)
    added: list[int] = []
    for admin_id in admin_ids:
        if admin_id == bot_id or admin_id in merged:
            continue
        merged.append(admin_id)
        added.append(admin_id)
    if added or created:
        await repo.upsert_field(bot_id, "admins", merged)
        await repo.invalidate_cache()
        await invalidate_bot_admins_cache(bot_id)
    return created, merged, added


def format_add_bot_admin_result(
    *,
    bot_id: int,
    created: bool,
    merged: list[int],
    added: list[int],
) -> str:
    if created and added:
        return (
            f"已为牛牛 {bot_id} 初始化库配置，并添加号主：{', '.join(map(str, added))}。"
            f"当前号主：{', '.join(map(str, merged)) or '（无）'}"
        )
    if created and not added:
        return f"已为牛牛 {bot_id} 初始化库配置；未指定新的号主 QQ。"
    if added:
        return (
            f"已为牛牛 {bot_id} 添加号主：{', '.join(map(str, added))}。"
            f"当前号主：{', '.join(map(str, merged)) or '（无）'}"
        )
    return f"牛牛 {bot_id} 已在库中，指定号主均已在 admins 中。当前号主：{', '.join(map(str, merged)) or '（无）'}"
