import time
from collections import Counter

from nonebot import logger, on_message
from nonebot.adapters import Bot, Event
from nonebot.adapters.onebot.v11 import GroupMessageEvent
from nonebot.rule import Rule
from ulid import ULID

from packages.repeater.opportunity_trace import append_conversation_decision_trace
from pallas.core.foundation.config import TaskManager
from pallas.core.foundation.db import make_message_repository
from pallas.core.perm import group_message_permission_for_command
from pallas.core.platform.ai_callback.task_types import LLM_CHAT_TASK_TYPE
from pallas.product.llm import ChatSubmitRequest, get_llm_config, is_llm_chat_service_enabled, submit_chat_task
from pallas.product.llm.behavior import (
    build_behavior_hint_text,
    classify_behavior_scene,
    default_group_chat_behavior_hint,
    select_behavior_patterns,
)
from pallas.product.llm.behavior_store import list_behavior_patterns
from pallas.product.llm.chat_queue import merge_queued_chat, stash_chat_during_cooldown
from pallas.product.llm.governance import check_llm_chat_gate, refresh_llm_chat_cooldown
from pallas.product.llm.kernel import (
    ConversationContext,
    behavior_scene_to_conversation_scene,
    decide_direct_chat_action,
    resolve_conversation_feature_level,
)
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
from pallas.product.llm.reply_variation import (
    build_recent_reply_ending_hint,
    build_recent_reply_variation_hint,
    repeated_assistant_openers,
    should_wait_for_more,
)
from pallas.product.llm.session_store import list_user_llm_messages
from pallas.product.llm.task_metrics import record_bot_llm_task
from pallas.product.llm.tools.registry import tool_metadata_for_chat
from pallas.product.persona.affect_kernel import build_persona_affect_contract, build_variation_hint_from_contract
from pallas.product.persona.corpus_expression_habits import infer_expression_affect_stance

from . import startup as _startup  # noqa: F401
from .config import get_llm_chat_config
from .near_field_scorer import ANSWER_SOURCE as _ANSWER_SOURCE
from .near_field_scorer import RECENT_LIVE_SOURCE as _RECENT_LIVE_SOURCE
from .near_field_scorer import recent_hint_source_label, select_scored_expression_candidates
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


def resolve_corpus_llm_route(llm_cfg, pool: list[str], candidate: str) -> str:
    if llm_cfg.llm_polish_lite_enabled and candidate and pool:
        return "corpus_polish_lite"
    if len(pool) >= 2 and llm_cfg.llm_select_enabled:
        return "corpus_select"
    if candidate and llm_cfg.llm_polish_enabled:
        return "corpus_polish"
    return "corpus_fallback"


async def build_llm_chat_expression_suffix(group_id: int | None) -> str:
    if group_id is None:
        return ""
    from pallas.core.foundation.db import make_group_config_repository
    from pallas.product.persona.expression_habits import build_expression_habits_suffix

    try:
        group_config = await make_group_config_repository().get(int(group_id))
    except Exception:
        return ""
    profile = getattr(group_config, "style_profile", None) if group_config is not None else None
    return build_expression_habits_suffix(profile if isinstance(profile, dict) else None)


def build_llm_chat_ending_hint(turns) -> str:
    return build_recent_reply_ending_hint(turns)


def extract_chat_trigger_keywords(text: str) -> list[str]:
    plain = str(text or "").strip()
    if not plain:
        return []
    try:
        from packages.repeater.model import ChatData
    except Exception:
        return []

    try:
        data = ChatData(
            group_id=0,
            user_id=0,
            raw_message=plain,
            plain_text=plain,
            time=0,
            bot_id=0,
        )
    except Exception:
        return []
    return [item for item in getattr(data, "_keywords_list", []) if item]


