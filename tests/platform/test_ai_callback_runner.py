from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from nonebot.adapters.onebot.v11.exception import NetworkError

from pallas.core.platform.ai_callback import runner as ai_callback_runner
from pallas.core.platform.ai_callback.task_types import (
    LLM_CHAT_TASK_TYPE,
    REPEATER_FALLBACK_TASK_TYPE,
    REPEATER_POLISH_TASK_TYPE,
)


@pytest.mark.asyncio
async def test_run_ai_callback_falls_back_to_shared_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    bot = MagicMock()
    bot.call_api = AsyncMock(return_value=None)
    monkeypatch.setattr(ai_callback_runner, "get_bot", lambda _bot_id: bot)
    monkeypatch.setattr(
        ai_callback_runner.TaskManager,
        "get_task",
        AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        ai_callback_runner,
        "get_ai_task_record",
        lambda _task_id: {"bot_id": "111", "group_id": 222},
    )
    remove_task = AsyncMock()
    monkeypatch.setattr(ai_callback_runner.TaskManager, "remove_task", remove_task)
    monkeypatch.setattr(ai_callback_runner, "remove_ai_task", lambda _task_id: None)

    result = await ai_callback_runner.run_ai_callback("task-1", status="success", text="hello")

    assert result == {"message": "ok"}
    remove_task.assert_awaited_once_with("task-1")


@pytest.mark.asyncio
async def test_run_ai_callback_appends_user_and_assistant_on_llm_chat_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bot = MagicMock()
    bot.call_api = AsyncMock(return_value=None)
    monkeypatch.setattr(ai_callback_runner, "get_bot", lambda _bot_id: bot)
    monkeypatch.setattr(
        ai_callback_runner.TaskManager,
        "get_task",
        AsyncMock(
            return_value={
                "bot_id": "111",
                "group_id": 222,
                "user_id": 333,
                "task_type": LLM_CHAT_TASK_TYPE,
                "user_text": "@帕拉斯 银灰是谁",
            }
        ),
    )
    remove_task = AsyncMock()
    monkeypatch.setattr(ai_callback_runner.TaskManager, "remove_task", remove_task)
    monkeypatch.setattr(ai_callback_runner, "remove_ai_task", lambda _task_id: None)

    calls: list[tuple] = []

    async def track_append(bot_id, group_id, user_id, role, content):
        calls.append((bot_id, group_id, user_id, role, content))
        return True

    monkeypatch.setattr(ai_callback_runner, "append_llm_message", track_append)

    result = await ai_callback_runner.run_ai_callback("task-1", status="success", text="银灰是谢拉格领袖")

    assert result == {"message": "ok"}
    assert calls == [
        (111, 222, 333, "user", "@帕拉斯 银灰是谁"),
        (111, 222, 333, "assistant", "银灰是谢拉格领袖"),
    ]


@pytest.mark.asyncio
async def test_run_ai_callback_records_llm_task_metrics(monkeypatch: pytest.MonkeyPatch) -> None:
    from pallas.product.llm.task_metrics import clear_llm_task_metrics_for_tests, llm_task_metrics_snapshot

    clear_llm_task_metrics_for_tests()
    bot = MagicMock()
    bot.call_api = AsyncMock(return_value=None)
    monkeypatch.setattr(ai_callback_runner, "get_bot", lambda _bot_id: bot)
    monkeypatch.setattr(
        ai_callback_runner.TaskManager,
        "get_task",
        AsyncMock(
            return_value={
                "bot_id": "111",
                "group_id": 222,
                "user_id": 333,
                "task_type": REPEATER_POLISH_TASK_TYPE,
            }
        ),
    )
    monkeypatch.setattr(ai_callback_runner.TaskManager, "remove_task", AsyncMock())
    monkeypatch.setattr(ai_callback_runner, "remove_ai_task", lambda _task_id: None)

    await ai_callback_runner.run_ai_callback("task-1", status="success", text="润色后")
    snap = llm_task_metrics_snapshot()
    assert snap["by_task"]["repeater_polish"]["callback_ok"] == 1
    clear_llm_task_metrics_for_tests()


