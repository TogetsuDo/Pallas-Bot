import asyncio
import random
import re
import time

from nonebot import get_bot, get_driver, logger, on_command, on_message, on_notice, require
from nonebot.adapters import Bot
from nonebot.adapters.onebot.v11 import GroupMessageEvent, GroupRecallNoticeEvent, Message, MessageSegment, permission
from nonebot.exception import ActionFailed
from nonebot.permission import SUPERUSER, Permission
from nonebot.plugin import PluginMetadata
from nonebot.rule import Rule, keyword, to_me
from nonebot.typing import T_State

from src.common.config import BotConfig
from src.common.db.modules import BotConfigModule, GroupConfigModule
from src.common.utils.array2cqcode import try_convert_to_cqcode
from src.common.utils.media_cache import get_image, insert_image

from .config import Config
from .emoji_reaction import reaction_msg
from .model import Chat

plugin_config = Config()

__plugin_meta__ = PluginMetadata(
    name="牛牛复读",
    description="具备智能学习和复读功能的聊天插件，可以学习群内对话并进行智能回复",
    usage="""
这个插件会自动学习群内对话并在适当时候进行回复：
1. 牛牛会自动学习群内对话内容
2. 当群内出现相似话题时，牛牛会自动回复相关内容
3. 当群内有消息被重复发送多次时，牛牛会复读该消息
4. 牛牛会主动参与群聊，根据上下文发表相关言论
5. 管理员功能：
   - 回复某条消息并发送"不可以"可以禁止牛牛回复该内容
   - 发送"不可以发这个"可以禁止牛牛回复你最新回复的消息
   - 管理员撤回牛牛的消息时，会自动将该消息加入禁用列表
    """.strip(),
    type="application",
    homepage="https://github.com/yourname/yourrepo",
    supported_adapters=["~onebot.v11"],
    extra={
        "version": "1.0.0",
        "menu_data": [
            {
                "func": "牛牛复读",
                "trigger_method": "on_message",
                "trigger_condition": "群内对话",
                "brief_des": "自动学习并回复相关内容",
                "detail_des": "牛牛会自动学习群内对话，根据话题相似度、消息重复度等条件智能回复。牛牛会根据上下文理解话题，并在适当时候参与讨论。",
            },
            {
                "func": "复读",
                "trigger_method": "on_message",
                "trigger_condition": "相同消息重复出现",
                "brief_des": "当相同消息重复出现时自动复读",
                "detail_des": "当群内相同消息重复出现达到设定次数（默认3次）时，牛牛会自动复读该消息。",
            },
            {
                "func": "主动发言",
                "trigger_method": "scheduler",
                "trigger_condition": "定时任务",
                "brief_des": "牛牛会主动参与群聊",
                "detail_des": "牛牛会根据学习到的内容，按一定概率主动在群内发言，参与群聊讨论。",
            },
            {
                "func": "不可以",
                "trigger_method": "on_message",
                "trigger_condition": "管理员指令",
                "brief_des": "管理员可以管理牛牛的回复内容",
                "detail_des": "管理员可以通过回复并发送'不可以'、发送'不可以发这个'或撤回牛牛的消息来禁止牛牛回复某些内容。",
            },
        ],
        "menu_template": "default",
    },
)

message_id_lock = asyncio.Lock()
message_id_dict = {}

driver = get_driver()


@driver.on_startup
async def startup():
    await Chat.update_global_blacklist()

    # 从数据库加载全局插件开关状态
    bot_config = await BotConfigModule.find_one({
        "account": list(plugin_config.bots)[0] if hasattr(plugin_config, "bots") and plugin_config.bots else 0
    })
    if bot_config and hasattr(bot_config, "disabled_plugins"):
        plugin_config.enabled = "repeater" not in bot_config.disabled_plugins


@driver.on_shutdown
async def shutdown():
    await Chat.sync()


async def is_shutup(self_id: int, group_id: int) -> bool:
    info = await get_bot(str(self_id)).call_api(
        "get_group_member_info",
        **{
            "user_id": self_id,
            "group_id": group_id,
        },
    )
    flag: bool = info["shut_up_timestamp"] > time.time()

    logger.info(f"bot [{self_id}] in group [{group_id}] is shutup: {flag}")

    return flag


