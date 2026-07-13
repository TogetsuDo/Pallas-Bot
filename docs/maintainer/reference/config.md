# 配置参考

配置索引：先看哪里、哪些立即生效、哪些要重启。不是把所有键平铺成百科。

## 先记住三件事

- 主配置：`config/pallas.toml`
- WebUI 落盘：`data/pallas_config/webui.json`
- 最终运行值以 WebUI 覆盖优先级最高

## 三类配置来源

### 1. 主配置文件

`config/pallas.toml` 负责更偏基础设施的内容：

- 监听地址与端口
- 数据库
- 基础环境
- 角色与部署前提

这类配置更接近「服务如何启动」。

### 2. WebUI 运行中落盘

`data/pallas_config/webui.json` 负责更偏运行态治理的内容：

- 插件配置页保存值
- 通用配置段
- 命令权限覆盖
- 各类策略、阈值、治理项

这类配置更接近「服务启动后怎样运行」。

### 3. 遗留兼容环境变量

根目录 `.env` 仍可保留，但在 4.0 里不再作为主入口：

- 只为兼容旧项或第三方插件保留
- 不要再把新的主运行配置堆回 `.env`

## 主要配置入口

| 配置类型 | 位置 | 什么时候改 |
| --- | --- | --- |
| 主运行配置 | `config/pallas.toml` | 监听地址、端口、数据库、superusers、基础环境 |
| 运行中通用配置 | `data/pallas_config/webui.json` | WebUI 保存的插件与通用配置 |
| 遗留兼容环境变量 | `.env` | 仅保留兼容或第三方插件相关，不再作为主入口 |

## 覆盖顺序怎么理解

排障时最容易犯的错，就是只看自己刚改的那一处。实际运行时按这个顺序理解：

1. `pallas.toml`
2. `.env` / `.env.{ENVIRONMENT}`
3. `webui.json`

所以：

- 你在 `pallas.toml` 里改对了，不代表最终值真的生效。
- 只要 WebUI 对同名项保存过，最终运行值通常优先看 `webui.json`。

## 哪些配置通常要重启

通常需要重启的场景：

- 端口变更
- 数据库连接变更
- 启停角色或分片方式变更
- 主进程启动链相关环境变更
- 官方插件安装、卸载、升级

这类变更影响的是「进程如何起来」，而不是简单的运行态参数。

## 哪些配置通常可直接生效

通常保存后即可生效的场景：

- 插件开关类配置
- 通用配置段
- 命令权限
- 冷却、阈值、策略型配置
- 已正确接入热重载的插件页配置

::: warning 这不是绝对保证
能否立即生效还取决于：

- 插件是否接入 `install_hot_reload_config`
- 对应配置是否只影响运行态
- 当前部署是否为分片，以及 worker 是否能读到共享落盘
:::

## 分片下要额外注意什么

分片时别以为「只改了 hub 就完了」。要确认：

- hub 与 worker 共用同一份 `data/pallas_config/webui.json`
- worker 能感知磁盘修订变化
- 当前问题到底是配置没落盘，还是 worker 没读到更新

如果分片下出现「WebUI 显示保存成功，但行为没变」，先查共享 `data/` 和落盘文件，别直接怀疑业务逻辑。

## 配置排障先看什么

按这个顺序判断：

1. 你改的是 `pallas.toml`、WebUI，还是遗留 `.env`
2. 该键是否被 `webui.json` 覆盖
3. 当前问题属于启动配置还是运行态配置
4. 这一类变更应该热生效还是需要重启
5. 分片下 worker 是否真的读到了新值

## 最常见的三类误判

### 改了 `pallas.toml`，但实际行为没变

通常要先怀疑：

- 同名键已被 WebUI 覆盖
- 改的是启动层配置，但进程还没重启

### WebUI 保存成功，但线上行为没变化

通常要先怀疑：

- 插件没接热重载
- 该配置本来就需要重启
- 分片 worker 没看到共享落盘更新

### `.env` 改了，结果和预期不一致

通常说明：

- 这个键现在已经不应以 `.env` 为主入口
- 或者已经被更高优先级的 WebUI 落盘覆盖

## Docker 挂载与迁移

| 宿主机 | 容器内 |
| --- | --- |
| `pallas-bot/config/pallas.toml` | `/app/config/pallas.toml` |
| `pallas-bot/data/` | `/app/data/` |

从旧 `.env` 一次性迁移：

```bash
uv run python tools/migrate_env_to_pallas.py
```

## 推荐阅读顺序

- 想理解合并顺序与读取 API：看 [配置存储](../../developer/architecture/config-storage.md)
- 想本机跑通：看 [五分钟跑起来](../../guide/quickstart.md)
- 想查部署形态：看 [运维入口](../quickstart.md)
- 想改运行中配置：看 [WebUI 运维](../operate/webui.md)
- 想排查保存后不生效：看 [排障](../operate/troubleshooting.md)
- 想站点定制与更新：看 [升级](../deploy/upgrade.md)
