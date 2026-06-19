"""接话语料未命中时异步智能生成，默认关。"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from nonebot import logger
from ulid import ULID

from pallas.core.foundation.config import TaskManager
from pallas.core.platform.ai_callback.task_types import REPEATER_FALLBACK_TASK_TYPE
from pallas.product.llm.client import submit_chat_task
from pallas.product.llm.config import get_llm_config
from pallas.product.llm.models import ChatSubmitRequest
from pallas.product.llm.task_metrics import record_bot_llm_task
from pallas.product.persona.compile_persona_prompt import load_fallback_lite_system_prompt

if TYPE_CHECKING:
    from nonebot.adapters.onebot.v11 import GroupMessageEvent


async def build_fallback_system_prompt(
    bot_id: int,
    group_id: int,
    plain_text: str,
) -> tuple[str, float | None, int | None]:
    from pallas.product.llm.inference_params import derive_llm_inference_params
    from pallas.product.persona import resolve_persona_for_message

    persona = await resolve_persona_for_message(bot_id, group_id, plain_text)
    temperature, token_count = derive_llm_inference_params(persona, mode="normal", purpose="fallback_lite")
    system_prompt = load_fallback_lite_system_prompt()
    if not system_prompt:
        from pallas.product.llm.persona_context import build_persona_llm_context

        bundle, temperature, token_count = await build_persona_llm_context(
            bot_id,
            group_id,
            plain_text,
            mode="normal",
            purpose="fallback",
        )
        system_prompt = bundle.system.strip()
    return system_prompt, temperature, token_count


async def build_fallback_expression_suffix(group_id: int) -> str:
    from pallas.core.foundation.db import make_group_config_repository
    from pallas.product.persona.expression_habits import build_expression_habits_suffix

    group_config = await make_group_config_repository().get(int(group_id))
    profile = getattr(group_config, "style_profile", None) if group_config is not None else None
    return build_expression_habits_suffix(profile if isinstance(profile, dict) else None)


async def maybe_submit_repeater_llm_fallback(event: GroupMessageEvent, *, user_text: str) -> bool:
    if event.is_tome():
        return False

    cfg = get_llm_config()
    if not cfg.llm_fallback_enabled or not cfg.llm_chat_enabled:
        return False

    text = (user_text or "").strip()
    if not text or "[CQ:" in text:
        return False
    if len(text) > cfg.user_message_max_len:
        text = text[: cfg.user_message_max_len].strip()
    if not text:
        return False

    group_id = int(event.group_id)
    user_id = int(event.user_id)
    bot_id = int(event.self_id)
    session_id = f"repeater_fb_{bot_id}_{group_id}_{user_id}"

    try:
        system_prompt, temperature, token_count = await build_fallback_system_prompt(bot_id, group_id, text)
    except Exception:
        logger.exception("repeater llm fallback compile prompt failed group={}", group_id)
        return False
    if not system_prompt:
        return False
    expression_suffix = await build_fallback_expression_suffix(group_id)
    if expression_suffix:
        system_prompt = f"{system_prompt.rstrip()}\n{expression_suffix}"

    request_id = str(ULID())
    await TaskManager.add_task(
        request_id,
        {
            "bot_id": bot_id,
            "group_id": group_id,
            "user_id": user_id,
            "task_type": REPEATER_FALLBACK_TASK_TYPE,
            "start_time": time.time(),
        },
    )
    result = await submit_chat_task(
        ChatSubmitRequest(
            request_id=request_id,
            session_id=session_id,
            user_text=text,
            system_prompt=system_prompt,
            bot_id=bot_id,
            group_id=group_id,
            user_id=user_id,
            mode="normal",
            task="repeater_fallback",
            token_count=token_count,
            temperature=temperature,
        ),
        cfg=cfg,
    )
    if not result.ok:
        await TaskManager.remove_task(request_id)
        record_bot_llm_task(REPEATER_FALLBACK_TASK_TYPE, "submit_skip")
        logger.debug(
            "repeater llm fallback submit skipped: status={} group={} user={}",
            result.status,
            group_id,
            user_id,
        )
        return False

    record_bot_llm_task(REPEATER_FALLBACK_TASK_TYPE, "submit_ok")
    logger.info(
        "repeater llm fallback queued: request_id={} group={} user={} text_len={}",
        request_id,
        group_id,
        user_id,
        len(text),
    )
    return True