@pytest.mark.asyncio
async def test_run_ai_callback_records_llm_route_metrics(monkeypatch: pytest.MonkeyPatch) -> None:
    from pallas.product.llm.task_metrics import clear_llm_task_metrics_for_tests, llm_task_metrics_snapshot

    clear_llm_task_metrics_for_tests()
    bot = MagicMock()
    bot.call_api = AsyncMock(return_value=None)
    monkeypatch.setattr(ai_callback_runner, "get_bot", lambda _bot_id: bot)
    monkeypatch.setattr(
        ai_callback_runner.TaskManager,
        "get_task",
        AsyncMock(
            return_value={
                "bot_id": "111",
                "group_id": 222,
                "user_id": 333,
                "task_type": LLM_CHAT_TASK_TYPE,
                "llm_route": "corpus_select",
            }
        ),
    )
    monkeypatch.setattr(ai_callback_runner.TaskManager, "remove_task", AsyncMock())
    monkeypatch.setattr(ai_callback_runner, "remove_ai_task", lambda _task_id: None)

    await ai_callback_runner.run_ai_callback("task-route-1", status="success", text="选句结果")
    snap = llm_task_metrics_snapshot()
    assert snap["by_task"]["llm_chat"]["route_counts"] == {"corpus_select": 1}
    clear_llm_task_metrics_for_tests()


@pytest.mark.asyncio
async def test_run_ai_callback_send_timeout_returns_failed(monkeypatch: pytest.MonkeyPatch) -> None:
    bot = MagicMock()
    bot.call_api = AsyncMock(side_effect=NetworkError("WebSocket call api send_group_msg timeout"))
    monkeypatch.setattr(ai_callback_runner, "get_bot", lambda _bot_id: bot)
    monkeypatch.setattr(
        ai_callback_runner.TaskManager,
        "get_task",
        AsyncMock(return_value={"bot_id": "111", "group_id": 222}),
    )
    remove_task = AsyncMock()
    monkeypatch.setattr(ai_callback_runner.TaskManager, "remove_task", remove_task)
    monkeypatch.setattr(ai_callback_runner, "remove_ai_task", lambda _task_id: None)

    result = await ai_callback_runner.run_ai_callback("task-1", status="success", text="hello")

    assert result == {"message": "failed"}
    remove_task.assert_awaited_once_with("task-1")


@pytest.mark.asyncio
async def test_run_ai_callback_llm_chat_duplicate_reply_uses_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    bot = MagicMock()
    bot.call_api = AsyncMock(return_value=None)
    monkeypatch.setattr(ai_callback_runner, "get_bot", lambda _bot_id: bot)
    monkeypatch.setattr(
        ai_callback_runner.TaskManager,
        "get_task",
        AsyncMock(
            return_value={
                "bot_id": "111",
                "group_id": 222,
                "user_id": 333,
                "task_type": LLM_CHAT_TASK_TYPE,
                "fallback_text": "语料候选",
            }
        ),
    )
    remove_task = AsyncMock()
    monkeypatch.setattr(ai_callback_runner.TaskManager, "remove_task", remove_task)
    monkeypatch.setattr(ai_callback_runner, "remove_ai_task", lambda _task_id: None)
    monkeypatch.setattr(
        ai_callback_runner,
        "should_suppress_llm_duplicate_reply",
        lambda task, reply_text: True,
    )

    result = await ai_callback_runner.run_ai_callback("task-dup-1", status="success", text="重复句")

    assert result == {"message": "ok"}
    bot.call_api.assert_awaited_once()
    call_kwargs = bot.call_api.await_args.kwargs
    assert call_kwargs["group_id"] == 222
    assert call_kwargs["message"] == "语料候选"
    remove_task.assert_awaited_once_with("task-dup-1")


@pytest.mark.asyncio
async def test_run_ai_callback_get_bot_failed(monkeypatch: pytest.MonkeyPatch) -> None:
    def raise_get_bot(_bot_id: str):
        raise ValueError("bot not found")

    monkeypatch.setattr(ai_callback_runner, "get_bot", raise_get_bot)
    monkeypatch.setattr(
        ai_callback_runner.TaskManager,
        "get_task",
        AsyncMock(return_value={"bot_id": "111", "group_id": 222}),
    )

    result = await ai_callback_runner.run_ai_callback("task-1", status="success", text="hello")

    assert result == {"message": "failed"}


