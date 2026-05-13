from nonebot import get_plugin_config
from pydantic import BaseModel, Field


class Config(BaseModel, extra="ignore"):
    pallas_image_min_priority: int = Field(
        default=5,
        description="「牛牛画画」等指令的插件优先级下限；数值越大越晚处理，便于被其他插件拦截。",
    )
    pallas_image_base_url: str = Field(
        default="",
        description="图像生成 API 的根 URL（如 OpenAI 兼容网关），须含协议且不以 / 结尾以外的路径按厂商要求填写。",
    )
    pallas_image_api_key: str = Field(default="", description="调用图像 API 的密钥或 Token。")
    pallas_image_model: str = Field(default="gpt-image-2", description="默认使用的图像模型名。")
    pallas_image_aspect_ratio: str = Field(
        default="",
        description="画幅比例，如 21:9、16:9、1:1；与 size 二选一填写，皆空则由接口默认。",
    )
    pallas_image_size: str = Field(
        default="",
        description="像素尺寸规格（如 1024x1024）；与 aspect_ratio 二选一，皆空则由接口默认。",
    )
    pallas_image_quality: str = Field(default="auto", description="生成质量档位，取值依上游 API 文档。")
    pallas_image_response_format: str = Field(
        default="b64_json",
        description="期望的返回格式（如 b64_json、url），依上游 API。",
    )
    pallas_image_use_edits_for_reference_images: bool = Field(
        default=True,
        description="带参考图时是否走 edits 接口而非纯文生图。",
    )
    pallas_image_merge_reference_urls_into_prompt: bool = Field(
        default=False,
        description="是否把参考图 URL 合并写进提示词（部分网关需要）。",
    )
    pallas_image_default_edit_prompt: str = Field(
        default="按参考图调整",
        description="编辑/参考图模式未给出文案时使用的默认提示词。",
    )
    pallas_image_request_timeout: float = Field(
        default=180.0,
        gt=10.0,
        le=600.0,
        description="单次图像请求超时时间（秒）。",
    )
    pallas_image_max_concurrency: int = Field(
        default=2,
        ge=1,
        le=16,
        description="全局并发生成请求上限，防止打爆上游或本机。",
    )
    pallas_image_http_transport: str = Field(
        default="auto",
        description="HTTP 客户端实现：auto / httpx / curl 等，参见插件实现说明。",
    )
    pallas_image_tls_impersonate: str = Field(
        default="chrome124",
        description="使用 curl 模拟 TLS 指纹时的浏览器标识（如 chrome124）。",
    )
    pallas_image_http_user_agent: str = Field(
        default="curl/8.5.0",
        description="出站请求 User-Agent，部分 CDN 会校验。",
    )
    pallas_image_draw_group_whitelist: list[int] = Field(
        default_factory=list,
        description="非空时仅允许这些群号使用画画指令；空表示不按群白名单限制。",
    )
    pallas_image_draw_per_user_limit: int = Field(
        default=0,
        ge=0,
        le=1_000_000,
        description="每人每群每日可调用画画次数上限；0 为不限制（按进程自然日）。",
    )
    pallas_image_draw_unlimited_group_ids: list[int] = Field(
        default_factory=list,
        description="不受每人每日次数限制的群号列表。",
    )
    pallas_image_draw_unlimited_user_ids: list[int] = Field(
        default_factory=list,
        description="不受每人每日次数限制的 QQ 号列表。",
    )
    pallas_image_draw_command_cooldown: int = Field(
        default=3,
        ge=0,
        le=3600,
        description="同一用户两次画画指令之间的最短间隔（秒）。",
    )


_raw = get_plugin_config(Config)


class ImageGenSettings:
    __slots__ = ("_c", "_draw_unlimited_groups", "_draw_unlimited_users")

    def __init__(self, c: Config) -> None:
        object.__setattr__(self, "_c", c)
        object.__setattr__(
            self,
            "_draw_unlimited_groups",
            frozenset(c.pallas_image_draw_unlimited_group_ids),
        )
        object.__setattr__(
            self,
            "_draw_unlimited_users",
            frozenset(c.pallas_image_draw_unlimited_user_ids),
        )

    @property
    def min_priority(self) -> int:
        return self._c.pallas_image_min_priority

    @property
    def base_url(self) -> str:
        return self._c.pallas_image_base_url

    @property
    def api_key(self) -> str:
        return self._c.pallas_image_api_key

    @property
    def model(self) -> str:
        return self._c.pallas_image_model

    @property
    def aspect_ratio(self) -> str:
        return self._c.pallas_image_aspect_ratio

    @property
    def size(self) -> str:
        return self._c.pallas_image_size

    @property
    def quality(self) -> str:
        return self._c.pallas_image_quality

    @property
    def response_format(self) -> str:
        return self._c.pallas_image_response_format

    @property
    def use_edits_for_reference_images(self) -> bool:
        return self._c.pallas_image_use_edits_for_reference_images

    @property
    def merge_reference_urls_into_prompt(self) -> bool:
        return self._c.pallas_image_merge_reference_urls_into_prompt

    @property
    def default_edit_prompt(self) -> str:
        return self._c.pallas_image_default_edit_prompt

    @property
    def request_timeout(self) -> float:
        return self._c.pallas_image_request_timeout

    @property
    def max_concurrency(self) -> int:
        return self._c.pallas_image_max_concurrency

    @property
    def http_transport(self) -> str:
        return self._c.pallas_image_http_transport

    @property
    def tls_impersonate(self) -> str:
        return self._c.pallas_image_tls_impersonate

    @property
    def http_user_agent(self) -> str:
        return self._c.pallas_image_http_user_agent

    @property
    def draw_group_whitelist(self) -> list[int]:
        return self._c.pallas_image_draw_group_whitelist

    @property
    def draw_per_user_limit(self) -> int:
        return self._c.pallas_image_draw_per_user_limit

    @property
    def draw_unlimited_group_ids(self) -> list[int]:
        return self._c.pallas_image_draw_unlimited_group_ids

    @property
    def draw_unlimited_user_ids(self) -> list[int]:
        return self._c.pallas_image_draw_unlimited_user_ids

    @property
    def draw_unlimited_group_ids_set(self) -> frozenset[int]:
        return self._draw_unlimited_groups

    @property
    def draw_unlimited_user_ids_set(self) -> frozenset[int]:
        return self._draw_unlimited_users

    @property
    def draw_command_cooldown(self) -> int:
        return self._c.pallas_image_draw_command_cooldown


image_gen_config = ImageGenSettings(_raw)
