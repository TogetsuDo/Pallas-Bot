"""AI 任务 HTTP 回调执行。"""

from __future__ import annotations

from fastapi import HTTPException, UploadFile
from nonebot import get_bot, logger

from pallas.core.foundation.config import GroupConfig, TaskManager
from pallas.core.foundation.db import SingProgress
from pallas.core.platform.ai_callback.delivery import send_group_image, send_group_message, send_group_voice
from pallas.core.platform.ai_callback.handlers import (
    failure_reply_for_task,
    should_append_llm_session,
    should_suppress_llm_duplicate_reply,
)
from pallas.core.platform.ai_callback.media_task_hooks import (
    invoke_media_task_failure,
    invoke_media_task_success,
)
from pallas.core.platform.ai_callback.task_types import (
    DRAW_IMAGE_TASK_TYPE,
    LLM_CHAT_TASK_TYPE,
    REPEATER_FALLBACK_TASK_TYPE,
    REPEATER_POLISH_LITE_TASK_TYPE,
    REPEATER_POLISH_TASK_TYPE,
    REPEATER_SELECT_TASK_TYPE,
    SING_TASK_TYPES,
)
from pallas.core.platform.shard.coord.ai_task_registry import get_ai_task_record, remove_ai_task
from pallas.product.llm.session_store import append_llm_message, compact_user_llm_history_with_summary
from pallas.product.llm.task_metrics import record_bot_llm_route, record_bot_llm_task

_TRACKED_LLM_TASKS = frozenset({
    LLM_CHAT_TASK_TYPE,
    REPEATER_FALLBACK_TASK_TYPE,
    REPEATER_POLISH_TASK_TYPE,
    REPEATER_POLISH_LITE_TASK_TYPE,
    REPEATER_SELECT_TASK_TYPE,
})


def track_llm_callback(task: dict, event: str) -> None:
    task_type = str(task.get("task_type") or "").strip()
    if task_type in _TRACKED_LLM_TASKS:
        record_bot_llm_task(task_type, event)
        if event == "callback_ok":
            record_bot_llm_route(task_type, str(task.get("llm_route") or ""))


async def resolve_callback_task(task_id: str) -> dict | None:
    task = await TaskManager.get_task(task_id)
    if task:
        return task
    rec = get_ai_task_record(task_id)
    if not rec:
        return None
    return {
        "bot_id": rec.get("bot_id"),
        "group_id": rec.get("group_id"),
        "user_id": rec.get("user_id"),
        "task_type": rec.get("task_type"),
        "fallback_text": rec.get("fallback_text"),
        "candidate_pool": rec.get("candidate_pool"),
        "llm_route": rec.get("llm_route"),
        "last_reply_text": rec.get("last_reply_text"),
    }


