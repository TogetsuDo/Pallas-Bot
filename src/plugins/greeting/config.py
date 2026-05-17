from pydantic import BaseModel, Field


class Config(BaseModel, extra="ignore"):
    enable_kick_ban: bool = Field(
        default=True,
        description="牛牛被移出群后，是否自动将其加入黑名单。",
    )
