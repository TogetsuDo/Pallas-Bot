from __future__ import annotations

import time
from typing import Any

from pallas.core.shared.utils import HTTPXClient

_MEDIA_TASK_ENDPOINT = "/api/media/tasks"


async def submit_sing_media_task(
    *,
    base_url: str,
    request_id: str,
    bot_id: int,
    group_id: int,
    user_id: int,
    speaker: str,
    song_id: int,
    sing_length: int,
    chunk_index: int,
    key: int,
) -> tuple[bool, str, str]:
    url = base_url.rstrip("/") + _MEDIA_TASK_ENDPOINT
    payload: dict[str, Any] = {
        "request_id": request_id,
        "capability": "media.sing",
        "caller": {
            "source": "bot",
            "bot_id": bot_id,
            "plugin": "sing",
        },
        "context": {
            "group_id": group_id,
            "user_id": user_id,
            "metadata": {
                "submitted_at": int(time.time()),
            },
        },
        "policy": {
            "mode": "default",
            "timeout_sec": float(max(sing_length, 60)),
            "allow_fallback": False,
            "prefer_local": False,
            "force_task_mode": True,
        },
        "payload": {
            "speaker": speaker,
            "song_id": song_id,
            "key": key,
            "chunk_index": chunk_index,
            "sing_length": sing_length,
        },
    }
    response = await HTTPXClient.post(url, json=payload)
    if not response:
        return False, "", "媒体任务提交失败"
    try:
        body = response.json()
    except ValueError:
        return False, "", "媒体任务响应无效"
    if str(body.get("result_state") or "").strip().lower() != "accepted":
        err = body.get("error") if isinstance(body, dict) else None
        message = "媒体任务被拒绝"
        if isinstance(err, dict):
            message = str(err.get("message") or message)
        return False, "", message
    task_id = str(body.get("task_id") or "").strip()
    if not task_id:
        return False, "", "媒体任务缺少 task_id"
    return True, task_id, ""
