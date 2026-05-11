from typing import Self

from nonebot import get_plugin_config
from pydantic import BaseModel, Field, model_validator


class Config(BaseModel, extra="ignore"):
    # --- 他群漂流：每轮 worker 是否从「别的群刚丢过来」的队列里取一条 ---
    # 取值 0~1。调高 = 更常发实时漂流；调低 = 更多走下面「历史 / 已学句 / 归档」，语料少时不容易刷同一句。
    dream_drift_queue_tick_probability: float = Field(default=0.8, ge=0.0, le=1.0)

    # --- 归档图：本轮已经还能发图时，有多大机会去抽一张牛牛画画归档 ---
    # 取值 0~1。只影响「走到归档分支」时的尝试概率，不是每条梦话都发图。
    dream_archive_image_probability: float = Field(default=0.5, ge=0.0, le=1.0)

    # --- 兜底文案：从复读已学句里抽一条时，最多重试几次（换一条再试）---
    # 数字越大，越容易在本轮里凑出一条能发的已学句。
    dream_echo_resample_attempts: int = Field(default=22, ge=1, le=48)

    # --- 已学句 vs 历史梦：每一 tick 里谁先被尝试（仅在「本 tick 没发漂流队列内容」之后掷骰）---
    # 取值 0~1。命中：先已学句再 is_dream 历史；未命中：先历史再已学句（与旧版顺序一致）。
    # 调高 = 更易先把复读 Context 里学会的短句当梦话；0 = 永远「历史 → 已学句」；默认 0.2 略偏先已学句。
    dream_prefer_learned_echo_probability: float = Field(default=0.2, ge=0.0, le=1.0)

    # --- 历史梦：从库里 is_dream 记录抽样时，最多重试几次 ---
    # 数字越大，越容易在本轮里换到一条能发的历史（文或图）。
    dream_hist_resample_attempts: int = Field(default=12, ge=1, le=48)

    # --- 发梦话节奏（仅「本群未醉酒」时）：每发完一轮后随机睡多久再发下一轮 ---
    # 单位：秒。会在 [最小, 最大] 之间均匀随机；上限必须 ≥ 下限（见下方校验）。
    dream_worker_sleep_min_sec: float = Field(default=45.0, ge=5.0, le=1200.0)
    dream_worker_sleep_max_sec: float = Field(default=165.0, ge=5.0, le=1200.0)

    # --- 历史梦能抽到多旧：只从最近 N 天内的 is_dream 里抽样；与手动删库脚本的「保留天数」同一口径 ---
    # 至少 7。调大 = 语料池更深；库表会变大，已不再默认按天自动删库。
    dream_message_retention_days: int = Field(default=90, ge=7, le=3650)

    # --- 按「接收群」记住最近发过哪些历史（防短期内同群重复）---
    # 每个群单独记若干条「去重键」（正文一套规则、图片按内容 hash）。填 0 = 不按历史键避让。
    # 进程不重启则一直累计；多场「牛牛做梦」共用本群这一条 LRU。
    dream_history_recent_dedupe_max: int = Field(default=120, ge=0, le=4000)

    # --- 历史抽样更偏向新记录：同一批候选里，时间越新权重相对越高 ---
    # 填 0 = 完全随机；填大 = 更爱抽新来的梦，老句在小库里不容易被反复抽到。
    dream_history_recency_power: float = Field(default=2.25, ge=0.0, le=8.0)

    @model_validator(mode="after")
    def dream_worker_sleep_order(self) -> Self:
        if self.dream_worker_sleep_max_sec < self.dream_worker_sleep_min_sec:
            msg = "dream_worker_sleep_max_sec must be >= dream_worker_sleep_min_sec"
            raise ValueError(msg)
        return self


plugin_config = get_plugin_config(Config)
