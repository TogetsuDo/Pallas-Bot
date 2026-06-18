import time

from nonebot import logger, on_message
from nonebot.adapters import Bot, Event
from nonebot.adapters.onebot.v11 import GroupMessageEvent
from nonebot.rule import Rule
from ulid import ULID

from pallas.core.foundation.config import TaskManager
from pallas.core.perm import group_message_permission_for_command
from pallas.core.platform.ai_callback.task_types import LLM_CHAT_TASK_TYPE
from pallas.product.llm import ChatSubmitRequest, get_llm_config, is_llm_chat_service_enabled, submit_chat_task
from pallas.product.llm.chat_queue import merge_queued_chat, stash_chat_during_cooldown
from pallas.product.llm.governance import check_llm_chat_gate, refresh_llm_chat_cooldown
from pallas.product.llm.memory import (
    append_memory_context,
    append_relationship_context,
    extract_at_target,
    parse_memory_teach,
    parse_relationship_teach,
    save_memory_entry,
    save_relationship_note,
)
from pallas.product.llm.persona_context import build_persona_llm_context
from pallas.product.llm.polish_lite import maybe_submit_repeater_corpus_llm
from pallas.product.llm.reply_gate import evaluate_llm_reply_gate
from pallas.product.llm.task_metrics import record_bot_llm_task

from . import startup as _startup  # noqa: F401
from .config import get_llm_chat_config
from .prompts import get_system_prompt
from .replies import (
    LLM_CHAT_BUSY_REPLY,
    LLM_CHAT_FAILED_REPLY,
    LLM_CHAT_MEMORY_SAVED_REPLY,
    LLM_CHAT_RELATIONSHIP_SAVED_REPLY,
    LLM_CHAT_VAGUE_REPLY,
)


def llm_chat_rule(event: Event) -> bool:
    if not is_llm_chat_service_enabled():
        return False
    return bool(getattr(event, "to_me", False))


llm_chat_msg = on_message(
    priority=get_llm_chat_config().llm_chat_min_priority + 1,
    block=False,
    rule=Rule(llm_chat_rule),
    permission=group_message_permission_for_command("llm_chat.chat"),
)


def user_reply_for_submit_failure(status: str) -> str | None:
    if status == "busy":
        return LLM_CHAT_BUSY_REPLY
    if status in {"request_failed", "empty_response", "invalid_response"}:
        return LLM_CHAT_FAILED_REPLY
    return None


