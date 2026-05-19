from __future__ import annotations

from fastapi import FastAPI  # noqa: TC002
from nonebot import get_app, get_bot, logger, on_command, on_message
from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupMessageEvent,
    Message,
    MessageEvent,
    MessageSegment,
    PrivateMessageEvent,
)
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
from nonebot.rule import Rule
from pydantic import BaseModel, Field

from src.common.cmd_perm import permission_for_command, private_message_permission_for_command

from .config import plugin_config
from .store import MaaStore, NotifyTarget
from .tasks import IMMEDIATE_TYPES, bind_device_id_error, normalize_device_id, parse_command_line

app: FastAPI = get_app()
store = MaaStore()

__plugin_meta__ = PluginMetadata(
    name="MAA 远控",
    description="通过 MAA 远程控制协议绑定设备并下发任务。",
    usage="""
在 MAA「远程控制」中填写用户标识符（你的 QQ 号）与下方 HTTP 端点，保存后私聊：
牛牛绑定MAA <设备标识符>
牛牛长草 / 牛牛公招 / 牛牛截图 等 — 向已绑定设备排队任务
牛牛MAA状态 — 查看绑定与队列
所需权限以「牛牛帮助」本插件功能详情为准（可由 WebUI「命令权限」覆盖）。
协议说明：https://docs.maa.plus/zh-cn/protocol/remote-control-schema.html
    """.strip(),
    type="application",
    homepage="https://github.com/PallasBot/Pallas-Bot",
    supported_adapters={"~onebot.v11"},
    extra={
        "version": "3.0.0",
        "command_permissions": [
            {"id": "maa.bind", "label": "牛牛绑定MAA", "default": "everyone"},
            {"id": "maa.control", "label": "MAA 远控指令", "default": "everyone"},
            {"id": "maa.status", "label": "牛牛MAA状态", "default": "everyone"},
        ],
        "menu_data": [
            {
                "func": "绑定 MAA 设备",
                "trigger_method": "on_cmd",
                "trigger_condition": "牛牛绑定MAA <设备标识符>（私聊）",
                "command_permission": "maa.bind",
                "brief_des": "将 MAA 设备与 QQ 绑定",
                "detail_des": (
                    "MAA 用户标识符须为 QQ 号；设备标识符在 MAA 设置中复制。须先让 MAA 连上牛牛并轮询后再绑定。"
                ),
            },
            {
                "func": "MAA 远控",
                "trigger_method": "on_message",
                "trigger_condition": "牛牛长草/牛牛截图/牛牛公招等",
                "command_permission": "maa.control",
                "brief_des": "向已绑定 MAA 下发任务",
                "detail_des": "支持一键长草及子项、截图、停止、心跳、工具箱抽卡等；详见插件 usage。",
            },
            {
                "func": "MAA 状态",
                "trigger_method": "on_cmd",
                "trigger_condition": "牛牛MAA状态",
                "command_permission": "maa.status",
                "brief_des": "查看绑定设备与待执行任务",
                "detail_des": "展示已绑定设备、当前选用设备及内存中排队任务数。",
            },
            {
                "func": "MAA HTTP",
                "trigger_method": "http",
                "trigger_condition": "POST /maa/getTask、/maa/reportStatus",
                "brief_des": "MAA 轮询与汇报端点",
                "detail_des": "实现 MAA 远程控制协议；路径可在插件配置中修改。",
            },
        ],
    },
)


class GetTaskRequest(BaseModel):
    user: str = ""
    device: str = ""


class GetTaskResponse(BaseModel):
    tasks: list[dict] = Field(default_factory=list)


class ReportStatusRequest(BaseModel):
    user: str = ""
    device: str = ""
    task: str = ""
    status: str = ""
    payload: str = ""


def _normalize_path(path: str) -> str:
    p = (path or "").strip()
    if not p.startswith("/"):
        p = f"/{p}"
    return p


GET_TASK_PATH = _normalize_path(plugin_config.maa_get_task_path)
REPORT_PATH = _normalize_path(plugin_config.maa_report_status_path)


@app.post(GET_TASK_PATH, response_model=GetTaskResponse)
async def maa_get_task(body: GetTaskRequest) -> GetTaskResponse:
    await store.touch_seen(body.user, body.device, plugin_config.maa_seen_ttl_seconds)
    if not await store.is_device_verified(body.user, body.device):
        return GetTaskResponse(tasks=[])
    tasks = await store.pending_tasks_for(body.user, body.device)
    return GetTaskResponse(tasks=tasks)


