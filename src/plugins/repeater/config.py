from pydantic import BaseModel, Field


class Config(BaseModel, extra="ignore"):
    answer_threshold: int = Field(
        default=3,
        description="「接话」随机阈值基数；数值越大 Bot 越少插话，越小则更爱接话。",
    )
    answer_threshold_weights: list[int] = Field(
        default=[7, 23, 70],
        description="与接话阈值配合的三段权重（JSON 数组），影响不同档位的接话倾向。",
    )
    topics_size: int = Field(
        default=16,
        description="每个群记住的上下文关键词条数上限，用于联想回复。",
    )
    topics_importance: int = Field(
        default=10000,
        description="命中上下文关键词时对接话权重的额外加成。",
    )
    cross_group_threshold: int = Field(
        default=2,
        description="至少多少个群出现相同短句后，才将其提升为全局可复用语料。",
    )
    repeat_threshold: int = Field(
        default=3,
        description="群内连续相同发言达到该次数时触发复读。",
    )
    repeat_ignore_user_ids: list[int] = Field(
        default_factory=list,
        description="复读判定与学习时忽略的第三方 QQ 号列表。",
    )
    speak_threshold: int = Field(
        default=5,
        description="主动发言的随机阈值；数值越小 Bot 越常主动说话。",
    )
    duplicate_reply: int = Field(
        default=10,
        description="同一条已发送回复在后续多少轮内不再重复选用。",
    )
    split_probability: float = Field(
        default=0.5,
        description="按逗号把一条回复拆成多条发送的概率。",
    )
    drunk_tts_threshold: int = Field(
        default=6,
        description="醉酒状态下，正文超过多少字时改为发语音（TTS）。",
    )
    speak_continuously_probability: float = Field(
        default=0.5,
        description="主动发言后，继续连说下一句的概率。",
    )
    speak_poke_probability: float = Field(
        default=0.6,
        description="主动发言时附带随机戳一戳群友的概率。",
    )
    speak_continuously_max_len: int = Field(
        default=2,
        description="连续主动发言最多连续几句。",
    )
    save_time_threshold: int = Field(
        default=3600,
        description="距上次持久化至少间隔多少秒再写盘（与条数条件为「或」关系）。",
    )
    save_count_threshold: int = Field(
        default=1000,
        description="单群聊天记录在内存中超过多少条触发持久化。",
    )
    save_reserved_size: int = Field(
        default=100,
        description="持久化后每个群在内存中保留的最近消息条数。",
    )
    enable_reaction: bool = Field(default=True, description="是否启用 QQ 表情回应（Reaction）能力。")
    enable_probability_reaction: bool = Field(
        default=True,
        description="日常消息是否按概率随机触发表情回应。",
    )
    reaction_probability: float = Field(
        default=0.1,
        description="日常消息触发表情回应的概率（0~1）。",
    )
    enable_face_reaction: bool = Field(
        default=False,
        description="收到带「小黄脸」表情的消息时是否自动回应。",
    )
    enable_auto_reply_on_reaction: bool = Field(
        default=True,
        description="他人对任意消息发表情回应时，Bot 是否跟着回应。",
    )
    reply_with_same_emoji: bool = Field(
        default=True,
        description="跟表情回应时是否优先使用与对方相同的表情。",
    )