async def post_proc(message: Message, self_id: int, group_id: int) -> Message:
    new_msg = Message()
    for seg in message:
        if seg.type == "at":
            try:
                info = await get_bot(str(self_id)).call_api(
                    "get_group_member_info",
                    **{
                        "user_id": seg.data["qq"],
                        "group_id": group_id,
                    },
                )
            except ActionFailed:  # 群员不存在
                continue
            nick_name = info["card"] or info["nickname"]
            new_msg += f"@{nick_name}"
        elif seg.type == "image":
            cq_code = str(seg)
            base64_data = await get_image(cq_code)
            if base64_data:
                new_msg += MessageSegment.image(file=base64_data)
            else:
                new_msg += seg
        else:
            new_msg += seg

    if not await Chat.reply_post_proc(str(message), str(new_msg), self_id, group_id):
        logger.warning(
            f"bot [{self_id}] post_proc failed in group [{group_id}]: [{str(message)[:30]}] -> [{str(new_msg)[:30]}]"
        )

    return new_msg


any_msg = on_message(
    priority=15,
    block=False,
    permission=permission.GROUP,
)


async def is_plugin_enabled(event: GroupMessageEvent) -> bool:
    """检查插件是否启用"""
    # 首先检查全局配置
    bot_config = await BotConfigModule.find_one({"account": event.self_id})
    if bot_config and hasattr(bot_config, "disabled_plugins"):
        if "repeater" in bot_config.disabled_plugins:
            return False
    elif not plugin_config.enabled:  # 如果没有数据库配置，则使用内存中的配置
        return False

    # 然后检查群配置
    group_config = await GroupConfigModule.find_one({"group_id": event.group_id})
    if group_config and hasattr(group_config, "disabled_plugins"):
        if "repeater" in group_config.disabled_plugins:
            return False

    return True


@any_msg.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    # 检查插件是否启用
    if not await is_plugin_enabled(event):
        return
    to_learn = True
    # 多账号登陆，且在同一群中时；避免一条消息被处理多次
    async with message_id_lock:
        message_id = event.message_id
        group_id = event.group_id
        if group_id in message_id_dict:
            if message_id in message_id_dict[group_id]:
                to_learn = False
        else:
            message_id_dict[group_id] = []

        group_message = message_id_dict[group_id]
        group_message.append(message_id)
        if len(group_message) > 100:
            group_message = group_message[:-10]

    chat: Chat = Chat(event)

    answers = None
    config = BotConfig(event.self_id, event.group_id)
    if await config.is_cooldown("repeat"):
        answers = await chat.answer()

    if to_learn:
        for seg in event.message:
            if seg.type == "image":
                await insert_image(seg)

        await chat.learn()

    if not answers:
        return

    await config.refresh_cooldown("repeat")
    delay = random.randint(2, 5)
    async for item in answers:
        msg = await post_proc(item, event.self_id, event.group_id)
        logger.info(f"bot [{event.self_id}] ready to send [{str(msg)[:30]}] to group [{event.group_id}]")

        await asyncio.sleep(delay)
        await config.refresh_cooldown("repeat")
        try:
            await any_msg.send(msg)
        except ActionFailed:
            if not await BotConfig(event.self_id).security():
                continue

            # 自动删除失效消息。若 bot 处于风控期，请勿开启该功能
            shutup = await is_shutup(event.self_id, event.group_id)
            if not shutup:  # 说明这条消息失效了
                logger.info(f"bot [{event.self_id}] ready to ban [{str(item)}] in group [{event.group_id}]")
                await Chat.ban(event.group_id, event.self_id, str(item), "ActionFailed")
                break
        delay = random.randint(1, 3)


async def is_config_admin(event: GroupMessageEvent) -> bool:
    return await BotConfig(event.self_id).is_admin_of_bot(event.user_id)


IsAdmin = permission.GROUP_OWNER | permission.GROUP_ADMIN | SUPERUSER | Permission(is_config_admin)

# 添加开关命令
repeater_cmd = on_command("牛牛复读", permission=IsAdmin, priority=5, block=True)


