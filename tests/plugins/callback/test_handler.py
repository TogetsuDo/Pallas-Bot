from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from nonebot.adapters.onebot.v11.exception import NetworkError

from src.plugins.callback import handler as callback_handler


@pytest.mark.asyncio
async def test_run_ai_callback_falls_back_to_shared_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    bot = MagicMock()
    bot.call_api = AsyncMock(return_value=None)
    monkeypatch.setattr(callback_handler, "get_bot", lambda _bot_id: bot)
    monkeypatch.setattr(
        callback_handler.TaskManager,
        "get_task",
        AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        callback_handler,
        "get_ai_task_record",
        lambda _task_id: {"bot_id": "111", "group_id": 222},
    )
    remove_task = AsyncMock()
    monkeypatch.setattr(callback_handler.TaskManager, "remove_task", remove_task)
    monkeypatch.setattr(callback_handler, "remove_ai_task", lambda _task_id: None)

    result = await callback_handler.run_ai_callback("task-1", status="success", text="hello")

    assert result == {"message": "ok"}
    remove_task.assert_awaited_once_with("task-1")


@pytest.mark.asyncio
async def test_run_ai_callback_send_timeout_returns_failed(monkeypatch: pytest.MonkeyPatch) -> None:
    bot = MagicMock()
    bot.call_api = AsyncMock(side_effect=NetworkError("WebSocket call api send_group_msg timeout"))
    monkeypatch.setattr(callback_handler, "get_bot", lambda _bot_id: bot)
    monkeypatch.setattr(
        callback_handler.TaskManager,
        "get_task",
        AsyncMock(return_value={"bot_id": "111", "group_id": 222}),
    )
    remove_task = AsyncMock()
    monkeypatch.setattr(callback_handler.TaskManager, "remove_task", remove_task)
    monkeypatch.setattr(callback_handler, "remove_ai_task", lambda _task_id: None)

    result = await callback_handler.run_ai_callback("task-1", status="success", text="hello")

    assert result == {"message": "failed"}
    remove_task.assert_awaited_once_with("task-1")


@pytest.mark.asyncio
async def test_run_ai_callback_get_bot_failed(monkeypatch: pytest.MonkeyPatch) -> None:
    def raise_get_bot(_bot_id: str):
        raise ValueError("bot not found")

    monkeypatch.setattr(callback_handler, "get_bot", raise_get_bot)
    monkeypatch.setattr(
        callback_handler.TaskManager,
        "get_task",
        AsyncMock(return_value={"bot_id": "111", "group_id": 222}),
    )

    result = await callback_handler.run_ai_callback("task-1", status="success", text="hello")

    assert result == {"message": "failed"}