@pytest.mark.asyncio
async def test_run_ai_callback_repeater_fallback_failed_is_silent(monkeypatch: pytest.MonkeyPatch) -> None:
    bot = MagicMock()
    bot.call_api = AsyncMock(return_value=None)
    monkeypatch.setattr(ai_callback_runner, "get_bot", lambda _bot_id: bot)
    monkeypatch.setattr(
        ai_callback_runner.TaskManager,
        "get_task",
        AsyncMock(
            return_value={
                "bot_id": "111",
                "group_id": 222,
                "task_type": REPEATER_FALLBACK_TASK_TYPE,
            }
        ),
    )
    remove_task = AsyncMock()
    monkeypatch.setattr(ai_callback_runner.TaskManager, "remove_task", remove_task)
    monkeypatch.setattr(ai_callback_runner, "remove_ai_task", lambda _task_id: None)

    result = await ai_callback_runner.run_ai_callback("task-1", status="failed")

    assert result == {"message": "ok"}
    bot.call_api.assert_not_awaited()
    remove_task.assert_awaited_once_with("task-1")


@pytest.mark.asyncio
async def test_run_ai_callback_repeater_polish_failed_uses_fallback_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bot = MagicMock()
    bot.call_api = AsyncMock(return_value=None)
    monkeypatch.setattr(ai_callback_runner, "get_bot", lambda _bot_id: bot)
    monkeypatch.setattr(
        ai_callback_runner.TaskManager,
        "get_task",
        AsyncMock(
            return_value={
                "bot_id": "111",
                "group_id": 222,
                "task_type": REPEATER_POLISH_TASK_TYPE,
                "fallback_text": "语料原文",
            }
        ),
    )
    remove_task = AsyncMock()
    monkeypatch.setattr(ai_callback_runner.TaskManager, "remove_task", remove_task)
    monkeypatch.setattr(ai_callback_runner, "remove_ai_task", lambda _task_id: None)

    result = await ai_callback_runner.run_ai_callback("task-1", status="failed")

    assert result == {"message": "ok"}
    bot.call_api.assert_awaited_once()
    call_kwargs = bot.call_api.await_args.kwargs
    assert call_kwargs["group_id"] == 222
    assert call_kwargs["message"] == "语料原文"
    remove_task.assert_awaited_once_with("task-1")


@pytest.mark.asyncio
async def test_run_ai_callback_repeater_fallback_success_rejected_is_silent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bot = MagicMock()
    bot.call_api = AsyncMock(return_value=None)
    monkeypatch.setattr(ai_callback_runner, "get_bot", lambda _bot_id: bot)
    monkeypatch.setattr(
        ai_callback_runner.TaskManager,
        "get_task",
        AsyncMock(
            return_value={
                "bot_id": "111",
                "group_id": 222,
                "task_type": REPEATER_FALLBACK_TASK_TYPE,
            }
        ),
    )
    monkeypatch.setattr(ai_callback_runner.TaskManager, "remove_task", AsyncMock())
    monkeypatch.setattr(ai_callback_runner, "remove_ai_task", lambda _task_id: None)
    monkeypatch.setattr(
        ai_callback_runner,
        "evaluate_repeater_callback_text",
        AsyncMock(return_value=False),
    )

    result = await ai_callback_runner.run_ai_callback("task-reject-fallback", status="success", text="AI 生成句")

    assert result == {"message": "ok"}
    bot.call_api.assert_not_awaited()


@pytest.mark.asyncio
async def test_run_ai_callback_repeater_polish_success_rejected_uses_fallback_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bot = MagicMock()
    bot.call_api = AsyncMock(return_value=None)
    monkeypatch.setattr(ai_callback_runner, "get_bot", lambda _bot_id: bot)
    monkeypatch.setattr(
        ai_callback_runner.TaskManager,
        "get_task",
        AsyncMock(
            return_value={
                "bot_id": "111",
                "group_id": 222,
                "task_type": REPEATER_POLISH_TASK_TYPE,
                "fallback_text": "语料原文",
            }
        ),
    )
    monkeypatch.setattr(ai_callback_runner.TaskManager, "remove_task", AsyncMock())
    monkeypatch.setattr(ai_callback_runner, "remove_ai_task", lambda _task_id: None)
    monkeypatch.setattr(
        ai_callback_runner,
        "evaluate_repeater_callback_text",
        AsyncMock(side_effect=[False, True]),
    )

    result = await ai_callback_runner.run_ai_callback("task-reject-polish", status="success", text="润色后")

    assert result == {"message": "ok"}
    bot.call_api.assert_awaited_once()
    call_kwargs = bot.call_api.await_args.kwargs
    assert call_kwargs["message"] == "语料原文"


