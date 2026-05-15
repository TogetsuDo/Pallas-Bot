# blacklist（牛牛黑名单）

按命令发起场景区分：

- **私聊**发 `牛牛拉黑` / `牛牛解禁`：维护 **`UserConfig.banned`（全局）**；除好友请求仅看全局外，凡带 `group_id` 的 OneBot V11 事件也会先查全局。
- **群聊**发同上命令：维护该群的 **`GroupConfig.blocked_user_ids`（本群）**；仅当事件上存在 **`group_id > 0`** 时，若行为者 QQ 在本群名单中则丢弃事件（含群内 **notice**、消息、入群邀请等）；**私聊、好友请求**不受本群名单影响。

## 指令

| 命令 | 别名 | 说明 |
|------|------|------|
| `牛牛拉黑` | `牛牛屏蔽` | 解析正文 **5～15 位** QQ（首位 1～9）及 `@`；**不会拉黑 Bot 自身**。私聊 → 全局 `banned=true`；群聊 → 本群 `blocked_user_ids` 追加。 |
| `牛牛解禁` | `牛牛取消屏蔽`、`牛牛取消拉黑` | 同上；私聊 → 全局解禁；群聊 → 从本群名单移除。 |

未附带任何有效 QQ / `@` 时，会提示补充目标，并**不会**继续执行成功分支。

### 权限

与 WebUI「通用配置 → 命令权限」中的 `blacklist.add` / `blacklist.remove` 一致。

| 场景 | 谁可用 |
|------|--------|
| 任意 | NoneBot **超管** |
| 私聊 | **号主**（`user_is_bot_admin`） |
| 群聊 | 群主 / 群管 **或** **号主** |

## 事件门禁（`event_preprocessor`）

行为者 QQ 见源码 `event_actor_user_id`；是否带群见 `event_group_id`（`group_id` 为正整数时视为群内上下文）。

- **全局拉黑**：与原先一致；好友请求仅在此为真时 `reject` 并忽略。
- **本群拉黑**：当事件含 `group_id` 且行为者在该群的 `blocked_user_ids` 内则忽略（含 `GroupRequestEvent` 入群邀请等）。
- **好友请求**：**仅**全局拉黑会拒绝；仅本群拉黑的用户仍可发好友请求（无 `group_id`）。

## 数据

| 场景 | 存储 |
|------|------|
| 全局 | `UserConfig.banned` |
| 本群 | `GroupConfig.blocked_user_ids`（升序去重 QQ 列表） |

控制台 / WebUI 改写 `user_config.banned` 或 `group_config.blocked_user_ids` 后：用户侧用 **`invalidate_user_ban_gate_cache`**；本群名单用 **`invalidate_group_ban_gate_cache(group_id)`**（WebUI 更新 `blocked_user_ids` 时会自动失效该群门禁缓存）。仍有 TTL（约 45s）时可能短暂不一致。

**MongoDB**：`GroupConfigModule` 已声明 `blocked_user_ids`；旧文档无该字段时读入等价于空列表，**无需**像 SQL 那样执行迁移。

**PostgreSQL 已有库**：`init_pg()` 在 `create_all` 之后会检测 `group_config` 是否缺少 **`blocked_user_ids`** 列，缺则自动 **`ALTER TABLE ... ADD COLUMN`**（见 `repository_pg._ensure_pg_group_config_blocked_user_ids`）。若你自行管理 schema 且禁用了该初始化路径，仍可手动执行：`ALTER TABLE group_config ADD COLUMN IF NOT EXISTS blocked_user_ids JSONB NOT NULL DEFAULT '[]'::jsonb;`

## 门禁查询与安全策略

| 机制 | 说明 |
|------|------|
| 全局 | `query_user_ban_status_for_gate`：单用户 TTL 缓存，超时 / 异常 **放行**。 |
| 本群 | `query_group_blocked_for_gate`：按 **群** 缓存该群整份 `blocked_user_ids` 集合，超时 / 异常 **放行**。 |

测试或排障：`reset_user_ban_gate_cache()`、`reset_group_ban_gate_cache()`（或 `invalidate_group_ban_gate_cache(None)` 清空本群门禁缓存）。

## 排障

| 现象 | 说明 |
|------|------|
| 本群已解禁仍被拦 | 等 TTL 或调 `invalidate_group_ban_gate_cache(群号)` / `reset_group_ban_gate_cache()`。 |
| 全局已解禁仍被拦 | `invalidate_user_ban_gate_cache` / `reset_user_ban_gate_cache()`。 |

## 关联

- [`UserConfig`](../../../src/common/config/__init__.py)、[`GroupConfig`](../../../src/common/config/__init__.py) 的拉黑相关方法。
- [`greeting`](../greeting/README.md) 的 `kick_me` 仍为 **`UserConfig(operator).ban()`（全局）**，与本群名单独立。

实现见 [`src/plugins/blacklist/__init__.py`](../../../src/plugins/blacklist/__init__.py)。
