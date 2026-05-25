"""通用配置 WebUI 字段说明：统一为「用途 / 填写 / 说明」三段。"""

from __future__ import annotations


def field_help(purpose: str, how: str, note: str = "") -> str:
    p = purpose.strip().rstrip("。")
    h = how.strip().rstrip("。")
    parts = [f"用途：{p}。", f"填写：{h}。"]
    if note.strip():
        parts.append(f"说明：{note.strip().rstrip('。')}。")
    return "\n".join(parts)
