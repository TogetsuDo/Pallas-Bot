from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

# MAA 客户端常见为 32 位十六进制（无连字符）；协议示例亦可能出现标准 UUID
_DEVICE_HEX32_RE = re.compile(r"^[0-9a-fA-F]{32}$")
_DEVICE_UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


def normalize_device_id(raw: str) -> str | None:
    s = (raw or "").strip()
    if not s:
        return None
    if _DEVICE_HEX32_RE.fullmatch(s) or _DEVICE_UUID_RE.fullmatch(s):
        return s.lower()
    return None


def bind_device_id_error(raw: str, qq: str) -> str | None:
    """校验绑定参数；通过则返回 None。"""
    text = (raw or "").strip()
    if not text:
        return "用法：牛牛绑定MAA <设备标识符>\n请复制 MAA「远程控制」中的「设备标识符（只读）」。"
    if text == (qq or "").strip():
        return "你填写的是用户标识符（QQ 号）。请填写 MAA 设置里「设备标识符（只读）」那一项（32 位十六进制）。"
    if normalize_device_id(text) is None:
        return "设备标识符格式不正确，请从 MAA「远程控制」完整复制「设备标识符（只读）」。"
    return None


# 协议支持的 type，见 https://docs.maa.plus/zh-cn/protocol/remote-control-schema.html
LINK_START_SUBTYPES = frozenset({
    "LinkStart-Base",
    "LinkStart-WakeUp",
    "LinkStart-Combat",
    "LinkStart-Recruiting",
    "LinkStart-Mall",
    "LinkStart-Mission",
    "LinkStart-AutoRoguelike",
    "LinkStart-Reclamation",
})

SETTINGS_TYPES = frozenset({
    "Settings-ConnectionAddress",
    "Settings-Stage1",
})

TOOLBOX_TYPES = frozenset({
    "Toolbox-GachaOnce",
    "Toolbox-GachaTenTimes",
})

IMMEDIATE_TYPES = frozenset({
    "CaptureImageNow",
    "StopTask",
    "HeartBeat",
})

# 用户口令 -> MAA type
COMMAND_TASK_MAP: dict[str, str] = {
    "牛牛长草": "LinkStart",
    "牛牛一键长草": "LinkStart",
    "牛牛唤醒": "LinkStart-WakeUp",
    "牛牛作战": "LinkStart-Combat",
    "牛牛公招": "LinkStart-Recruiting",
    "牛牛换班": "LinkStart-Base",
    "牛牛基建": "LinkStart-Base",
    "牛牛信用商店": "LinkStart-Mall",
    "牛牛信用商店领取": "LinkStart-Mall",
    "牛牛任务": "LinkStart-Mission",
    "牛牛肉鸽": "LinkStart-AutoRoguelike",
    "牛牛盐酸": "LinkStart-Reclamation",
    "牛牛截图": "CaptureImage",
    "牛牛立刻截图": "CaptureImageNow",
    "牛牛停止": "StopTask",
    "牛牛停止任务": "StopTask",
    "牛牛心跳": "HeartBeat",
    "牛牛单抽": "Toolbox-GachaOnce",
    "牛牛十连": "Toolbox-GachaTenTimes",
}


@dataclass(frozen=True, slots=True)
class MaaTaskSpec:
    task_type: str
    params: str | None = None


def build_task_payload(task_id: str, spec: MaaTaskSpec) -> dict[str, Any]:
    payload: dict[str, Any] = {"id": task_id, "type": spec.task_type}
    if spec.params is not None:
        payload["params"] = spec.params
    return payload


def parse_command_line(text: str) -> MaaTaskSpec | None:
    """解析「牛牛长草」或「牛牛设置连接 xxx」类口令。"""
    line = (text or "").strip()
    if not line:
        return None

    if line.startswith("牛牛设置连接 "):
        value = line.removeprefix("牛牛设置连接 ").strip()
        if value:
            return MaaTaskSpec("Settings-ConnectionAddress", value)
        return None

    if line.startswith("牛牛设置关卡 "):
        value = line.removeprefix("牛牛设置关卡 ").strip()
        if value:
            return MaaTaskSpec("Settings-Stage1", value)
        return None

    task_type = COMMAND_TASK_MAP.get(line)
    if task_type:
        return MaaTaskSpec(task_type)
    return None
