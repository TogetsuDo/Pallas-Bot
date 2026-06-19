# Reload 与 Activation

这两个概念在 4.0 里必须分开理解。

- `reload_policy`：作者角度，插件内部哪些改动可以不重启
- `activation_policy`：维护者角度，安装或更新后怎样生效

很多混乱都来自把这两个词当成一件事。

## `reload_policy`

它描述插件配置或元数据变更的热载边界。

常见值：

- `config_only`
- `metadata`
- `full`

你要关注的是：

- WebUI 保存配置后，插件是否能立即反映
- 改帮助、ingress、权限声明后是否需要重启
- 代码本身改了以后是否仍然必须重启

典型判断：

- 只改阈值、开关、文案：优先考虑 `config_only`
- 改帮助声明、权限声明、ingress 声明：通常更接近 `metadata`
- 改 Python 逻辑：仍然按重启理解

## `activation_policy`

它描述官方扩展安装、升级、卸载之后怎样让新状态真正生效。

常见值：

- `hot-reloadable`
- `workers-restart`
- `full-restart`

这更偏运维语义，而不是插件代码结构语义。

典型判断：

- 纯命令和轻量配置插件：可能接近 `hot-reloadable`
- 主要运行在 worker 的扩展：常见是 `workers-restart`
- 会影响 hub、协议端或全局挂载的扩展：更接近 `full-restart`

## 两者的典型区别

一个插件可能：

- `reload_policy = metadata`
- `activation_policy = workers-restart`

这并不矛盾。

含义只是：

- 你在 WebUI 改元数据相关配置时，平台能重建索引，不必立刻重启
- 但你刚安装或升级这个扩展包时，仍然需要 worker 重启才算真正生效

## 开发者应该怎么用

写插件时：

1. 先判断配置改动是否应立即生效
2. 再判断帮助和治理声明是否需要热载
3. 不要把代码级变更伪装成热载问题

## 维护者应该怎么理解

::: warning 支持配置热重载 ≠ 装包后不用重启
安装或升级插件时，看 `activation_policy`。不要只因为“插件支持配置热重载”就推断“装包后不用重启”。
:::

## 相关阅读

- [元数据](metadata.md)
- [热重载分级](../../architecture/hot-reload-tiers.md)
- [插件治理](../architecture/plugin-governance.md)
