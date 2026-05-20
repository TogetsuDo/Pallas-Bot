from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

# MAA 客户端常见为 32 位十六进制（无连字符）；协议示例亦可能出现标准 UUID
_DEVICE_HEX32_RE = re.compile(r"^[0-9a-fA-F]{32}$")
_DEVICE_UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


def normalize_device_id(raw: str) -> str | None:
    """统一为 32 位小写 hex（去掉 UUID 连字符），便于与 MAA 轮询体对齐。"""
    s = (raw or "").strip()
    if not s:
        return None
    compact = s.lower().replace("-", "")
    if _DEVICE_HEX32_RE.fullmatch(compact):
        return compact
    if _DEVICE_UUID_RE.fullmatch(s.lower()):
        return compact
    return None


def parse_bind_command_args(text: str) -> tuple[str, str]:
    """解析「牛牛绑定MAA <设备标识符> [别名]」，返回 (设备参数, 别名)。"""
    line = (text or "").strip()
    if not line:
        return "", ""
    parts = line.split(maxsplit=1)
    device_part = parts[0].strip()
    alias_part = parts[1].strip() if len(parts) > 1 else ""
    return device_part, alias_part


def bind_device_id_error(raw: str, qq: str) -> str | None:
    """校验绑定参数；通过则返回 None。"""
    text = (raw or "").strip()
    if not text:
        return "用法：牛牛绑定MAA <设备标识符> [别名]\n请复制 MAA「远程控制」中的「设备标识符（只读）」。"
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

STAGE_SETTING_MAX = 4

SETTINGS_STAGE_TYPES = frozenset(f"Settings-Stage{i}" for i in range(1, STAGE_SETTING_MAX + 1))

# 较新 MAA 可能支持；旧版会忽略未知 Settings type
SETTINGS_FIGHT_ENABLE = "Settings-FightEnable"

SETTINGS_TYPES = (
    frozenset({
        "Settings-ConnectionAddress",
        SETTINGS_FIGHT_ENABLE,
    })
    | SETTINGS_STAGE_TYPES
)

COMBAT_PREP_TASK_TYPES = frozenset({"LinkStart-Combat"})

TOOLBOX_TYPES = frozenset({
    "Toolbox-GachaOnce",
    "Toolbox-GachaTenTimes",
})

IMMEDIATE_TYPES = frozenset({
    "CaptureImageNow",
    "StopTask",
    "HeartBeat",
})

# 下发这些 type 时不再自动追加截图任务（CaptureImageNow 已在 IMMEDIATE_TYPES）
TASK_TYPES_WITHOUT_AUTO_SCREENSHOT = IMMEDIATE_TYPES | frozenset({"CaptureImage"})

# 维护者：LinkStart-* 子项（除 WakeUp/完整 LinkStart）不含唤醒；游戏未在主界面时 MAA 易 TaskChainError。
# 牛牛不自动前置 LinkStart-WakeUp。截图/心跳/停止见 IMMEDIATE_TYPES。详见 docs/plugins/maa/README.md「维护者说明」。

# 远程控制协议允许下发的 type（不含 params 的项不得带多余参数）
ALLOWED_REMOTE_TASK_TYPES: frozenset[str] = (
    frozenset({"LinkStart", "CaptureImage"})
    | frozenset(LINK_START_SUBTYPES)
    | SETTINGS_TYPES
    | TOOLBOX_TYPES
    | IMMEDIATE_TYPES
)

MAA_RAW_TASK_PREFIX = "牛牛MAA任务"


@dataclass(frozen=True, slots=True)
class MaaControlCommandHelp:
    phrase: str
    task_type: str
    description: str


