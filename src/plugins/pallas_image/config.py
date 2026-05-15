from __future__ import annotations

import json
import os
from dataclasses import dataclass
from threading import Lock
from typing import Any, Self

from nonebot import get_plugin_config
from pydantic import BaseModel, ConfigDict, Field

from src.common.env_dotenv import merged_repo_dotenv_upper, repo_layered_dotenv_files_exist


class ImageBackendEntry(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    base_url: str = Field(default="", description="备选 API 根 URL。")
    api_key: str = Field(default="", description="备选 API 密钥。")
    model: str = Field(
        default="",
        description="可选模型名；留空则使用主配置 pallas_image_model。",
    )


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
    pallas_image_api_backends: list[ImageBackendEntry] = Field(
        default_factory=list,
        description=(
            "备选 API 列表（JSON 数组）；主配置失败后按顺序尝试。"
            "每项含 base_url、api_key，model 可选（省略则用 pallas_image_model）。"
            '示例：[{"base_url":"https://api2.example.com/v1","api_key":"sk-xxx","model":"gpt-image-2"},'
            '{"base_url":"https://api3.example.com/v1","api_key":"sk-yyy"}]'
        ),
    )
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

    @classmethod
    def from_env(cls) -> Self:
        merged = merged_repo_dotenv_upper()
        data: dict[str, Any] = {}
        for name, field in cls.model_fields.items():
            key = name.upper()
            raw: str | None = None
            if key in os.environ:
                raw = os.environ.get(key)
            elif key in merged:
                raw = merged[key]
            if raw is None:
                continue
            data[name] = parse_pallas_image_env_value(name, str(raw), field.annotation)
        return cls.model_validate(data)


def parse_pallas_image_env_value(name: str, raw: str, ann: Any) -> Any:
    text = raw.strip()
    ann_text = str(ann).lower()
    if "bool" in ann_text:
        return text.lower() in ("1", "true", "yes", "on")
    if "list" in ann_text or "dict" in ann_text:
        if not text:
            return [] if "list" in ann_text else {}
        parsed = json.loads(text)
        if name == "pallas_image_api_backends" and isinstance(parsed, list):
            return [ImageBackendEntry.model_validate(x) for x in parsed if isinstance(x, dict)]
        return parsed
    if "float" in ann_text and "list" not in ann_text:
        return float(text)
    if "int" in ann_text and "list" not in ann_text:
        return int(text)
    return text


@dataclass(frozen=True)
class ImageApiBackend:
    base_url: str
    api_key: str
    model: str
    label: str


_config_lock = Lock()
_cached_pallas_image_config: Config | None = None


def clear_pallas_image_config_cache() -> None:
    global _cached_pallas_image_config
    with _config_lock:
        _cached_pallas_image_config = None


def get_pallas_image_config() -> Config:
    global _cached_pallas_image_config
    with _config_lock:
        if _cached_pallas_image_config is None:
            if repo_layered_dotenv_files_exist():
                _cached_pallas_image_config = Config.from_env()
            else:
                _cached_pallas_image_config = get_plugin_config(Config)
        return _cached_pallas_image_config


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

    def reload(self, c: Config) -> None:
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

    def api_backends(self) -> list[ImageApiBackend]:
        default_model = (self._c.pallas_image_model or "").strip()
        out: list[ImageApiBackend] = []
        primary_url = (self._c.pallas_image_base_url or "").strip()
        primary_key = (self._c.pallas_image_api_key or "").strip()
        if primary_url and primary_key:
            out.append(
                ImageApiBackend(
                    base_url=primary_url,
                    api_key=primary_key,
                    model=default_model,
                    label="primary",
                )
            )
        for i, entry in enumerate(self._c.pallas_image_api_backends):
            url = (entry.base_url or "").strip()
            key = (entry.api_key or "").strip()
            if not url or not key:
                continue
            model = (entry.model or "").strip() or default_model
            out.append(
                ImageApiBackend(
                    base_url=url,
                    api_key=key,
                    model=model,
                    label=f"fallback-{i}",
                )
            )
        return out

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


image_gen_config = ImageGenSettings(get_pallas_image_config())


def reload_image_gen_config() -> None:
    """WebUI 写入 .env 后调用，使牛牛画画配置与并发限制立即生效。"""
    clear_pallas_image_config_cache()
    cfg = get_pallas_image_config()
    image_gen_config.reload(cfg)
    from .runtime_state import sync_image_gen_semaphore

    sync_image_gen_semaphore(cfg.pallas_image_max_concurrency)
