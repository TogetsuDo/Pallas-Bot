# Reload 与 Activation

两个正交策略，禁止混用。

| | `reload_policy` | `activation_policy` |
| --- | --- | --- |
| 视角 | 作者 / 插件内部 | 维护者 / 装包运维 |
| 触发 | WebUI 改配置或声明 | 安装、升级、卸载扩展 |
| 类型 | `config_only` \| `metadata` \| `full` | `hot-reloadable` \| `workers-restart` \| `full-restart` |
| 定义 | `pallas.core.plugin_reload.metadata` | `plugin_matrix.ActivationPolicy` |

## `reload_policy`

| 值 | 适用变更 | 运行时行为 |
| --- | --- | --- |
| `config_only` | 开关、频率、文案等配置字段 | 保存即可；`reload` API 可提示无需模块重载 |
| `metadata` | 帮助、权限、ingress 声明 | 重建元数据索引 |
| `full` | 需模块级重载的结构 | 完整 reload / 重启 |

代码级逻辑变更仍按进程重启理解，与上述枚举无关。

## `activation_policy`

| 值 | 适用扩展 | 生效动作 |
| --- | --- | --- |
| `hot-reloadable` | 轻量命令 / 配置型 | 可能热载（unified 模式） |
| `workers-restart` | 主要跑在 worker 的玩法 | 重启 worker |
| `full-restart` | 影响 hub、协议端或全局挂载 | 全量重启 |

## 并存示例

```text
reload_policy = metadata
activation_policy = workers-restart
```

含义：WebUI 改声明可重建索引；新装 / 升级包仍需 worker 重启才真正生效。

## 规则

| 角色 | 规则 |
| --- | --- |
| 作者 | 按变更粒度选 `reload_policy`；勿把代码变更标成可热载 |
| 维护者 | 装包看 `activation_policy`；支持配置热载 ≠ 装包免重启 |

分级总览：[hot-reload-tiers](../../architecture/hot-reload-tiers.md)。

## 相关

- [元数据](metadata.md)
- [插件治理](../architecture/plugin-governance.md)