async def load_recent_live_expression_rows(
    group_id: int,
    text: str,
    *,
    bot_id: int | None = None,
    current_user_id: int | None = None,
) -> list[dict[str, object]]:
    trigger_keywords = extract_chat_trigger_keywords(text)
    repo = make_message_repository()
    try:
        messages = await repo.find_recent_in_group(int(group_id), before_time=int(time.time()) + 1, limit=32)
    except Exception:
        return []

    user_weights = Counter(int(getattr(msg, "user_id", 0) or 0) for msg in messages)
    user_topic_hits = Counter()
    for msg in messages:
        plain = str(getattr(msg, "plain_text", "") or "").strip()
        if not plain or "[CQ:" in plain:
            continue
        keywords = str(getattr(msg, "keywords", "") or "").strip()
        if trigger_keywords and keywords and not any(keyword in keywords for keyword in trigger_keywords):
            continue
        user_id = int(getattr(msg, "user_id", 0) or 0)
        user_topic_hits[user_id] += 1

    rows: list[dict[str, object]] = []
    for msg in messages:
        plain = str(getattr(msg, "plain_text", "") or "").strip()
        if not plain or "[CQ:" in plain:
            continue
        user_id = int(getattr(msg, "user_id", 0) or 0)
        if current_user_id is not None and user_id == int(current_user_id):
            continue
        bot_msg_id = int(getattr(msg, "bot_id", 0) or 0)
        if bot_id is not None and user_id == int(bot_id):
            continue
        if bot_id is not None and bot_msg_id != 0 and bot_msg_id != int(bot_id):
            continue
        if trigger_keywords:
            keywords = str(getattr(msg, "keywords", "") or "").strip()
            if keywords and not any(keyword in keywords for keyword in trigger_keywords):
                continue
        rows.append({
            "text": plain,
            "count": int(user_weights.get(user_id, 0) or 0),
            "topic_hits": int(user_topic_hits.get(user_id, 0) or 0),
            "keywords": str(getattr(msg, "keywords", "") or "").strip(),
            "time": int(getattr(msg, "time", 0) or 0),
            "user_id": user_id,
            "source": _RECENT_LIVE_SOURCE,
        })
    rows.sort(
        key=lambda item: (
            -int(item.get("topic_hits") or 0),
            -int(item.get("count") or 0),
            -int(item.get("time") or 0),
        )
    )
    return rows


async def build_llm_chat_corpus_ending_hint(
    group_id: int | None,
    text: str = "",
    *,
    bot_id: int | None = None,
    current_user_id: int | None = None,
) -> str:
    if group_id is None:
        return ""
    recent_rows = await load_recent_live_expression_rows(
        int(group_id),
        text,
        bot_id=bot_id,
        current_user_id=current_user_id,
    )
    near_field_rows = list(recent_rows)

    try:
        from pallas.core.foundation.db.context_repo_access import get_shared_context_repository
    except Exception:
        repo = None
    else:
        repo = get_shared_context_repository()

    answer_rows: list[dict[str, object]] = []
    list_answers = getattr(repo, "list_answers_for_group_since", None) if repo is not None else None
    if callable(list_answers):
        try:
            answers = await list_answers(int(group_id), 0)
        except Exception:
            answers = []
        for ans in answers:
            messages = getattr(ans, "messages", None) or []
            sample = str(messages[0] if messages else getattr(ans, "keywords", "") or "").strip()
            answer_rows.append({
                "text": sample,
                "count": int(getattr(ans, "count", 0) or 0),
                "keywords": str(getattr(ans, "keywords", "") or "").strip(),
                "source": _ANSWER_SOURCE,
                "time": int(getattr(ans, "time", 0) or 0),
                "topic_hits": 0,
            })

    trigger_keywords = extract_chat_trigger_keywords(text)
    target_stance = infer_expression_affect_stance(text)
    merged_rows = near_field_rows + answer_rows
    candidates = select_scored_expression_candidates(
        merged_rows,
        target_stance=target_stance,
        trigger_keywords=trigger_keywords,
        query_text=text,
        limit=3,
    )
    if not candidates:
        return ""
    label = recent_hint_source_label(merged_rows, trigger_keywords)
    return "\n【语料收尾参考】" + label + "：" + "、".join(candidates) + "。"


