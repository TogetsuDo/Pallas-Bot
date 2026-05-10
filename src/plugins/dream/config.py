from nonebot import get_plugin_config
from pydantic import BaseModel, Field


class Config(BaseModel, extra="ignore"):
    # 每个 tick 在队列非空时尝试消费「他群漂流」的概率；降低则更多走历史/已学句/归档，缓解初期语料少时刷屏感
    dream_drift_queue_tick_probability: float = Field(default=0.28, ge=0.0, le=1.0)
    # 在满足发图上限时，尝试发归档画的概率（其余 tick 在走到归档分支时跳过）
    dream_archive_image_probability: float = Field(default=0.26, ge=0.0, le=1.0)
    # 已学句抽样最大重试次数（越大越容易在本 tick 发出一条已学句）
    dream_echo_resample_attempts: int = Field(default=22, ge=1, le=48)
    # 历史梦抽样最大重试次数
    dream_hist_resample_attempts: int = Field(default=12, ge=1, le=48)
    # 梦库定时清理 cron（默认每天 4:00）
    dream_library_cleanup_cron_hour: int = Field(default=4, ge=0, le=23)
    dream_library_cleanup_cron_minute: int = Field(default=0, ge=0, le=59)
    # 删除早于该天数的 is_dream 记录（与历史抽样窗口可独立调）
    dream_message_retention_days: int = Field(default=90, ge=7, le=3650)


plugin_config = get_plugin_config(Config)
