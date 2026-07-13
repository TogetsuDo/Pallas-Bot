# 写第一个插件

对标 NoneBot「创建插件」教程：一步可跑通，再接到权限 / 帮助 / 配置。完整骨架见 [Golden Plugin](golden-plugin.md)；社区规范见 [社区插件作者](/guide/community-plugin-author)。

## 你要达成什么

在 `local/plugins/hello_pallas/` 放一个群口令插件：发「牛牛你好」→ 回复一句；权限、帮助、冷却声明齐全。

## 前置

| 项 | 要求 |
| --- | --- |
| 主仓可跑 | [五分钟跑起来](/guide/quickstart) |
| 目录 | 仓库根下已有或将创建 `local/plugins/` |
| API | 只用 `pallas.api.*` |

`config/pallas.toml`：

```toml
[bootstrap]
extra_plugin_dirs = ["local/plugins"]
```

未配置时，现行主线也会自动扫描 `local/plugins/`；仍建议写上。

## 1. 建目录

```text
local/plugins/hello_pallas/
├── __init__.py
├── handlers.py
└── README.md
```

## 2. `__init__.py`

```python
from nonebot.plugin import PluginMetadata

from pallas.api.commands import bind_alias_handlers, group_command
from pallas.api.limits import command_limit_list, command_limit_row
from pallas.api.metadata import SCENE_GROUP, join_usage, usage_line
from pallas.api.perm import command_perm_list, command_perm_row

from .handlers import handle_hello

__plugin_meta__ = PluginMetadata(
    name="你好牛牛",
    description="示例：群内打招呼。",
    usage=join_usage(usage_line("牛牛你好", "回一句问候。")),
    type="application",
    supported_adapters={"~onebot.v11"},
    extra={
        "command_permissions": command_perm_list(
            command_perm_row("hello_pallas.hello", "牛牛你好", "everyone"),
        ),
        "command_limits": command_limit_list(
            command_limit_row("hello_pallas.hello", 3),
        ),
        "menu_data": [
            {
                "func": "打招呼",
                "trigger_method": "命令",
                "trigger_scene": SCENE_GROUP,
                "trigger_condition": "牛牛你好",
                "brief_des": "回一句问候。",
                "detail_des": "群内发送「牛牛你好」。",
                "command_permission": "hello_pallas.hello",
            },
        ],
        "reload_policy": "config_only",
    },
)

cmd = group_command("hello_pallas.hello", "牛牛你好")
bind_alias_handlers(cmd, handle_hello)
```

## 3. `handlers.py`

```python
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message
from nonebot.matcher import Matcher

from pallas.api.limits import is_command_cooldown_ready, refresh_command_cooldown

COMMAND_ID = "hello_pallas.hello"
CD_SEC = 3


async def handle_hello(matcher: Matcher, event: GroupMessageEvent) -> None:
    if not await is_command_cooldown_ready(event, COMMAND_ID, CD_SEC):
        return
    await refresh_command_cooldown(event, COMMAND_ID, CD_SEC)
    await matcher.finish(Message("你好，这里是 hello_pallas 示例插件。"))
```

## 4. README（最小）

写清：做什么、口令、是否需单独安装、默认权限以 WebUI 为准。

## 5. 加载与验收

1. 重启 Bot（或按站点 activation 策略热载）
2. 群内发 **牛牛你好** → 有回复
3. **牛牛帮助** 能看到本插件，且「何人可用」与声明一致
4. WebUI **命令权限** 矩阵出现 `hello_pallas.hello`

## 常见失败

| 现象 | 原因 |
| --- | --- |
| 无响应 | 未进 `extra_plugin_dirs` / 目录名与包不一致 / 未重启 |
| import 错 | 写了 `pallas.core.*` 或旧 `src.*` |
| 帮助无「何人可用」 | 未绑 `command_permission` 或 ID 不一致 |
| 权限文案写死 | 违反 cmd_perm；改走 metadata |

## 下一步

| 目标 | 文档 |
| --- | --- |
| 配置页 + 热载 | [配置与 WebUI](config-and-webui.md) |
| 正式骨架 | [Golden Plugin](golden-plugin.md) |
| 权限细则 | [cmd_perm](/common/cmd_perm) |
| 独立仓 / PyPI | [发布](publishing.md)、扩展模板 `templates/pallas-plugin-extension/` |
| 社区商店示例 | [pallas-community-plugin-interact](https://github.com/TogetsuDo/pallas-community-plugin-interact) |

## 相关

- [入门](getting-started.md)
- [Cookbook](pallas-api-cookbook.md)
- [测试](testing.md)
