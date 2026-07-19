# help（牛牛帮助）

三级帮助图（Markdown 渲染）；群管/超管可开关本群插件。

## 用户命令

| 口令 | 场景 | 说明 |
| --- | --- | --- |
| 牛牛帮助 | 群内或私聊 | 插件总览与开关 |
| 牛牛帮助 \<插件\> | 群内或私聊 | 插件功能表 |
| 牛牛帮助 \<插件\> \<功能\> | 群内或私聊 | 单条功能详情 |
| 牛牛开启 / 牛牛关闭 + 插件名 | 群内 | 开关单插件 |
| 牛牛开启全部功能 / 牛牛关闭全部功能 | 群内 | 批量开关 |

## 命令权限

| 命令 ID | 默认等级 |
| --- | --- |
| `help.help` | everyone |
| `help.plugin_enable` / `help.plugin_disable` | staff |
| `help.plugin_enable_all` / `help.plugin_disable_all` | staff |

## 配置

[`config.py`](../../../src/plugins/help/config.py)：`default_style`、`custom_styles`、`ignored_plugins` 等。视觉令牌见 [VISUAL.md](./VISUAL.md)。

## 排障

| 现象 | 处理 |
| --- | --- |
| 成图失败 | 查样式路径与日志 |
| 开关无效 | 确认插件名；部分插件另有独立开关 |

## 实现

[`src/plugins/help/`](../../../src/plugins/help/)