@pytest.mark.asyncio
async def test_run_ai_callback_draw_image_failed_records_runtime_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    import importlib

    pytest.importorskip("pallas_plugin_draw")
    import pallas_plugin_draw.startup  # noqa: F401 — 注册 media task hooks

    from pallas.core.platform.ai_callback.task_types import DRAW_IMAGE_TASK_TYPE

    def draw_submodule(plugin_id: str, submodule: str):
        assert plugin_id == "draw"
        return importlib.import_module(f"pallas_plugin_draw.{submodule}")

    monkeypatch.setattr("pallas.core.platform.plugin_runtime.resolve.import_plugin_submodule", draw_submodule)

    bot = MagicMock()
    bot.call_api = AsyncMock(return_value=None)
    monkeypatch.setattr(ai_callback_runner, "get_bot", lambda _bot_id: bot)
    monkeypatch.setattr(
        ai_callback_runner.TaskManager,
        "get_task",
        AsyncMock(
            return_value={
                "bot_id": "111",
                "group_id": 222,
                "user_id": 333,
                "task_type": DRAW_IMAGE_TASK_TYPE,
            }
        ),
    )
    monkeypatch.setattr(ai_callback_runner.TaskManager, "remove_task", AsyncMock())
    monkeypatch.setattr(ai_callback_runner, "remove_ai_task", lambda _task_id: None)
    record_failure = MagicMock()
    monkeypatch.setattr("pallas_plugin_draw.runtime_state.record_ai_runtime_failure", record_failure)

    result = await ai_callback_runner.run_ai_callback("draw-task-fail", status="failed")

    assert result == {"message": "ok"}
    record_failure.assert_called_once_with("draw_callback_failed")
    bot.call_api.assert_awaited_once()


@pytest.mark.asyncio
async def test_run_ai_callback_draw_image_success(monkeypatch: pytest.MonkeyPatch) -> None:
    import importlib
    from io import BytesIO

    from fastapi import UploadFile

    pytest.importorskip("pallas_plugin_draw")
    import pallas_plugin_draw.startup  # noqa: F401 — 注册 media task hooks

    from pallas.core.platform.ai_callback.task_types import DRAW_IMAGE_TASK_TYPE

    def draw_submodule(plugin_id: str, submodule: str):
        assert plugin_id == "draw"
        return importlib.import_module(f"pallas_plugin_draw.{submodule}")

    monkeypatch.setattr("pallas.core.platform.plugin_runtime.resolve.import_plugin_submodule", draw_submodule)

    bot = MagicMock()
    bot.call_api = AsyncMock(return_value=None)
    monkeypatch.setattr(ai_callback_runner, "get_bot", lambda _bot_id: bot)
    monkeypatch.setattr(
        ai_callback_runner.TaskManager,
        "get_task",
        AsyncMock(
            return_value={
                "bot_id": "111",
                "group_id": 222,
                "user_id": 333,
                "task_type": DRAW_IMAGE_TASK_TYPE,
                "count_usage": True,
            }
        ),
    )
    remove_task = AsyncMock()
    monkeypatch.setattr(ai_callback_runner.TaskManager, "remove_task", remove_task)
    monkeypatch.setattr(ai_callback_runner, "remove_ai_task", lambda _task_id: None)
    bump_usage = MagicMock()
    monkeypatch.setattr("pallas_plugin_draw.draw_usage_store.bump_pallas_draw_usage", bump_usage)
    persist = MagicMock()
    monkeypatch.setattr("pallas_plugin_draw.image_api.schedule_persist_generated_draw", persist)
    record_success = MagicMock()
    monkeypatch.setattr("pallas_plugin_draw.runtime_state.record_ai_runtime_success", record_success)

    png = b"\x89PNG\r\n\x1a\n" + (b"x" * 64)
    upload = UploadFile(filename="draw.png", file=BytesIO(png))

    result = await ai_callback_runner.run_ai_callback("draw-task-1", status="success", file=upload)

    assert result == {"message": "ok"}
    bot.call_api.assert_awaited_once()
    bump_usage.assert_called_once_with((222, 333), True)
    persist.assert_called_once_with(png, 222, 333)
    record_success.assert_called_once()
    remove_task.assert_awaited_once_with("draw-task-1")