@app.post(REPORT_PATH)
async def maa_report_status(body: ReportStatusRequest) -> dict[str, str]:
    task = await store.mark_reported(body.task)
    if not task:
        return {"message": "ok"}

    notify = task.notify
    try:
        bot = get_bot(str(notify.bot_id))
    except Exception:
        logger.warning("maa reportStatus: bot {} offline, task={}", notify.bot_id, body.task)
        return {"message": "ok"}

    lines = [f"MAA 任务 {body.task} 已结束：{body.status}"]
    if task.task_type == "HeartBeat":
        running = body.payload or "（当前无顺序任务）"
        lines.append(f"正在执行的任务：{running or '无'}")
    elif task.task_type in {"CaptureImage", "CaptureImageNow"} and body.payload:
        lines.append("截图如下：")
        msg_text = "\n".join(lines)
        segments = [MessageSegment.text(msg_text), MessageSegment.image(f"base64://{body.payload}")]
    else:
        if body.payload:
            lines.append(body.payload[:500])
        segments = [MessageSegment.text("\n".join(lines))]

    try:
        if notify.group_id:
            await bot.send_group_msg(group_id=notify.group_id, message=segments)
        else:
            await bot.send_private_msg(user_id=notify.user_id, message=segments)
    except Exception as exc:
        logger.warning("maa reportStatus notify failed task={}: {}", body.task, exc)
    return {"message": "ok"}


def _notify_from_event(event: MessageEvent, bot: Bot) -> NotifyTarget:
    group_id = event.group_id if isinstance(event, GroupMessageEvent) else None
    return NotifyTarget(bot_id=int(bot.self_id), user_id=int(event.get_user_id()), group_id=group_id)


bind_cmd = on_command(
    "牛牛绑定MAA",
    priority=5,
    block=True,
    permission=private_message_permission_for_command("maa.bind"),
)

status_cmd = on_command(
    "牛牛MAA状态",
    priority=5,
    block=True,
    permission=permission_for_command("maa.status"),
)


async def is_maa_control_msg(event: MessageEvent) -> bool:
    text = event.get_plaintext().strip()
    if text in {"牛牛长草", "牛牛一键长草", "牛牛截图", "牛牛立刻截图", "牛牛停止", "牛牛停止任务", "牛牛心跳"}:
        return True
    if text in {
        "牛牛唤醒",
        "牛牛作战",
        "牛牛公招",
        "牛牛换班",
        "牛牛基建",
        "牛牛信用商店",
        "牛牛信用商店领取",
        "牛牛任务",
        "牛牛肉鸽",
        "牛牛盐酸",
        "牛牛单抽",
        "牛牛十连",
    }:
        return True
    return text.startswith(("牛牛设置连接 ", "牛牛设置关卡 "))


maa_control_msg = on_message(
    Rule(is_maa_control_msg),
    priority=5,
    block=True,
    permission=permission_for_command("maa.control"),
)


@bind_cmd.handle()
async def handle_bind(event: PrivateMessageEvent, args: Message = CommandArg()):  # noqa: B008
    raw_device = args.extract_plain_text().strip()
    qq = str(event.get_user_id())
    fmt_err = bind_device_id_error(raw_device, qq)
    if fmt_err:
        await bind_cmd.finish(fmt_err)
    device = normalize_device_id(raw_device)
    if device is None:
        await bind_cmd.finish(fmt_err or "设备标识符格式不正确。")

    err = await store.bind_device(
        int(event.get_user_id()),
        qq,
        device,
        plugin_config.maa_seen_ttl_seconds,
    )
    if err:
        await bind_cmd.finish(err)
    await bind_cmd.finish(
        f"已绑定设备 {device}。\n"
        f"请在 MAA 中配置：\n"
        f"获取任务：POST {GET_TASK_PATH}\n"
        f"汇报任务：POST {REPORT_PATH}\n"
        f"用户标识符：{event.get_user_id()}"
    )


@status_cmd.handle()
async def handle_status(event: MessageEvent):
    qq = int(event.get_user_id())
    devices = await store.list_devices(qq)
    active = await store.get_active_device(qq)
    verified = [d for d in devices if d.verified]
    if not verified:
        await status_cmd.finish("尚未绑定 MAA 设备。请私聊发送「牛牛绑定MAA <设备标识符>」。")

    lines = ["已绑定设备："]
    for d in verified:
        mark = "（当前）" if d.device == active else ""
        lines.append(f"- {d.device}{mark}")
    pending = await store.pending_count_for_user(qq)
    lines.append(f"待 MAA 拉取任务数：{pending}")
    await status_cmd.finish("\n".join(lines))


@maa_control_msg.handle()
async def handle_control(bot: Bot, event: MessageEvent):
    spec = parse_command_line(event.get_plaintext())
    if not spec:
        return

    notify = _notify_from_event(event, bot)
    attach = plugin_config.maa_attach_screenshot and spec.task_type not in IMMEDIATE_TYPES | {
        "CaptureImage",
        "CaptureImageNow",
    }
    task_ids, err = await store.enqueue(
        int(event.get_user_id()),
        [spec],
        notify,
        attach_screenshot=attach,
    )
    if err:
        await maa_control_msg.finish(err)
    label = spec.task_type
    await maa_control_msg.finish(f"已向 MAA 排队任务 {label}（{len(task_ids)} 项），稍后会推送执行结果。")