@llm_chat_msg.handle()
async def handle_llm_chat(bot: Bot, event: Event):
    if not is_llm_chat_service_enabled():
        return

    cfg = get_llm_chat_config()
    plain = event.get_plaintext().strip()
    if plain.casefold() in ("clear", "unload", "model"):
        return

    session_id = event.get_session_id()
    msg = str(event.get_message()).strip()
    if not msg:
        await llm_chat_msg.send(LLM_CHAT_VAGUE_REPLY)
        return

    llm_cfg = get_llm_config()
    raw_group_id = getattr(event, "group_id", None)
    group_id = int(raw_group_id) if raw_group_id is not None else None
    user_id = int(getattr(event, "user_id", 0) or 0)

    teach_body = parse_memory_teach(plain or msg)
    if teach_body is not None and llm_cfg.llm_memory_rag_enabled:
        saved = await save_memory_entry(int(bot.self_id), group_id, teach_body, cfg=llm_cfg)
        if saved:
            await llm_chat_msg.send(LLM_CHAT_MEMORY_SAVED_REPLY)
            return

    relationship_body = parse_relationship_teach(plain or msg)
    if relationship_body is not None and llm_cfg.llm_relationship_notes_enabled:
        target_id = extract_at_target(msg) or user_id
        saved = await save_relationship_note(int(bot.self_id), group_id, target_id, relationship_body, cfg=llm_cfg)
        if saved:
            await llm_chat_msg.send(LLM_CHAT_RELATIONSHIP_SAVED_REPLY)
            return

    system_prompt = ""
    bundle = None
    try:
        bundle, temperature, token_count = await build_persona_llm_context(
            int(bot.self_id),
            group_id,
            plain or msg,
            mode="normal",
            purpose="chat",
            base_system_path=cfg.llm_chat_system_prompt_path or None,
        )
        system_prompt = bundle.system.strip()
    except Exception:
        logger.exception("compile_persona_prompt failed, falling back to static system prompt")
        temperature = None
        token_count = None

    if not system_prompt:
        system_prompt = get_system_prompt()
    if not system_prompt:
        logger.error("llm chat system prompt file is missing or empty")
        await llm_chat_msg.send(LLM_CHAT_VAGUE_REPLY)
        return

    system_prompt = await append_memory_context(
        system_prompt,
        bot_id=int(bot.self_id),
        group_id=group_id,
        query_text=plain or msg,
        cfg=llm_cfg,
    )

    system_prompt = await append_relationship_context(
        system_prompt,
        bot_id=int(bot.self_id),
        group_id=group_id,
        user_id=user_id,
        cfg=llm_cfg,
    )

    persona_for_gate = None
    if bundle is not None:
        try:
            persona_raw = bundle.metadata.persona
            if isinstance(persona_raw, dict):
                from pallas.product.persona.model import ResolvedPersona

                persona_for_gate = ResolvedPersona(**persona_raw)
        except Exception:
            persona_for_gate = None

    gate_decision = evaluate_llm_reply_gate(plain or msg, cfg=llm_cfg, persona=persona_for_gate)
    if gate_decision == "skip":
        record_bot_llm_task(LLM_CHAT_TASK_TYPE, "reply_gate_skip")
        logger.debug("llm chat reply gate skip group={} user={}", group_id, user_id)
        return

    if llm_cfg.llm_select_enabled and group_id is not None and isinstance(event, GroupMessageEvent):
        from packages.repeater.model import Chat

        chat = Chat(event)
        try:
            bundle = await chat.find_reply_bundle()
        except Exception:
            bundle = None
        if bundle is not None:
            pool = [item for item in bundle.message_pool if item and "[CQ:" not in item]
            candidate = next((item for item in bundle.answer_list if item and "[CQ:" not in item), "")
            if (pool or candidate) and await maybe_submit_repeater_corpus_llm(
                event,
                user_text=plain or msg,
                candidates=pool,
                candidate_text=candidate,
            ):
                gate = await check_llm_chat_gate(event, group_id, cfg=llm_cfg)
                if gate is None:
                    await refresh_llm_chat_cooldown(event, default_cd_sec=llm_cfg.llm_chat_cooldown_sec)
                return

    gate = await check_llm_chat_gate(event, group_id, cfg=llm_cfg)
    if gate is not None:
        if gate == "cooldown" and llm_cfg.llm_chat_queue_merge:
            stash_chat_during_cooldown(int(bot.self_id), group_id, user_id, msg, cfg=llm_cfg)
            record_bot_llm_task(LLM_CHAT_TASK_TYPE, "reply_gate_defer")
            logger.debug("llm chat queued during cooldown group={} user={}", group_id, user_id)
            return
        if gate == "cooldown":
            record_bot_llm_task(LLM_CHAT_TASK_TYPE, "reply_gate_skip")
        logger.debug("llm chat gated: reason={} group={} user={}", gate, group_id, user_id)
        return

    merge_result = merge_queued_chat(int(bot.self_id), group_id, user_id, msg, cfg=llm_cfg)
    msg = merge_result.text
    if merge_result.merged:
        logger.debug("llm chat merged queued message group={} user={}", group_id, user_id)

    request_id = str(ULID())
    await TaskManager.add_task(
        request_id,
        {
            "bot_id": bot.self_id,
            "group_id": getattr(event, "group_id", None),
            "user_id": user_id,
            "task_type": LLM_CHAT_TASK_TYPE,
            "user_text": msg,
            "start_time": time.time(),
        },
    )

    result = await submit_chat_task(
        ChatSubmitRequest(
            request_id=request_id,
            session_id=session_id,
            user_text=msg,
            system_prompt=system_prompt,
            bot_id=int(bot.self_id),
            group_id=group_id,
            user_id=user_id,
            task="llm_chat",
            token_count=token_count,
            temperature=temperature,
        ),
        cfg=llm_cfg,
    )
    if not result.ok:
        await TaskManager.remove_task(request_id)
        record_bot_llm_task(LLM_CHAT_TASK_TYPE, "submit_skip")
        reply = user_reply_for_submit_failure(result.status)
        if reply:
            await llm_chat_msg.send(reply)
        return

    await refresh_llm_chat_cooldown(event, default_cd_sec=llm_cfg.llm_chat_cooldown_sec)
    record_bot_llm_task(LLM_CHAT_TASK_TYPE, "submit_ok")

    if not result.task_id:
        await TaskManager.remove_task(request_id)
