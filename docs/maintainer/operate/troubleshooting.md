# 排障

这页只回答一件事：Pallas 4.0 出问题时，先看什么、后看什么。

别一上来就全仓搜索、重装依赖或怀疑某个插件源码。大部分运行时问题，都能先归到下面五类之一：

- 配置没生效
- 角色判断错了
- 协议端没有连上正确目标
- WebUI 资源或聚合状态不对
- 扩展存在，但没有真正加载或生效

## 建议排障顺序

1. 确认部署形态
2. 确认配置来源
3. 确认运行角色与连接路径
4. 看对应日志
5. 再看 WebUI 聚合状态与插件状态

## 第一步：先分清你在查哪种部署

先回答几个问题：

- 这是单进程还是分片部署
- 是主仓源码部署、Docker 部署，还是混合目录部署
- 问题发生在 core、官方扩展、协议端，还是 WebUI

::: warning 部署形态没分清，后面全白费
连部署形态都没分清，后面大概率会看错日志、看错端口、看错仓库。
:::

## 第二步：确认配置到底从哪来

4.0 配置优先级是：

1. `config/pallas.toml`
2. 遗留 `.env`
3. `data/pallas_config/webui.json`

最终以 WebUI 落盘覆盖前面的同名项。

::: warning 最常见的误判
你改了 `pallas.toml`，但运行中仍被 `webui.json` 覆盖，看起来就像「改了没用」。
:::

## 第三步：看对角色和连接路径

::: details 单进程：优先确认这些
- Bot 是否成功启动
- 协议端是否连接到当前进程
- 扩展是否在当前进程中加载
:::

::: details 分片：优先确认这些
- 问题发生在 hub 还是 worker
- 协议端连接的是不是目标 worker
- Redis 是否可达
- hub 聚合到的 worker 状态是否正常

分片排障默认先看这两个日志，不要优先翻单进程日志：

- `data/pallas_shard/logs/hub.log`
- `data/pallas_shard/logs/worker-*.log`
:::

## 第四步：按问题类型看日志

::: details WebUI 页面旧了或和源码不一致
- `data/pb_webui/public/` 是否是新产物
- 浏览器缓存是否刷新
- 你改的是不是 `Pallas-Bot-WebUI` 源码仓
:::

::: details 协议端连不上
- 协议端实例里的 `ws_url`
- 分片下 `registry.json` 的端口映射
- 对应 worker 是否真的在监听那个端口
:::

::: details 扩展装了但没反应
- 是否已经重启
- 是否安装到当前运行环境
- 是否被 `local/plugins/` 同名插件覆盖
- 分片下是不是只看了 hub，没有看 worker
:::

::: details AI 任务发出了，但没有回执
- AI runtime 回调是否打到 hub
- hub 是否成功路由到目标 worker
- 目标 worker 是否仍在线
:::

::: details 命令权限或 cooldown 不符合预期
- 代码默认值
- WebUI 命令权限覆盖
- 分片下 hub 聚合到的 worker 插件元数据是否完整
:::

## 常看的关键路径

配置：

- `config/pallas.toml`
- `data/pallas_config/webui.json`

单进程日志：

- 当前 Bot 进程日志

分片日志：

- `data/pallas_shard/logs/hub.log`
- `data/pallas_shard/logs/worker-*.log`
- `data/pallas_shard/registry.json`
- `data/pallas_shard/stats/worker-*.json`

WebUI 运行资源：

- `data/pb_webui/public/`

## 看到现象后，先做哪个判断

| 现象 | 第一判断 |
| --- | --- |
| 页面没更新 | 资源同步或缓存问题 |
| 页面能开但数据错 | API 契约或 worker 聚合问题 |
| QQ 在线但不回复 | 协议端连接、worker 日志、Redis |
| 商店显示已安装但功能没生效 | 进程未重启或加载路径冲突 |
| 只有某只 Bot 或某个群异常 | 先定位对应 worker，不要全局扫 |

## 不要这样排

- 不要在分片问题里先看单进程日志。
- 不要把 WebUI 源码仓和主仓运行产物当成同一份东西。
- 不要只看到「命令匹配了」就当成功，还要区分是否真的执行成功。
- 不要因为页面缺数据就默认是前端 bug，很多时候是 worker 元数据没聚合上来。

## 还是定位不到？

走完这页的顺序仍无法确定问题，再按专题深挖：

- 协议端与账号管理：看 [协议端安装与管理](../install/protocol.md)
- 分片连接与协调：看 [分片部署](../deploy/sharded.md)
- WebUI 资源与控制台：看 [WebUI](../install/webui.md)
- 常见环境问题：看 [FAQ](../../FAQ.md)

## 延伸阅读

- [FAQ](../../FAQ.md)
- [协议端](../install/protocol.md)
- [分片部署](../deploy/sharded.md)
- [官方扩展安装](../install/official-extensions.md)