# 口令、MAA type、用途说明（COMMAND_TASK_MAP 由此生成，避免与帮助文案脱节）
MAA_CONTROL_COMMAND_HELPS: tuple[MaaControlCommandHelp, ...] = (
    MaaControlCommandHelp(
        "牛牛长草",
        "LinkStart",
        "按 MAA 当前勾选执行完整一键长草（全部子项，依本地配置）。",
    ),
    MaaControlCommandHelp(
        "牛牛唤醒",
        "LinkStart-WakeUp",
        "仅执行一键长草中的「唤醒」子项。",
    ),
    MaaControlCommandHelp(
        "牛牛作战",
        "LinkStart-Combat",
        "仅执行「作战」子项（刷理智关卡，关卡依 MAA 作战配置）。",
    ),
    MaaControlCommandHelp(
        "牛牛公招",
        "LinkStart-Recruiting",
        "仅执行「公招」子项。",
    ),
    MaaControlCommandHelp(
        "牛牛基建",
        "LinkStart-Base",
        "仅执行「基建」子项（含换班、线索、制造等，依 MAA 基建配置）。",
    ),
    MaaControlCommandHelp(
        "牛牛信用商店",
        "LinkStart-Mall",
        "仅执行「信用商店」子项。",
    ),
    MaaControlCommandHelp(
        "牛牛领取奖励",
        "LinkStart-Mission",
        "仅执行「领取报酬」子项（日常/周常奖励等，依 MAA 配置）。",
    ),
    MaaControlCommandHelp(
        "牛牛肉鸽",
        "LinkStart-AutoRoguelike",
        "仅执行「自动肉鸽」子项（集成战略等，依 MAA 配置）。",
    ),
    MaaControlCommandHelp(
        "牛牛盐酸",
        "LinkStart-Reclamation",
        "仅执行「生息演算」子项（盐酸等，依 MAA 配置）。",
    ),
    MaaControlCommandHelp(
        "牛牛截图",
        "CaptureImage",
        "排队截取当前模拟器画面，完成后通过 QQ 回传。",
    ),
    MaaControlCommandHelp(
        "牛牛立刻截图",
        "CaptureImageNow",
        "立即截图（不等待前面排队任务结束）。",
    ),
    MaaControlCommandHelp(
        "牛牛停止",
        "StopTask",
        "请求结束当前正在执行的顺序任务。",
    ),
    MaaControlCommandHelp(
        "牛牛心跳",
        "HeartBeat",
        "查询当前顺序队列正在执行的任务 id（无任务则返回空）。",
    ),
    MaaControlCommandHelp(
        "牛牛单抽",
        "Toolbox-GachaOnce",
        "工具箱：公开招募单抽一次。",
    ),
    MaaControlCommandHelp(
        "牛牛十连",
        "Toolbox-GachaTenTimes",
        "工具箱：公开招募十连。",
    ),
)

COMMAND_TASK_MAP: dict[str, str] = {item.phrase: item.task_type for item in MAA_CONTROL_COMMAND_HELPS}

_MAA_SETTINGS_COMMAND_HELPS: tuple[MaaControlCommandHelp, ...] = (
    MaaControlCommandHelp(
        "牛牛设置连接 <值>",
        "Settings-ConnectionAddress",
        "修改 MAA 连接地址（如模拟器 adb 地址）。",
    ),
    MaaControlCommandHelp(
        "牛牛设置关卡 <关卡…>",
        "Settings-Stage1",
        "设置作战关卡与候选（最多 4 个，空格或逗号分隔；用 - 表示空候选）。",
    ),
)


def format_maa_control_commands_help() -> str:
    """生成「牛牛帮助」中 MAA 远控口令说明（与 COMMAND_TASK_MAP 同步）。"""
    bullet_lines = [f"· {item.phrase}：{item.description}" for item in MAA_CONTROL_COMMAND_HELPS]
    bullet_lines.extend(f"· {item.phrase}：{item.description}" for item in _MAA_SETTINGS_COMMAND_HELPS)
    body = "\n".join(bullet_lines)
    return "\n\n".join([
        "发送下列完整一行口令（须先私聊「牛牛绑定MAA」）。",
        "子项类口令会单独跑对应一键长草模块；"
        "牛牛作战前可自动写入已保存的关卡候选（见「牛牛设置关卡」）。"
        "具体行为以 MAA 本地配置为准：",
        body,
        "协议 type 写法：牛牛MAA任务 <type> [params]（见本插件「MAA 远控（原始 type）」详情）。",
    ])


def format_maa_raw_task_types_help() -> str:
    allowed = "、".join(sorted(ALLOWED_REMOTE_TASK_TYPES))
    return (
        "用法：牛牛MAA任务 <type> [params]。"
        "Settings-* 须带 params；其余 type 勿多余参数。"
        f"可用 type：{allowed}。"
        "示例：牛牛MAA任务 Settings-Stage1 1-7；牛牛MAA任务 LinkStart-Recruiting。"
    )


@dataclass(frozen=True, slots=True)
class MaaTaskSpec:
    task_type: str
    params: str | None = None


def parse_stage_setting_values(raw: str) -> list[str] | None:
    """解析关卡候选，最多 4 项；`-` 表示留空。"""
    text = (raw or "").strip()
    if not text:
        return None
    parts = re.split(r"[,，\s]+", text)
    stages: list[str] = []
    for part in parts:
        if len(stages) >= STAGE_SETTING_MAX:
            break
        token = part.strip()
        if token in ("-", "—", "空"):
            stages.append("")
        elif token:
            stages.append(token)
    if not stages or not any(stages):
        return None
    return stages


