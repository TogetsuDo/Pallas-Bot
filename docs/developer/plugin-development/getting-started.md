# 插件开发入门

最小闭环：可加载插件 → 元数据 / 权限 / 帮助对齐 → 配置热载（如需）→ 测试 + README。

## 放置位置

| 类型 | 路径 | 用途 |
| --- | --- | --- |
| 站点私有 | `local/plugins/` | 试验、未上游化 |
| 内置 core | `packages/` | 随主仓发布 |
| 官方 / 社区扩展 | 独立仓库 | 独立版本与安装 |

验证优先从 `local/plugins/` 开始。

## 完成定义（DoD）

| 项 | 要求 |
| --- | --- |
| 入口 | Golden 目录；`__init__.py` 只做声明与注册 |
| API | 社区扩展只 import `pallas.api.*` |
| 权限 | `extra["command_permissions"]`；`usage` / `trigger_condition` 不写死角色 |
| 帮助 | `usage` + `menu_data`；命令 ID 一致 |
| 配置 | 有插件页则 `install_hot_reload_config` + `get_config()` |
| 测试 | `tests/plugins/<name>/` 至少覆盖 metadata |
| 文档 | `docs/plugins/<name>/README.md`（扩展仓则自有 README） |

## 实施顺序

1. [Golden Plugin](golden-plugin.md) 定目录与 `__init__.py`
2. `config.py` 接热载（有配置页时）
3. `handlers.py` 写口令逻辑；`bind_alias_handlers` / `group_command`
4. 补 metadata 测试与 README
5. 需要发版时走 [发布](publishing.md)

## 硬约束

| MUST | MUST NOT |
| --- | --- |
| 使用 `pallas.api.*` | 依赖旧 `src.*` 或 `pallas.core.*`（社区扩展） |
| `__init__.py` 保持薄入口 | 把业务 / 持久化 / 长启动逻辑堆在入口 |
| 权限走 `command_permissions` | 在帮助文案写死「仅群管」等角色 |
| 配置走统一热载入口 | 自造并行配置文件或长期缓存 `get_config()` 快照 |

## 相关

- [Golden Plugin](golden-plugin.md)
- [配置与 WebUI](config-and-webui.md)
- [pallas.api Cookbook](pallas-api-cookbook.md)
- [测试](testing.md)
