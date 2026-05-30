from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message
from nonebot.exception import FinishedException


def _make_event(*, body: str = "牛牛画画", self_id: int = 123) -> GroupMessageEvent:
    return GroupMessageEvent.model_construct(
        time=1,
        self_id=self_id,
        post_type="message",
        message_type="group",
        sub_type="normal",
        user_id=2,
        group_id=1,
        message_id=3,
        message=Message(body),
        raw_message=body,
        reply=None,
    )


@pytest.mark.asyncio
async def test_draw_handle_skips_claim_when_backend_missing(monkeypatch):
    from src.plugins.draw import draw as mod

    called = False

    async def fake_claim(*_args, **_kwargs) -> bool:
        nonlocal called
        called = True
        return True

    async def fake_finish(*_args, **_kwargs):
        raise FinishedException

    monkeypatch.setattr(mod, "draw_group_allowed", lambda _gid: True)
    monkeypatch.setattr(mod, "draw_group_cooldown_ready", AsyncMock(return_value=True))
    monkeypatch.setattr(mod, "active_image_gen_settings", lambda: SimpleNamespace(api_backends=list))
    monkeypatch.setattr(mod, "claim_group_handler", fake_claim)
    monkeypatch.setattr(mod.pallas_draw, "finish", fake_finish)

    with pytest.raises(FinishedException):
        await mod.pallas_draw_handle(SimpleNamespace(self_id="123"), _make_event(), Message(""))

    assert called is False


@pytest.mark.asyncio
async def test_draw_handle_skips_claim_when_prompt_and_refs_empty(monkeypatch):
    from src.plugins.draw import draw as mod
    from src.plugins.draw.config import ImageApiBackend

    called = False

    async def fake_claim(*_args, **_kwargs) -> bool:
        nonlocal called
        called = True
        return True

    async def fake_finish(*_args, **_kwargs):
        raise FinishedException

    backend = ImageApiBackend(
        base_url="https://api.example.com/",
        api_key="sk-test",
        model="m",
        label="primary",
    )

    monkeypatch.setattr(mod, "draw_group_allowed", lambda _gid: True)
    monkeypatch.setattr(mod, "draw_group_cooldown_ready", AsyncMock(return_value=True))
    monkeypatch.setattr(mod, "active_image_gen_settings", lambda: SimpleNamespace(api_backends=lambda: [backend]))
    monkeypatch.setattr(mod, "draw_should_count_usage", lambda *_args, **_kwargs: False)
    monkeypatch.setattr(mod, "SUPERUSER", AsyncMock(return_value=False))
    monkeypatch.setattr(mod, "claim_group_handler", fake_claim)
    monkeypatch.setattr(mod.pallas_draw, "finish", fake_finish)

    with pytest.raises(FinishedException):
        await mod.pallas_draw_handle(SimpleNamespace(self_id="123"), _make_event(), Message(""))

    assert called is False
