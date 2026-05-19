from __future__ import annotations

from dataclasses import dataclass

from nonebot import get_driver

from src.common.web import public_base_url as nonebot_public_base_url

from .config import get_maa_config


def normalize_http_path(path: str) -> str:
    p = (path or "").strip()
    if not p.startswith("/"):
        p = f"/{p}"
    return p


def normalize_public_base_url(raw: str) -> str | None:
    s = (raw or "").strip().rstrip("/")
    if not s:
        return None
    if not s.startswith(("http://", "https://")):
        s = f"http://{s}"
    return s


def normalize_full_endpoint(raw: str) -> str | None:
    s = (raw or "").strip()
    if not s:
        return None
    if not s.startswith(("http://", "https://")):
        s = f"http://{s}"
    return s


@dataclass(frozen=True, slots=True)
class MaaHttpEndpoints:
    get_task_url: str
    report_status_url: str
    inferred_base: bool


def resolve_maa_http_endpoints() -> MaaHttpEndpoints:
    cfg = get_maa_config()
    get_path = normalize_http_path(cfg.maa_get_task_path)
    report_path = normalize_http_path(cfg.maa_report_status_path)

    get_override = normalize_full_endpoint(cfg.maa_get_task_endpoint)
    report_override = normalize_full_endpoint(cfg.maa_report_status_endpoint)
    if get_override and report_override:
        return MaaHttpEndpoints(get_override, report_override, inferred_base=False)

    configured_base = normalize_public_base_url(cfg.maa_public_base_url)
    if configured_base:
        base = configured_base
        inferred = False
    else:
        dconf = get_driver().config
        base = nonebot_public_base_url(host=getattr(dconf, "host", None), port=getattr(dconf, "port", None))
        inferred = True

    if get_override:
        get_url = get_override
    else:
        get_url = f"{base}{get_path}"
    if report_override:
        report_url = report_override
    else:
        report_url = f"{base}{report_path}"
    return MaaHttpEndpoints(get_url, report_url, inferred)


def format_maa_http_setup_help() -> str:
    ep = resolve_maa_http_endpoints()
    lines = [
        "在 MAA「设置 → 远程控制」填写（POST JSON）：",
        f"获取任务端点：{ep.get_task_url}",
        f"汇报任务端点：{ep.report_status_url}",
        "用户标识符：你的 QQ 号（与绑定命令一致）。",
    ]
    if ep.inferred_base:
        lines.append(
            "当前地址由 NoneBot 的 host/port 推断，仅适合本机调试；"
            "对外部署请配置 maa_public_base_url，"
            "或分别配置 maa_get_task_endpoint、maa_report_status_endpoint。"
        )
    return "\n\n".join(lines)