async def latest_llm_assistant_reply(bot_id: int, group_id: int | None, user_id: int) -> str:
    try:
        turns = await list_user_llm_messages(bot_id, group_id, user_id, limit=6)
    except Exception:
        return ""
    for turn in reversed(turns):
        if str(getattr(turn, "role", "")).strip() == "assistant":
            return str(getattr(turn, "content", "") or "").strip()
    return ""


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
        if not plain and not getattr(event, "reply", None):
            return
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
    expression_suffix = await build_llm_chat_expression_suffix(group_id)
    if expression_suffix:
        system_prompt = f"{system_prompt.rstrip()}\n{expression_suffix}"

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
    if should_wait_for_more(plain or msg):
        record_bot_llm_task(LLM_CHAT_TASK_TYPE, "reply_gate_defer")
        logger.debug("llm chat wait-for-more group={} user={}", group_id, user_id)
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
            corpus_fallback = candidate or (pool[0] if pool else "")
            llm_route = resolve_corpus_llm_route(llm_cfg, pool, candidate)
        else:
            corpus_fallback = ""
            llm_route = "plain_llm_chat"
    else:
        corpus_fallback = ""
        llm_route = "plain_llm_chat"

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
    recent_turns = await list_user_llm_messages(int(bot.self_id), group_id, user_id, limit=6)
    variation_hint = build_recent_reply_variation_hint(recent_turns)
    if persona_for_gate is not None:
        affect_contract = build_persona_affect_contract(
            persona_for_gate,
            repeated_openers=repeated_assistant_openers(recent_turns),
        )
        affect_hint = build_variation_hint_from_contract(affect_contract)
        if affect_hint and affect_hint not in variation_hint:
            variation_hint = f"{variation_hint}\n{affect_hint}".strip() if variation_hint else affect_hint
    if variation_hint:
        system_prompt = f"{system_prompt.rstrip()}\n\n{variation_hint}"
    behavior_scene = classify_behavior_scene(
        user_text=plain or msg,
        recent_texts=[str(getattr(turn, "content", "") or "").strip() for turn in recent_turns[-6:]],
        has_multi_party_overlap=isinstance(event, GroupMessageEvent)
        and len({
            int(getattr(turn, "user_id", 0) or 0) for turn in recent_turns[-6:] if int(getattr(turn, "user_id", 0) or 0)
        })
        >= 2,
    )
    conversation_scene = behavior_scene_to_conversation_scene(behavior_scene)
    direct_ctx = ConversationContext.for_direct_chat(
        plain_text=plain or msg,
        group_id=group_id,
        bot_id=int(bot.self_id),
        user_id=user_id,
        scene=conversation_scene,
        recent_texts=[str(getattr(turn, "content", "") or "").strip() for turn in recent_turns[-6:]],
        has_multi_party_overlap=isinstance(event, GroupMessageEvent)
        and len({
            int(getattr(turn, "user_id", 0) or 0) for turn in recent_turns[-6:] if int(getattr(turn, "user_id", 0) or 0)
        })
        >= 2,
    )
    tool_meta = tool_metadata_for_chat(task="llm_chat", user_text=plain or msg)
    direct_decision = decide_direct_chat_action(
        direct_ctx,
        feature_level=resolve_conversation_feature_level(llm_cfg),
        tools_enabled=bool(tool_meta.get("tools_enabled")),
    )
    if group_id is not None:
        append_conversation_decision_trace({
            "group_id": int(group_id),
            "bot_id": int(bot.self_id),
            **direct_decision.trace.to_trace_row(),
        })
    behavior_patterns = select_behavior_patterns(
        scene=behavior_scene,
        group_id=group_id,
        patterns=list_behavior_patterns(),
        limit=2,
    )
    behavior_actions = [item.action for item in behavior_patterns]
    group_behavior_hint = default_group_chat_behavior_hint()
    if group_behavior_hint:
        system_prompt = f"{system_prompt.rstrip()}\n{group_behavior_hint}"
    behavior_hint = build_behavior_hint_text(scene=behavior_scene, actions=behavior_actions)
    if behavior_hint:
        system_prompt = f"{system_prompt.rstrip()}\n{behavior_hint}"
    ending_hint = build_llm_chat_ending_hint(recent_turns)
    if ending_hint:
        system_prompt = f"{system_prompt.rstrip()}{ending_hint}"
    corpus_ending_hint = await build_llm_chat_corpus_ending_hint(
        group_id,
        plain or msg,
        bot_id=int(bot.self_id),
        current_user_id=user_id,
    )
    if corpus_ending_hint:
        system_prompt = f"{system_prompt.rstrip()}{corpus_ending_hint}"
    last_reply_text = await latest_llm_assistant_reply(int(bot.self_id), group_id, user_id)
    await TaskManager.add_task(
        request_id,
        {
            "bot_id": bot.self_id,
            "group_id": getattr(event, "group_id", None),
            "user_id": user_id,
            "task_type": LLM_CHAT_TASK_TYPE,
            "user_text": msg,
            "fallback_text": corpus_fallback,
            "llm_route": llm_route,
            "agent_loop_enabled": bool(tool_meta.get("tools_enabled")),
            "agent_stage_plan": list(direct_decision.agent_stages),
            "tool_schema_count": len(tool_meta.get("tool_schemas") or []),
            "last_reply_text": last_reply_text,
            "variation_hint": variation_hint,
            "variation_applied": bool(variation_hint),
            "behavior_scene": str(behavior_scene),
            "behavior_pattern_ids": [item.pattern_id for item in behavior_patterns],
            "behavior_actions": [str(item.action) for item in behavior_patterns],
            "behavior_hint": behavior_hint,
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