async def run_ai_callback(
    task_id: str,
    *,
    status: str,
    text: str | None = None,
    song_id: str | None = None,
    chunk_index: int | None = None,
    key: int | None = None,
    file: UploadFile | None = None,
    history_summary: str | None = None,
    history_keep_messages: int | None = None,
) -> dict[str, str]:
    task = await resolve_callback_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    bot_id = task.get("bot_id")
    group_id = task.get("group_id")

    bot_id_str = str(bot_id).strip() if bot_id is not None else ""
    bot = None
    try:
        bot = get_bot(bot_id_str)
    except Exception as e:
        logger.warning("AI callback get_bot failed task={} bot_id={}: {}", task_id, bot_id_str, e)
    logger.info(
        "AI callback resolved task={} status={} task_type={} bot_id={} group_id={} has_text={} has_file={} song_id={} chunk_index={} key={} history_summary={} history_keep_messages={}",
        task_id,
        status,
        str(task.get("task_type") or "").strip(),
        bot_id_str or "<missing>",
        group_id,
        bool(str(text or "").strip()),
        file is not None,
        song_id,
        chunk_index,
        key,
        bool(history_summary),
        history_keep_messages,
    )

    if group_id and song_id is not None and chunk_index is not None and key is not None and bot is not None:
        config = GroupConfig(group_id)
        sing_progress = SingProgress(
            song_id=str(song_id),
            chunk_index=chunk_index,
            key=key,
        )
        await config.update_sing_progress(sing_progress)

    if status == "failed":
        track_llm_callback(task, "callback_fail")
        invoke_media_task_failure(task)
        await TaskManager.remove_task(task_id)
        remove_ai_task(task_id)
        if bot is not None and group_id:
            fail_msg = failure_reply_for_task(task)
            if fail_msg:
                logger.info(
                    "AI callback sending failure reply task={} bot_id={} group_id={} length={}",
                    task_id,
                    getattr(bot, "self_id", bot_id_str or "<missing>"),
                    group_id,
                    len(fail_msg),
                )
                await send_group_message(bot, group_id, fail_msg)
        return {"message": "ok"}

    if status == "success":
        delivered = bot is not None
        reply_text = str(text or "").strip()
        task_type = str(task.get("task_type") or "").strip()
        if task_type == REPEATER_SELECT_TASK_TYPE:
            from pallas.product.llm.select import resolve_select_callback_text

            pool = task.get("candidate_pool") or []
            fallback = str(task.get("fallback_text") or "").strip()
            reply_text = resolve_select_callback_text(reply_text, pool, fallback)
        elif should_suppress_llm_duplicate_reply(task, reply_text):
            fallback = str(task.get("fallback_text") or "").strip()
            reply_text = fallback if fallback and fallback != reply_text else ""
        if reply_text and group_id and bot is not None:
            logger.info(
                "AI callback delivering text task={} bot_id={} group_id={} length={} task_type={}",
                task_id,
                getattr(bot, "self_id", bot_id_str or "<missing>"),
                group_id,
                len(reply_text),
                task_type,
            )
            delivered = await send_group_message(bot, group_id, reply_text) and delivered
        if should_append_llm_session(task) and reply_text:
            raw_group_id = task.get("group_id")
            scope_group = int(raw_group_id) if raw_group_id is not None else None
            speaker_id = int(task.get("user_id") or 0)
            user_text = str(task.get("user_text") or "").strip()
            if speaker_id:
                if history_summary and history_keep_messages:
                    await compact_user_llm_history_with_summary(
                        int(bot_id),
                        scope_group,
                        speaker_id,
                        history_summary,
                        keep_messages=int(history_keep_messages),
                    )
                if user_text:
                    await append_llm_message(int(bot_id), scope_group, speaker_id, "user", user_text)
                await append_llm_message(int(bot_id), scope_group, speaker_id, "assistant", reply_text)
        track_llm_callback(task, "callback_ok")
        if file and group_id and bot is not None:
            file_bytes = await file.read()
            logger.info(
                "AI callback read file task={} bot_id={} group_id={} task_type={} bytes={} song_id={} chunk_index={} key={}",
                task_id,
                getattr(bot, "self_id", bot_id_str or "<missing>"),
                group_id,
                task_type,
                len(file_bytes),
                song_id,
                chunk_index,
                key,
            )
            if task_type == DRAW_IMAGE_TASK_TYPE:
                at_user = task.get("user_id")
                at_user_id = int(at_user) if at_user is not None else None
                logger.info(
                    "AI callback delivering image task={} bot_id={} group_id={} at_user_id={} bytes={}",
                    task_id,
                    getattr(bot, "self_id", bot_id_str or "<missing>"),
                    group_id,
                    at_user_id,
                    len(file_bytes),
                )
                delivered = (
                    await send_group_image(
                        bot,
                        group_id,
                        file_bytes,
                        at_user_id=at_user_id,
                    )
                    and delivered
                )
                if delivered and file_bytes:
                    invoke_media_task_success(task, image_bytes=file_bytes, group_id=int(group_id))
            elif task_type in SING_TASK_TYPES or (song_id is not None and chunk_index is not None):
                logger.info(
                    "AI callback delivering voice task={} bot_id={} group_id={} task_type={} bytes={} song_id={} chunk_index={} key={}",
                    task_id,
                    getattr(bot, "self_id", bot_id_str or "<missing>"),
                    group_id,
                    task_type,
                    len(file_bytes),
                    song_id,
                    chunk_index,
                    key,
                )
                delivered = await send_group_voice(bot, group_id, file_bytes) and delivered

        await TaskManager.remove_task(task_id)
        remove_ai_task(task_id)
        logger.info(
            "AI callback completed task={} delivered={} bot_id={} group_id={} task_type={}",
            task_id,
            delivered,
            bot_id_str or "<missing>",
            group_id,
            str(task.get("task_type") or "").strip(),
        )
        return {"message": "ok" if delivered else "failed"}

    raise HTTPException(status_code=400, detail="Invalid status")
