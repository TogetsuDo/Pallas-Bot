from __future__ import annotations

from nonebot import get_app, get_bot, on_command, on_message
from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupMessageEvent,
    Message,
    MessageEvent,
    PrivateMessageEvent,
)
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
from nonebot.rule import Rule

from src.common.cmd_perm import permission_for_command, private_message_permission_for_command

from .config import get_maa_config
from .endpoints import resolve_maa_http_endpoints
from .http_routes import remount_maa_http_routes
from .store import NotifyTarget, maa_store
from .tasks import (
    COMMAND_TASK_MAP,
    IMMEDIATE_TYPES,
    MAA_RAW_TASK_PREFIX,
    MaaTaskSpec,
    bind_device_id_error,
    format_maa_control_commands_help,
    format_maa_raw_task_types_help,
    maa_raw_task_validate,
    normalize_device_id,
    parse_command_line,
)

app = get_app()
store = maa_store

__plugin_meta__ = PluginMetadata(
    name="MAA 远控",
    description="通过 MAA 远程控制协议绑定设备并下发任务。",
    usage=f"""
1. 绑定（私聊）
牛牛绑定MAA <设备标识符>（MAA「设备标识符（只读）」32 位 hex，不是 QQ 号）
2. MAA 对接地址
发「牛牛帮助 MAA远控」见当前 getTask / reportStatus 完整 URL（由部署配置生成）。
3. 远控口令（群聊或私聊，向已绑定设备排队）
{format_maa_control_commands_help()}
4. 其它
牛牛MAA状态 — 查看绑定设备与待拉取任务数
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
                    "MAA 用户标识符须为 QQ 号；设备标识符在 MAA 设置中复制。"
                    "须先让 MAA 连上牛牛并轮询后再绑定。"
                    "对接 URL 见「牛牛帮助 MAA远控」中的「MAA 对接地址」。"
                ),
            },
            {
                "func": "MAA 远控",
                "trigger_method": "on_message",
                "trigger_condition": "牛牛长草、牛牛公招、牛牛截图等口令",
                "command_permission": "maa.control",
                "brief_des": "向已绑定 MAA 下发任务",
                "detail_des": format_maa_control_commands_help(),
            },
            {
                "func": "MAA 远控（原始 type）",
                "trigger_method": "on_cmd",
                "trigger_condition": "牛牛MAA任务 <type> [params]",
                "command_permission": "maa.control",
                "brief_des": "按协议 type 下发远控任务",
                "detail_des": format_maa_raw_task_types_help(),
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
                "detail_des": (
                    "实现 MAA 远程控制协议。"
                    "完整 URL 见「牛牛帮助 MAA远控」中的「MAA 对接地址」（由 maa_public_base_url 等配置生成）。"
                ),
            },
        ],
    },
)


remount_maa_http_routes(app)


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
    if text in COMMAND_TASK_MAP:
        return True
    return text.startswith(("牛牛设置连接 ", "牛牛设置关卡 "))


maa_control_msg = on_message(
    Rule(is_maa_control_msg),
    priority=5,
    block=True,
    permission=permission_for_command("maa.control"),
)

maa_raw_task_cmd = on_command(
    "牛牛MAA任务",
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
        get_maa_config().maa_seen_ttl_seconds,
    )
    if err:
        await bind_cmd.finish(err)
    ep = resolve_maa_http_endpoints()
    hint = ""
    if ep.inferred_base:
        hint = "\n（地址由本机 host/port 推断，对外请让管理员配置 maa_public_base_url）"
    await bind_cmd.finish(
        f"已绑定设备 {device}。\n"
        f"请在 MAA「远程控制」中配置：\n"
        f"获取任务端点：{ep.get_task_url}\n"
        f"汇报任务端点：{ep.report_status_url}\n"
        f"用户标识符：{event.get_user_id()}{hint}"
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


async def enqueue_and_reply(bot: Bot, event: MessageEvent, spec: MaaTaskSpec, matcher) -> None:
    notify = _notify_from_event(event, bot)
    attach = get_maa_config().maa_attach_screenshot and spec.task_type not in IMMEDIATE_TYPES | {
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
        await matcher.finish(err)
    msg = f"已向 MAA 排队任务 {spec.task_type}"
    if spec.params is not None:
        msg += f"（params={spec.params}）"
    await matcher.finish(f"{msg}（共 {len(task_ids)} 项），稍后会推送执行结果。")


@maa_control_msg.handle()
async def handle_control(bot: Bot, event: MessageEvent):
    spec = parse_command_line(event.get_plaintext())
    if not spec:
        return
    await enqueue_and_reply(bot, event, spec, maa_control_msg)


@maa_raw_task_cmd.handle()
async def handle_raw_task(bot: Bot, event: MessageEvent, args: Message = CommandArg()):  # noqa: B008
    arg_text = args.extract_plain_text().strip()
    line = f"{MAA_RAW_TASK_PREFIX} {arg_text}".strip() if arg_text else MAA_RAW_TASK_PREFIX
    spec, err = maa_raw_task_validate(line)
    if err:
        await maa_raw_task_cmd.finish(err)
    if spec is None:
        await maa_raw_task_cmd.finish("用法：牛牛MAA任务 <type> [params]")
    await enqueue_and_reply(bot, event, spec, maa_raw_task_cmd)
