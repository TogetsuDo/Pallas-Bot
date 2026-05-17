from pydantic import BaseModel, Field


class Config(BaseModel, extra="ignore"):
    request_handler_notify_superusers: bool = Field(
        default=False,
        description="收到好友申请时是否同时通知 SUPERUSER（默认关闭，避免与适配器通知重复）。",
    )
    request_handler_poll_doubt_friends: bool = Field(
        default=True,
        description="是否定时检查「可能被风控拦截」的好友申请，并私聊提醒管理员（约每 4 小时一轮）。",
    )
