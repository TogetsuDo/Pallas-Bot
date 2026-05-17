from unittest.mock import AsyncMock, MagicMock

import pytest

from src.plugins.pallas_image.image_api import (
    image_api_body_issue_label,
    reply_from_image_api_json,
)


def test_image_api_body_issue_label_ok_b64() -> None:
    assert image_api_body_issue_label('{"data":[{"b64_json":"aGVsbG8="}]}') is None


def test_image_api_body_issue_label_upstream_error() -> None:
    body = '{"error":{"message":"quota","type":"new_api_error"}}'
    assert image_api_body_issue_label(body) == "upstream_error"


def test_image_api_body_issue_label_invalid_json() -> None:
    assert image_api_body_issue_label("not-json") == "invalid_json"


def test_image_api_body_issue_label_no_image() -> None:
    assert image_api_body_issue_label('{"data":[]}') == "no_image"


@pytest.mark.asyncio
async def test_reply_finish_on_error_false_on_upstream_error() -> None:
    matcher = MagicMock()
    matcher.finish = AsyncMock()
    matcher.send = AsyncMock()
    body = '{"error":{"message":"quota"}}'
    ok = await reply_from_image_api_json(
        matcher,
        AsyncMock(),
        body,
        finish_on_error=False,
    )
    assert ok is False
    matcher.finish.assert_not_called()
    matcher.send.assert_not_called()


@pytest.mark.asyncio
async def test_reply_finish_on_error_true_on_upstream_error() -> None:
    matcher = MagicMock()
    matcher.finish = AsyncMock()
    body = '{"error":{"message":"quota"}}'
    ok = await reply_from_image_api_json(
        matcher,
        AsyncMock(),
        body,
        finish_on_error=True,
    )
    assert ok is False
    matcher.finish.assert_awaited_once()
