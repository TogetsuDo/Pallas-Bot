"""
简易实现一下入站过滤
"""

from __future__ import annotations

import os
from typing import Any

import httpx
from nonebot import logger

_needles_lower: list[str] | None = None


def reload_inbound_filter_needles() -> None:
    """清空子串缓存，下次读取环境变量（供测试或热重载）。"""
    global _needles_lower
    _needles_lower = None


def _load_needles_lower() -> list[str]:
    global _needles_lower
    if _needles_lower is None:
        raw = os.getenv("PALLAS_INBOUND_FILTER_SUBSTRINGS", "").strip()
        _needles_lower = [p.lower() for p in raw.split(",") if p.strip()]
    return _needles_lower


def is_inbound_substring_filtered(*, plain_text: str, raw_message: str) -> bool:
    needles = _load_needles_lower()
    if not needles:
        return False
    hay_plain = (plain_text or "").lower()
    hay_raw = (raw_message or "").lower()
    return any(n in hay_plain or n in hay_raw for n in needles)


def _api_fail_open() -> bool:
    v = os.getenv("PALLAS_INBOUND_FILTER_API_FAIL_OPEN", "1").strip().lower()
    return v in ("1", "true", "yes", "on", "")


def _api_headers() -> dict[str, str]:
    key = os.getenv("PALLAS_INBOUND_FILTER_API_KEY", "").strip()
    if not key:
        return {}
    return {"Authorization": f"Bearer {key}"}


def _coerce_blocked(body: Any) -> bool | None:
    if not isinstance(body, dict) or "blocked" not in body:
        return None
    v = body.get("blocked")
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return bool(v)
    if isinstance(v, str):
        s = v.strip().lower()
        if s in ("1", "true", "yes", "on"):
            return True
        if s in ("0", "false", "no", "off", ""):
            return False
        return None
    return None


async def is_inbound_group_message_filtered_async(*, plain_text: str, raw_message: str) -> bool:
    if is_inbound_substring_filtered(plain_text=plain_text, raw_message=raw_message):
        return True
    url = os.getenv("PALLAS_INBOUND_FILTER_API_URL", "").strip()
    if not url:
        return False
    try:
        timeout_sec = float(os.getenv("PALLAS_INBOUND_FILTER_API_TIMEOUT_SEC", "2"))
    except ValueError:
        timeout_sec = 2.0
    payload = {"plain_text": plain_text or "", "raw_message": raw_message or ""}
    fail_open = _api_fail_open()
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(timeout_sec), trust_env=True) as client:
            r = await client.post(url, json=payload, headers=_api_headers())
    except Exception as e:
        logger.debug("inbound filter API request failed: {}", e)
        return not fail_open
    if r.status_code != 200:
        logger.debug("inbound filter API non-200: {} {}", r.status_code, r.text[:200] if r.text else "")
        return not fail_open
    try:
        body = r.json()
    except Exception as e:
        logger.debug("inbound filter API JSON parse failed: {}", e)
        return not fail_open
    blocked = _coerce_blocked(body)
    if blocked is None:
        logger.debug('inbound filter API missing or invalid "blocked" bool in body')
        return not fail_open
    return blocked
