# 元数据

Pallas 4.0 里的插件元数据，不只是“给帮助图看”的装饰字段，而是插件治理、权限、帮助、配置与运行时行为的声明入口。

把它当成插件对平台的契约，而不是可有可无的附注。

## 元数据至少承载什么

通常至少包括：

- 名称与描述
- `usage`
- `menu_data`
- `command_permissions`
- `command_limits`
- `reload_policy`
- `activation_policy`

## 为什么元数据这么重要

4.0 下，很多平台能力依赖声明式信息，而不是靠平台去猜插件行为：

- 帮助系统依赖 `usage` 和 `menu_data`
- 命令权限页依赖 `command_permissions`
- 冷却展示依赖 `command_limits`
- 热重载能力展示依赖 `reload_policy`
- 插件安装后的生效方式依赖 `activation_policy`

元数据不完整，插件即使“功能能跑”，也很难进入现行治理体系。

## `usage` 与 `menu_data`

这两个字段各管一摊：

- `usage`：给帮助图和插件说明做统一口令展示
- `menu_data`：给帮助系统和治理页面提供更结构化的入口信息

一个常见错误是把权限信息直接写死进 `usage` 或 `trigger_condition`。4.0 里不推荐这么做，权限应交给运行时和 WebUI 覆盖系统表达。

## `command_permissions`

每个可独立治理的命令，最好都对应一个稳定的命令 ID。

例如：

```python
"command_permissions": [
    {"id": "my_plugin.demo", "label": "牛牛示例", "default": "everyone"},
]
```

这样同一个命令 ID 会贯穿：

- matcher 权限
- WebUI 命令权限覆盖
- 帮助图中的“何人可用”

## `command_limits`

这是冷却声明，不只是给代码自己看的。

即使实际冷却在 handler 里判断，也建议把默认值声明出来，让文档、帮助和治理页面能统一感知。

## `reload_policy`

这是你站在插件实现角度，对“改了什么之后能否不重启”给出的声明。

常见值：

- `config_only`
- `metadata`
- `full`

它关注插件内部变更粒度，不等同于维护者安装/更新扩展后的生效方式。

## `activation_policy`

这是站点运维视角的声明，说明安装、升级、卸载后需要怎样生效。

常见值：

- `hot-reloadable`
- `workers-restart`
- `full-restart`

::: warning 别和 reload_policy 混用
这和 `reload_policy` 是两件不同的事，插件文档里要避免混用。
:::

## 常见最小组合

### 纯命令型插件

通常至少应有：

- `command_permissions`
- `command_limits`
- `menu_data`

### 维护者向插件

通常重点不在群口令，而在：

- `help_audience`
- `activation_policy`
- WebUI 或运维入口说明

### 带配置页插件

除了上面这些，还应明确：

- 配置项是否热重载
- `reload_policy` 取值

## 一份最小示例

```python
extra={
    "command_permissions": [
        {"id": "my_plugin.demo", "label": "牛牛示例", "default": "everyone"},
    ],
    "command_limits": [
        {"id": "my_plugin.demo", "seconds": 10},
    ],
    "reload_policy": "metadata",
    "activation_policy": "hot-reloadable",
}
```

## 一份稍完整的方向

对一个更接近 4.0 标准的插件，通常还会继续补：

- `menu_template`
- `plugin_storage`
- 更完整的 `menu_data`
- 明确的 `help_audience`

## 自检问题

写完插件元数据后，至少问自己：

- 命令 ID 是否统一
- 权限是否通过声明表达，而不是写死文案
- 帮助系统是否能仅靠元数据理解这个插件
- 安装和更新后的生效方式是否明确

## 相关阅读

- [Golden Plugin](golden-plugin.md)
- [Reload 与 Activation](reload-and-activation.md)
- [cmd_perm](../../common/cmd_perm/README.md)
- [command_limits](../../common/command_limits/README.md)
