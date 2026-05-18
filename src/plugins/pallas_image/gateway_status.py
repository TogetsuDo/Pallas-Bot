from nonebot import on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent

from src.common.cmd_perm import group_message_permission_for_command

from .config import image_gen_config
from .gateway_probe import format_gateway_status_text, probe_all_backends

pallas_gateway = on_command(
    "牛牛网关",
    priority=image_gen_config.min_priority,
    block=True,
    permission=group_message_permission_for_command("pallas_image.gateway"),
)


@pallas_gateway.handle()
async def pallas_gateway_handle(event: GroupMessageEvent) -> None:
    results = await probe_all_backends(image_gen_config)
    if not results:
        await pallas_gateway.finish("牛牛画画：尚未配置可用网关（需 base_url、api_key）")
    await pallas_gateway.finish(format_gateway_status_text(results))
