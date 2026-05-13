# blacklist（牛牛黑名单）

按 QQ **全局**维护 `UserConfig.banned`：被拉黑用户与当前 Bot 的 **OneBot V11 交互**在事件入口被丢弃（`IgnoredException`），并可通过命令批量拉黑 / 解禁。

## 指令

| 命令 | 别名 | 说明 |
|------|------|------|
| `牛牛拉黑` | `牛牛屏蔽` | 解析正文中的 **5～15 位** QQ 号（首位 1～9）及消息中的 `@`，写入 `banned=true`；**不会拉黑 Bot 自身**（`self_id` 会被过滤）。 |
| `牛牛解禁` | `牛牛取消屏蔽`、`牛牛取消拉黑` | 同上解析目标，写入 `banned=false`。 |

未附带任何有效 QQ / `@` 时，会提示补充目标（文案见插件内 `finish`），并**不会**继续执行后续成功分支。

### 权限

| 场景 | 谁可用 |
|------|--------|
| 任意 | NoneBot **超管** |
| 私聊 | 当前 Bot 的 **管理员**（`user_is_bot_admin`） |
| 群聊 | 群主 / 群管 **或** 当前 Bot 的管理员 |

## 事件门禁（`event_preprocessor`）

在 **OneBot V11** 事件上，根据「行为者」QQ 查拉黑状态；若为已拉黑且非 Bot 自身：

- **好友请求**：尝试 `reject` 后抛出 `IgnoredException`（`reject` 失败仅打日志，仍会忽略事件）。
- **入群邀请**（`GroupRequestEvent`，`sub_type == "invite"`）：同上尝试拒绝后忽略。
- **其余**（群/私聊消息、戳一戳、上传、撤回操作者等）：直接 `IgnoredException`，后续 Matcher 不再处理。

行为者 QQ 的提取规则见源码 `event_actor_user_id`（消息类用 `user_id`，群撤回用 `operator_id` 等）。

## 数据

- 字段：`UserConfig`（按 `user_id` 存文档/行）上的 **`banned`** 布尔值。
- 控制台 / WebUI 若也改写同一用户的 `banned`，门禁侧有 **内存 TTL 缓存**（默认约 45 秒），在缓存未过期前可能仍按旧状态判断；本插件内拉黑/解禁及 [`greeting`](../greeting/README.md) 中「被踢自动拉黑」路径会调用 **`invalidate_user_ban_gate_cache`** 主动失效对应 QQ 的缓存。

## 门禁查询与安全策略

门禁通过 **`query_user_ban_status_for_gate`** 读库，内置：

| 机制 | 默认/说明 |
|------|-----------|
| 单次查库超时 | **3 秒**（`asyncio.wait_for`）；超时记日志并视为 **未拉黑（放行）**，避免事件链与连接池被拖死。 |
| 查库异常 | 记 `exception` 日志后同样 **放行**（fail-open）。 |
| 取消 | `asyncio.CancelledError` **原样上抛**，不吞。 |
| 正/负结果缓存 | TTL **45 秒**；条目数超上限时先清过期项，仍过多则整表清空。 |

其它代码路径在直接 `UserConfig.ban()` / `unban()` 后，若希望门禁立即一致，应 **`await invalidate_user_ban_gate_cache(qq)`**（可传单个 `int` 或可迭代 QQ 列表）。

测试或排障可 **`await reset_user_ban_gate_cache()`** 清空整表内存缓存。

## 排障

| 现象 | 说明 |
|------|------|
| 已拉黑仍能发指令 | 查库超时/异常时策略为 **放行**；看日志是否有 `is_banned timeout` / `is_banned failed`。 |
| 控制台已解禁，Bot 仍拦 | 等待缓存 TTL，或重启进程 / 调用 `invalidate_user_ban_gate_cache` / `reset_user_ban_gate_cache`。 |
| 命令无反应 | 检查是否具备群管/群主或 Bot 管理员/超管；命令是否被其它插件抢占（本插件命令 `priority=5`，`block=True`）。 |

## 关联

- **用户配置**：[`UserConfig`](../../../src/common/config/__init__.py) 的 `ban` / `unban` / `is_banned`。
- **欢迎 / 被踢**：[`greeting`](../greeting/README.md) 在开启 `enable_kick_ban` 且 `kick_me` 时会 `UserConfig(operator).ban()` 并失效门禁缓存。

实现见 [`src/plugins/blacklist/`](../../../src/plugins/blacklist/)（入口 [`__init__.py`](../../../src/plugins/blacklist/__init__.py)）。
