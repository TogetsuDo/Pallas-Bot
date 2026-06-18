"""AI 回调结果投递到 QQ 群。"""

from __future__ import annotations

from nonebot import logger
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot.adapters.onebot.v11.exception import NetworkError
from nonebot.exception import ActionFailed

_CALLBACK_SEND_ERRORS = (ActionFailed, NetworkError)


async def send_group_message(bot, group_id: int, message: str) -> bool:
    try:
        await bot.call_api(
            "send_group_msg",
            **{
                "message": message,
                "group_id": group_id,
            },
        )
        return True
    except _CALLBACK_SEND_ERRORS as e:
        logger.warning("AI callback send_group_msg failed group={}: {}", group_id, e)
        return False


async def send_group_image(bot, group_id: int, image_bytes: bytes, *, at_user_id: int | None = None) -> bool:
    from pallas.core.platform.plugin_runtime.resolve import import_plugin_submodule

    image_api = import_plugin_submodule("draw", "image_api")
    if not image_bytes:
        return False
    if not image_api.is_valid_generated_image(image_bytes):
        logger.warning(
            "AI callback draw image rejected group={} len={}",
            group_id,
            len(image_bytes),
        )
        return False
    message = image_api.optional_message_at_user(at_user_id, MessageSegment.image(image_bytes))
    try:
        await bot.call_api(
            "send_group_msg",
            **{
                "message": message,
                "group_id": group_id,
            },
        )
        return True
    except _CALLBACK_SEND_ERRORS as e:
        logger.warning("AI callback send_group image failed group={}: {}", group_id, e)
        return False


async def send_group_voice(bot, group_id: int, audio_bytes: bytes) -> bool:
    if not audio_bytes:
        return False
    try:
        await bot.call_api(
            "send_group_msg",
            **{
                "message": MessageSegment.record(file=audio_bytes),
                "group_id": group_id,
            },
        )
        return True
    except _CALLBACK_SEND_ERRORS as e:
        logger.warning("AI callback send voice failed group={}: {}", group_id, e)
        return False