@repeater_cmd.handle()
async def handle_repeater_cmd(bot: Bot, event: GroupMessageEvent):
    cmd = event.get_plaintext().strip()

    if "开启" in cmd or "打开" in cmd or "启用" in cmd:
        # 全局开启
        if "全局" in cmd:
            if not await SUPERUSER(bot, event):
                await repeater_cmd.finish("权限不足，只有超级用户才能执行全局操作")
                return

            # 更新内存中的配置
            plugin_config.enabled = True

            # 更新数据库中的配置
            bot_config = await BotConfigModule.find_one({"account": event.self_id})
            if not bot_config:
                bot_config = BotConfigModule(account=event.self_id)

            if not hasattr(bot_config, "disabled_plugins"):
                bot_config.disabled_plugins = []

            if "repeater" in bot_config.disabled_plugins:
                bot_config.disabled_plugins.remove("repeater")
                await bot_config.save()

            await repeater_cmd.finish("已全局开启复读功能")
            return

        # 群聊开启
        group_config = await GroupConfigModule.find_one({"group_id": event.group_id})
        if not group_config:
            group_config = GroupConfigModule(group_id=event.group_id)

        if not hasattr(group_config, "disabled_plugins"):
            group_config.disabled_plugins = []

        if "repeater" in group_config.disabled_plugins:
            group_config.disabled_plugins.remove("repeater")
            await group_config.save()

        await repeater_cmd.finish("已在本群开启复读功能")

    elif "关闭" in cmd or "禁用" in cmd:
        # 全局关闭
        if "全局" in cmd:
            if not await SUPERUSER(bot, event):
                await repeater_cmd.finish("权限不足，只有超级用户才能执行全局操作")
                return

            # 更新内存中的配置
            plugin_config.enabled = False

            # 更新数据库中的配置
            bot_config = await BotConfigModule.find_one({"account": event.self_id})
            if not bot_config:
                bot_config = BotConfigModule(account=event.self_id)

            if not hasattr(bot_config, "disabled_plugins"):
                bot_config.disabled_plugins = []

            if "repeater" not in bot_config.disabled_plugins:
                bot_config.disabled_plugins.append("repeater")
                await bot_config.save()

            await repeater_cmd.finish("已全局关闭复读功能")
            return

        # 群聊关闭
        group_config = await GroupConfigModule.find_one({"group_id": event.group_id})
        if not group_config:
            group_config = GroupConfigModule(group_id=event.group_id)

        if not hasattr(group_config, "disabled_plugins"):
            group_config.disabled_plugins = []

        if "repeater" not in group_config.disabled_plugins:
            group_config.disabled_plugins.append("repeater")
            await group_config.save()

        await repeater_cmd.finish("已在本群关闭复读功能")

    elif "状态" in cmd:
        # 检查全局状态
        bot_config = await BotConfigModule.find_one({"account": event.self_id})
        global_disabled = False
        if bot_config and hasattr(bot_config, "disabled_plugins"):
            global_disabled = "repeater" in bot_config.disabled_plugins

        global_status = "关闭" if global_disabled else "开启"

        # 检查群状态
        group_config = await GroupConfigModule.find_one({"group_id": event.group_id})
        group_disabled = False
        if group_config and hasattr(group_config, "disabled_plugins"):
            group_disabled = "repeater" in group_config.disabled_plugins

        group_status = "关闭" if group_disabled else "开启"

        await repeater_cmd.finish(f"复读功能状态：\n全局：{global_status}\n本群：{group_status}")

    else:
        await repeater_cmd.finish(
            "用法：\n牛牛复读 开启/关闭 - 在本群开启/关闭复读功能\n牛牛复读 全局开启/全局关闭 - 全局开启/关闭复读功能\n牛牛复读 状态 - 查看复读功能状态"
        )


async def is_reply(event: GroupMessageEvent) -> bool:
    return bool(event.reply)


ban_msg = on_message(
    rule=to_me() & keyword("不可以") & Rule(is_reply),
    priority=5,
    block=True,
    permission=IsAdmin,
)