@pytest.mark.asyncio
async def test_run_ai_callback_sing_sends_voice_without_progress_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from io import BytesIO

    from fastapi import UploadFile
    from nonebot.adapters.onebot.v11 import MessageSegment

    bot = MagicMock()
    bot.call_api = AsyncMock(return_value=None)
    monkeypatch.setattr(ai_callback_runner, "get_bot", lambda _bot_id: bot)
    monkeypatch.setattr(
        ai_callback_runner.TaskManager,
        "get_task",
        AsyncMock(
            return_value={
                "bot_id": "111",
                "group_id": 222,
                "task_type": "sing",
            }
        ),
    )
    monkeypatch.setattr(ai_callback_runner.TaskManager, "remove_task", AsyncMock())
    monkeypatch.setattr(ai_callback_runner, "remove_ai_task", lambda _task_id: None)

    mp3 = b"ID3" + (b"x" * 64)
    upload = UploadFile(filename="sing.mp3", file=BytesIO(mp3))

    result = await ai_callback_runner.run_ai_callback("sing-task-1", status="success", file=upload)

    assert result == {"message": "ok"}
    bot.call_api.assert_awaited_once()
    call_kwargs = bot.call_api.await_args.kwargs
    assert call_kwargs["group_id"] == 222
    message = call_kwargs["message"]
    assert isinstance(message, MessageSegment)
    assert message.type == "record"


@pytest.mark.asyncio
async def test_run_ai_callback_sing_registry_fallback_uses_registered_bot(monkeypatch: pytest.MonkeyPatch) -> None:
    from io import BytesIO

    from fastapi import UploadFile
    from nonebot.adapters.onebot.v11 import MessageSegment

    bot = MagicMock()
    bot.self_id = "2927116873"
    bot.call_api = AsyncMock(return_value=None)

    def fake_get_bot(bot_id: str):
        assert bot_id == "2927116873"
        return bot

    monkeypatch.setattr(ai_callback_runner, "get_bot", fake_get_bot)
    monkeypatch.setattr(ai_callback_runner.TaskManager, "get_task", AsyncMock(return_value=None))
    monkeypatch.setattr(
        ai_callback_runner,
        "get_ai_task_record",
        lambda _task_id: {
            "bot_id": "2927116873",
            "group_id": 626266902,
            "user_id": 123456789,
            "task_type": "sing",
        },
    )
    monkeypatch.setattr(ai_callback_runner.TaskManager, "remove_task", AsyncMock())
    monkeypatch.setattr(ai_callback_runner, "remove_ai_task", lambda _task_id: None)

    mp3 = b"ID3" + (b"x" * 64)
    upload = UploadFile(filename="sing.mp3", file=BytesIO(mp3))

    result = await ai_callback_runner.run_ai_callback("sing-task-registry", status="success", file=upload)

    assert result == {"message": "ok"}
    bot.call_api.assert_awaited_once()
    call_kwargs = bot.call_api.await_args.kwargs
    assert call_kwargs["group_id"] == 626266902
    message = call_kwargs["message"]
    assert isinstance(message, MessageSegment)
    assert message.type == "record"


@pytest.mark.asyncio
async def test_send_group_voice_uses_message_segment_record() -> None:
    from nonebot.adapters.onebot.v11 import MessageSegment

    from pallas.core.platform.ai_callback.delivery import send_group_voice

    bot = MagicMock()
    bot.call_api = AsyncMock(return_value=None)
    mp3 = b"ID3" + (b"x" * 32)

    ok = await send_group_voice(bot, 626266902, mp3)

    assert ok is True
    bot.call_api.assert_awaited_once()
    call_kwargs = bot.call_api.await_args.kwargs
    message = call_kwargs["message"]
    assert isinstance(message, MessageSegment)
    assert message.type == "record"
