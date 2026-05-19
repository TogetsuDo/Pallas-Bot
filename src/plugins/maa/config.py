from nonebot import get_plugin_config
from pydantic import BaseModel, Field


class Config(BaseModel):
    maa_get_task_path: str = Field(
        default="/maa/getTask",
        description="MAA 轮询获取任务的 HTTP 路径（POST JSON）。",
    )
    maa_report_status_path: str = Field(
        default="/maa/reportStatus",
        description="MAA 汇报任务结果的 HTTP 路径（POST JSON）。",
    )
    maa_attach_screenshot: bool = Field(
        default=True,
        description="用户下发指令后是否默认再排队一张截图任务。",
    )
    maa_seen_ttl_seconds: int = Field(
        default=86400,
        description="未绑定设备在内存中的保留时长（秒），超时需重新让 MAA 连一次再绑定。",
    )


plugin_config = get_plugin_config(Config)