@ban_msg.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if "[CQ:reply," not in try_convert_to_cqcode(event.raw_message):
        return False

    raw_message = ""
    for item in event.reply.message:
        raw_reply = str(item)
        # 去掉图片消息中的 url, subType 等字段
        raw_message += re.sub(r"(\[CQ\:.+)(?:,url=*)(\])", r"\1\2", raw_reply)

    logger.info(f"bot [{event.self_id}] ready to ban [{raw_message}] in group [{event.group_id}]")

    try:
        await bot.delete_msg(message_id=event.reply.message_id)
    except ActionFailed:
        logger.warning(f"bot [{event.self_id}] failed to delete [{raw_message}] in group [{event.group_id}]")

    if await Chat.ban(event.group_id, event.self_id, raw_message, str(event.user_id)):
        await ban_msg.finish("这对角可能会不小心撞倒些家具，我会尽量小心。")


async def is_admin_recall_self_msg(bot: Bot, event: GroupRecallNoticeEvent):
    # 好像不需要这句
    # if event.notice_type != "group_recall":
    #     return False
    self_id = event.self_id
    user_id = event.user_id
    group_id = event.group_id
    operator_id = event.operator_id
    if self_id != user_id:
        return False
    # 如果是自己撤回的就不用管
    if operator_id == self_id:
        return False
    operator_info = await bot.get_group_member_info(group_id=group_id, user_id=operator_id)
    return operator_info["role"] == "owner" or operator_info["role"] == "admin"


ban_recalled_msg = on_notice(
    rule=Rule(is_admin_recall_self_msg),
    priority=5,
    block=True,
)


@ban_recalled_msg.handle()
async def _(bot: Bot, event: GroupRecallNoticeEvent, state: T_State):
    try:
        msg = await bot.get_msg(message_id=event.message_id)
    except ActionFailed:
        logger.warning(f"bot [{event.self_id}] failed to get msg [{event.message_id}]")
        return

    raw_message = ""
    # 使用get_msg得到的消息不是消息序列，使用正则生成一个迭代对象
    for item in re.compile(r"\[[^\]]*\]|\w+").findall(try_convert_to_cqcode(msg["message"])):
        raw_reply = str(item)
        # 去掉图片消息中的 url, subType 等字段
        raw_message += re.sub(r"(\[CQ\:.+)(?:,url=*)(\])", r"\1\2", raw_reply)

    logger.info(f"bot [{event.self_id}] ready to ban [{raw_message}] in group [{event.group_id}]")

    if await Chat.ban(event.group_id, event.self_id, raw_message, str(f"recall by {event.operator_id}")):
        await ban_recalled_msg.finish("这对角可能会不小心撞倒些家具，我会尽量小心。")


async def message_is_ban(bot: Bot, event: GroupMessageEvent, state: T_State) -> bool:
    return event.get_plaintext().strip() == "不可以发这个"


ban_msg_latest = on_message(
    rule=to_me() & Rule(message_is_ban),
    priority=5,
    block=True,
    permission=IsAdmin,
)


@ban_msg_latest.handle()
async def _(bot: Bot, event: GroupMessageEvent, state: T_State):
    logger.info(f"bot [{event.self_id}] ready to ban latest reply in group [{event.group_id}]")

    try:
        await bot.delete_msg(message_id=event.reply.message_id)
    except ActionFailed:
        logger.warning(
            f"bot [{event.self_id}] failed to delete latest reply [{event.raw_message}] in group [{event.group_id}]"
        )

    if await Chat.ban(event.group_id, event.self_id, "", str(event.user_id)):
        await ban_msg_latest.finish("这对角可能会不小心撞倒些家具，我会尽量小心。")


speak_sched = require("nonebot_plugin_apscheduler").scheduler


@speak_sched.scheduled_job("interval", seconds=60)
async def speak_up():
    ret = await Chat.speak()
    if not ret:
        return

    bot_id, group_id, messages, target_id = ret

    for msg in messages:
        logger.info(f"bot [{bot_id}] ready to speak [{msg}] to group [{group_id}]")
        await get_bot(str(bot_id)).call_api(
            "send_group_msg",
            **{
                "message": msg,
                "group_id": group_id,
            },
        )
        if target_id:
            await get_bot(str(bot_id)).call_api(
                "group_poke",
                **{
                    "user_id": target_id,
                    "group_id": group_id,
                },
            )
        await asyncio.sleep(random.randint(2, 5))


update_sched = require("nonebot_plugin_apscheduler").scheduler


@update_sched.scheduled_job("cron", hour="4")
async def update_data():
    await Chat.sync()
    await Chat.clearup_context()
