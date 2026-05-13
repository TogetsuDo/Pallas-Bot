from pydantic import BaseModel, Field


class Config(BaseModel, extra="ignore"):
    bots: set[int] = Field(
        default_factory=set,
        description=(
            "当前已连接的本 Bot QQ 号集合，随连接/断开自动维护；"
            "用于识别群内「另一只牛牛」并拦截其消息。一般无需手动填写。"
        ),
    )
