# Golden Plugin

Golden Plugin 不是“看起来整洁”的目录模板，而是 4.0 下插件结构、元数据、配置、帮助、治理接入方式的一套默认答案。

要新增 core 插件，或者把一个老插件整理回 4.0 主线风格，先按这页来。

## 目标

Golden Plugin 解决四个问题：

1. 入口文件不能继续膨胀成超大 `__init__.py`
2. 插件元数据、命令权限、帮助文案需要统一表达
3. 配置、热重载、存储、测试要走统一入口
4. core 插件与普通社区插件要共享尽可能一致的骨架

## 推荐目录

```text
packages/<name>/
├── __init__.py
├── config.py
├── handlers.py
├── startup.py
└── ...
```

最小职责如下：

| 文件 | 责任 |
| --- | --- |
| `__init__.py` | `PluginMetadata`、matcher 注册、薄入口 |
| `config.py` | Pydantic 配置、WebUI 热重载接入 |
| `handlers.py` | 口令 handler、被动消息 handler |
| `startup.py` | 启动钩子、HTTP 路由注册、仅在确实需要时存在 |

## `__init__.py` 应该长什么样

合格的 `__init__.py` 以“声明”为主，而不是以“实现”为主。

通常包含：

- `PluginMetadata`
- `extra["command_permissions"]`
- `extra["command_limits"]`
- `extra["menu_data"]`
- 必要的 matcher 注册

通常不该包含：

- 大段业务逻辑
- 复杂持久化实现
- 启动期长逻辑
- 大段 HTTP 路由细节

对 core 插件，`__init__.py` 目标是薄，最好控制在约 120 行量级。

## 命令型插件的默认写法

优先使用 `plugin_sdk` / `pallas.api.commands` 体系，别让每个插件自己拼 matcher、权限、帮助元数据。

理想状态下，一条命令会同时具备：

- 明确的 `command_id`
- 对应的 `command_permission`
- 对应的 `menu_data`
- 必要时对应的 `command_limit`

这样 WebUI、帮助系统、权限治理和测试都更容易保持一致。

## 配置与热重载

有插件页配置时，默认做法是：

1. 在 `config.py` 定义 Pydantic 模型
2. 使用 `install_hot_reload_config`
3. 业务代码通过 `get_config()` 获取当前值

::: warning 别缓存配置快照
不要在模块 import 时缓存配置快照，然后期待 WebUI 保存后自动同步。那样热重载会失效。
:::

## 维护者向插件与普通群口令插件的区别

不是所有插件都要有群口令。

对 `pb_webui`、`pb_protocol`、`pb_stats` 这类维护者向插件：

- 可以没有群口令
- `help_audience` 应偏向 `maintainer`
- 说明重点放在 WebUI 页面、运维用途、配置段，而不是聊天口令

对普通群口令插件：

- 以 `handlers.py` 和 `menu_data` 为中心
- 权限、冷却、帮助说明要齐全

## 存储与路径

Golden Plugin 也约束数据该怎么放：

- 结构化状态优先用声明式 `plugin_storage`
- 大文件、缓存、导出文件再用 `plugin_data_dir`
- 不要在插件里随手硬编码相对路径和散落 JSON

## 测试与文档

新增或重构插件时，最少同步：

- `tests/plugins/<name>/`
- `docs/plugins/<name>/README.md`

一个插件结构整理成了 Golden Plugin，却没同步测试和文档，那它只完成了一半。

## 一份简化骨架

```python
from nonebot.plugin import PluginMetadata

from pallas.api.commands import bind_alias_handlers, group_command

from .handlers import handle_main

__plugin_meta__ = PluginMetadata(
    name="example",
    description="示例插件。",
    type="application",
    extra={
        "command_permissions": [...],
        "command_limits": [...],
        "menu_data": [...],
    },
)

cmd = group_command("example.main", "示例命令")
bind_alias_handlers(cmd, handle_main)
```

真正的实现细节应继续下沉到 `handlers.py`、`config.py` 和其他语义化模块。

## 自检清单

提交前至少问自己：

- `__init__.py` 还是不是薄入口
- 配置是否走了统一热重载
- 权限、帮助、冷却是否和命令 ID 对齐
- 是否误把大段实现继续塞在入口文件
- 是否补了最小测试和插件 README

## 相关阅读

- [插件开发入门](getting-started.md)
- [配置与 WebUI](config-and-webui.md)
- [测试](testing.md)
- [内核插件统一化](../../architecture/internal/core-plugin-unification-design.md)
- [Golden Checklist 参考](../../skills/pallas-plugin-development/references/08-golden-plugin-checklist.md)