def build_stage_setting_specs(stages: list[str]) -> list[MaaTaskSpec]:
    padded = (stages + [""] * STAGE_SETTING_MAX)[:STAGE_SETTING_MAX]
    return [MaaTaskSpec(f"Settings-Stage{i + 1}", stage) for i, stage in enumerate(padded)]


def build_combat_prep_specs(stage_plan: list[str], *, auto_enable_fight: bool) -> list[MaaTaskSpec]:
    """作战前准备：启用作战（若 MAA 支持）并写入关卡候选。"""
    specs: list[MaaTaskSpec] = []
    if auto_enable_fight:
        specs.append(MaaTaskSpec(SETTINGS_FIGHT_ENABLE, "true"))
    if stage_plan:
        specs.extend(build_stage_setting_specs(stage_plan))
    return specs


def expand_command_specs(
    specs: list[MaaTaskSpec],
    *,
    stage_plan: list[str],
    combat_auto_prepare: bool,
) -> list[MaaTaskSpec]:
    if not combat_auto_prepare or not any(s.task_type in COMBAT_PREP_TASK_TYPES for s in specs):
        return specs
    prep = build_combat_prep_specs(stage_plan, auto_enable_fight=True)
    if not prep:
        return specs
    return prep + specs


def build_task_payload(task_id: str, spec: MaaTaskSpec) -> dict[str, Any]:
    payload: dict[str, Any] = {"id": task_id, "type": spec.task_type}
    if spec.params is not None:
        payload["params"] = spec.params
    return payload


def parse_command_line(text: str) -> MaaTaskSpec | None:
    specs = parse_command_specs(text)
    if not specs:
        return None
    return specs[0]


def parse_command_specs(text: str) -> list[MaaTaskSpec] | None:
    """解析「牛牛长草」或「牛牛设置连接 xxx」类口令，可能返回多项（如关卡候选）。"""
    line = (text or "").strip()
    if not line:
        return None

    if line.startswith("牛牛设置连接 "):
        value = line.removeprefix("牛牛设置连接 ").strip()
        if value:
            return [MaaTaskSpec("Settings-ConnectionAddress", value)]
        return None

    if line.startswith("牛牛设置关卡 "):
        stages = parse_stage_setting_values(line.removeprefix("牛牛设置关卡 "))
        if stages:
            return build_stage_setting_specs(stages)
        return None

    task_type = COMMAND_TASK_MAP.get(line)
    if task_type:
        return [MaaTaskSpec(task_type)]
    raw = parse_maa_raw_task(line)
    return [raw] if raw else None


def parse_maa_raw_task(text: str) -> MaaTaskSpec | None:
    """解析「牛牛MAA任务 <type> [params]」。"""
    line = (text or "").strip()
    if not line.startswith(MAA_RAW_TASK_PREFIX):
        return None
    rest = line.removeprefix(MAA_RAW_TASK_PREFIX).strip()
    if not rest:
        return None
    parts = rest.split(maxsplit=1)
    task_type = parts[0]
    params = parts[1].strip() if len(parts) > 1 else None
    if task_type not in ALLOWED_REMOTE_TASK_TYPES:
        return None
    if task_type in SETTINGS_TYPES:
        if not params:
            return None
        return MaaTaskSpec(task_type, params)
    if params:
        return None
    return MaaTaskSpec(task_type)


def maa_raw_task_usage_error() -> str:
    allowed = ", ".join(sorted(ALLOWED_REMOTE_TASK_TYPES))
    return (
        "用法：牛牛MAA任务 <type> [params]\n"
        "示例：牛牛MAA任务 Settings-Stage1 1-7\n"
        "示例：牛牛MAA任务 LinkStart-Recruiting\n"
        f"可用 type：{allowed}"
    )


def maa_raw_task_validate(text: str) -> tuple[MaaTaskSpec | None, str | None]:
    """返回 (spec, error_message)。"""
    line = (text or "").strip()
    if not line.startswith(MAA_RAW_TASK_PREFIX):
        return None, None
    rest = line.removeprefix(MAA_RAW_TASK_PREFIX).strip()
    if not rest:
        return None, maa_raw_task_usage_error()
    parts = rest.split(maxsplit=1)
    task_type = parts[0]
    params = parts[1].strip() if len(parts) > 1 else None
    if task_type not in ALLOWED_REMOTE_TASK_TYPES:
        return None, f"不支持的 type：{task_type}\n{maa_raw_task_usage_error()}"
    if task_type in SETTINGS_TYPES:
        if not params:
            return None, f"{task_type} 需要 params，例如：牛牛MAA任务 {task_type} <值>"
        return MaaTaskSpec(task_type, params), None
    if params:
        return None, f"{task_type} 不需要 params，请去掉「{params}」"
    return MaaTaskSpec(task_type), None
