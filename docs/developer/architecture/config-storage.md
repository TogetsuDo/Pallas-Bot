# 配置存储

运行时配置事实源与读取合同。插件接法见 [配置与 WebUI](../plugin-development/config-and-webui.md)。权威细节：[settings-storage](../../architecture/settings-storage.md)。

## 事实源

| 源 | 角色 | 用途 |
| --- | --- | --- |
| `config/pallas.toml` | 启动 / 基础设施 | 监听、数据库、部署前提、`[bootstrap]` / `[env]` |
| `.env` / `.env.{ENVIRONMENT}` | 遗留只读合并 | 历史兼容、nb/pip 插件项；禁止作为新主能力首选入口 |
| `data/pallas_config/webui.json` | 运行态最高优先级 | 插件页、通用段、WebUI 覆盖 |

只读快照：`config/pallas.webui.export.toml`（保存时生成，非手写源）。

## 合并顺序

```text
pallas.toml  →  .env  →  webui.json
```

后者覆盖前者。代码不得假设某一单文件为终值。

## 读取入口

| 场景 | API |
| --- | --- |
| 仓库合并键（平台 / 产品） | `pallas.core.foundation.config.repo_settings.repo_env_raw_value`（亦经 `pallas.api.config.repo_env_raw_value` 导出） |
| 启动灌入 environ | `apply_repo_settings_to_environ()` |
| 插件页 | `install_hot_reload_config` → `get_config()` |
| 业务侧禁止 | 散落 `os.environ` 当终值；私有「先 env 再文件」拼读 |

## 热载 vs 重启

| 信号 | 含义 |
| --- | --- |
| WebUI 保存成功 | 落盘成功，不等于所有进程已更新 |
| `install_hot_reload_config` | 插件已接热载通道 |
| 启动层键 | 通常需重启进程 |
| 分片 | hub / worker 必须读同一合并结果；配置是跨进程一致性问题 |

## 分片要求

| MUST | MUST NOT |
| --- | --- |
| 统一读取入口 | hub 本地 env 推断全局 |
| 保存后确认 worker 感知路径 | 各模块私有 fallback 链 |

## 禁止

1. `os.environ[...]` 当作合并后终值
2. 插件自造私有配置文件绕开 `webui.json`
3. 平台横切项塞进单插件私有页

## 相关

- [配置与 WebUI](../plugin-development/config-and-webui.md)
- [分片运行时](shard-runtime.md)
- [settings-storage](../../architecture/settings-storage.md)
