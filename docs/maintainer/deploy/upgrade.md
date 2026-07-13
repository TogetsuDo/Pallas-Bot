# 升级

把各层升级对齐，别漏掉任何一层。

4.0 的升级别当成“只拉主仓代码”。它是多层联动的活儿。

## 先分三层看

1. 本体升级
2. 官方扩展升级
3. WebUI / AI Runtime / 协议端联动升级

::: warning
任何一层没对齐，都可能出现“服务能跑，但表现像半升级状态”。
:::

## 升级前先确认什么

先回答这几个问题：

- 这次只升级主仓，还是包含官方扩展与前端资源？
- 当前是单进程还是分片？
- 当前是否接入了协议端和 AI Runtime？
- `config/`、`data/` 是否已备份？

::: warning
这些边界没搞清楚，先别直接上线升级。
:::

## 推荐升级顺序

### 1. 先备份运行数据

至少保护这些内容：

- `config/pallas.toml`
- `data/`
- 如有需要，再备份数据库和协议端实例数据

### 2. 升级主仓代码与依赖

这一步关注的是：

- 主仓版本本身
- Python 依赖是否同步
- 新配置项是否需要补齐

### 3. 升级官方扩展

别默认“主仓升级后扩展一定兼容旧状态”。

确认这些：

- 已安装扩展的版本
- 是否需要同步到对应 PyPI 新版
- 插件治理、元数据、配置页是否与主仓能力一致

### 4. 同步 WebUI 资源

这次变更涉及控制台页面或接口契约的话：

- 只升级后端不够
- 还要同步当前版本对应的 WebUI 静态资源

### 5. 联调协议端与 AI Runtime

部署里用到了协议端管理或 AI 回调链路时，升级后都至少做一次最小联调，确认外部运行时没因为地址、字段或行为变化而漂移。

## 单进程与分片下的差异

### 单进程

重点是：

- 本体能否正常启动
- WebUI 与协议端是否恢复正常
- 关键插件是否按预期生效

### 分片

除上述外，还要额外确认：

- hub 与 worker 都已升级到一致版本
- 共用 `data/` 没有残留旧状态导致聚合异常
- registry、worker 端口和协议端连接关系仍一致
- shard 观测接口与控制台状态正常

## 升级后最少验证

升级完成后，至少验证：

1. Bot 本体正常启动。
2. WebUI 能打开且页面不是旧资源。
3. `/pallas/api/health` 与基础状态接口正常。
4. 协议端连接正常，账号在线状态正确。
5. 官方扩展列表、治理页、命令权限页能正常工作。
6. 如接入 AI Runtime，最小任务能走通。
7. 如为分片，worker 聚合状态正常。

## 最常见的升级后问题

### 页面样式或字段像旧版

通常是 WebUI 静态资源没有同步。

### 插件行为和帮助展示不一致

通常是主仓、扩展和元数据治理能力版本不一致。

### 分片状态异常，但进程都在线

通常要回头看：

- registry
- 共用 `data/`
- worker 聚合接口
- 协议端是否连到了正确 worker

## 更稳妥的升级策略

更建议这样做：

- 一次升级一类环境
- 升级后立刻做最小回归验证
- 明确区分“主仓升级”和“整套运行环境升级”

::: warning
别把协议端、AI Runtime、WebUI 和主仓升级，混成一条不可回退的黑盒流程。
:::

## 站点定制：更新时不丢本地改动

| 内容 | 放哪里 | 更新主仓时 |
| --- | --- | --- |
| 监听、数据库、超管 | `config/pallas.toml` | 不动 |
| 插件 / 通用配置 | `data/pallas_config/webui.json` | 不动 |
| 运行数据、协议实例 | `data/` | 不动 |
| 站点自有插件 | `local/plugins/` + `extra_plugin_dirs` | 不动 |

避免直接改已跟踪源码；否则「应用 Bot 更新」需要 stash / 手工合并。

### 站点自有插件

1. 在 `local/plugins/<插件名>/` 按 NoneBot 插件结构放置代码
2. 在 `config/pallas.toml` 设置：

```toml
[bootstrap]
extra_plugin_dirs = ["local/plugins"]
```

3. 重启 Bot（分片需重启 hub 与对应 worker）
4. 与官方扩展 / 内置插件同名时 **优先加载 local**

社区插件商店与官方扩展商店见 [社区插件商店](../../guide/community-plugin-store.md)、[安装插件](../../guide/install-plugins.md)。

### 部署形态与更新方式

控制台「版本与更新 → Bot 本体」检测 `deployment_mode`：

| 模式 | 含义 | 推荐更新 |
| --- | --- | --- |
| `docker` | 非 git 工作副本 | `docker compose pull` + `up -d` |
| `release_tag` | HEAD 在 Release tag 且干净 | WebUI「应用 Bot 更新」或 `git checkout --detach vX.Y.Z` |
| `release_tag_dirty` | tag 上有本地改动 | 先迁定制到 `local/`；更新会 stash → checkout → stash pop |
| `dev_clone` | 非精确 tag（如 `main`） | `git pull --ff-only --autostash` |

Docker 可挂载 `./pallas-bot/local/plugins:/app/local/plugins`；镜像更新只替换代码，挂载的插件与 `data/`、`config/` 保留。

### Docker 外挂插件卷

[`docker-compose.yml`](https://github.com/PallasBot/Pallas-Bot/blob/main/docker-compose.yml) 可选挂载：

```yaml
- ./pallas-bot/local/plugins:/app/local/plugins
```

宿主机 `pallas-bot/config/pallas.toml` 中设置 `extra_plugin_dirs = ["local/plugins"]`。

### 生产门禁：重复命令 prefix

同时使用 local 整包覆盖与官方扩展时，可能出现同一口令被多个模块注册。生产建议：

```toml
[env]
PALLAS_DUPLICATE_PREFIX_STRICT = "true"
```

检测到冲突时阻断启动。

## 相关阅读

- [运维入口](../quickstart.md)
- [配置参考](../reference/config.md)
- [配置存储](../../developer/architecture/config-storage.md)
- [WebUI](../install/webui.md)
- [协议端](../install/protocol.md)
- [LLM 与 AI 运维](../operate/llm-and-ai.md)
- [3.0 迁移](../../Migration-v3.md)
