# maa（MAA 远控）

实现 [MAA 远程控制协议](https://docs.maa.plus/zh-cn/protocol/remote-control-schema.html)：提供 `getTask` / `reportStatus` HTTP 端点，并通过 QQ 绑定设备、排队任务、回传截图与执行结果。

## 配置 MAA

1. 在 MAA「设置 → 远程控制」填写（**完整 URL** 以游戏内「牛牛帮助 → MAA 远控」中 **MAA 对接地址** 为准，由部署方在插件配置中生成）：
   - **用户标识符**：你的 QQ 号（与绑定命令使用的账号一致）
   - **获取任务端点**、**汇报任务端点**：见帮助页或私聊绑定成功后的回复
2. 保存后 MAA 会每秒轮询；此时设备尚未绑定，接口返回空 `tasks`。
3. 私聊牛牛：`牛牛绑定MAA <设备标识符> [别名]`（复制 MAA「设备标识符（只读）」整段，一般为 **32 位十六进制**，不是 QQ 号；别名可选，最长 32 字）。

### 多台设备

| 命令 | 说明 |
|------|------|
| `牛牛MAA状态` | 查看已绑定列表与**当前选用**（带「当前」标记） |
| `牛牛清空MAA队列` | 丢弃牛牛内存中尚未被 MAA 拉取的任务（可加参数 `当前` 仅清当前选用设备） |
| `牛牛切换MAA设备 <…>` | 指定远控口令下发目标；可用完整 id、**别名**或至少 **8 位** id 前缀 |
| `牛牛MAA设备名 <设备> <别名>` | 为已绑定设备起名（最长 32 字；别名为空则清除） |

- 每次 `牛牛绑定MAA` 会将该设备设为**当前选用**并持久化，重启后仍有效。
- 仅绑定一台时自动作为当前设备；绑定多台且未切换时，发远控口令会提示先切换。

游戏内可发 **「牛牛帮助」** → 打开 **MAA 远控** 插件，二级页「插件内用法」与三级功能详情含完整口令表（与下文同步）。

## 常用口令

游戏内 **牛牛帮助 → MAA 远控** 含每条口令的用途说明；下表为 type 对照（维护者与 `tasks.py` 同步）。

| 口令 | type | 用途摘要 |
|------|------|----------|
| 牛牛长草 | LinkStart | 完整一键长草 |
| 牛牛唤醒 | LinkStart-WakeUp | 仅唤醒子项 |
| 牛牛作战 | LinkStart | 按 MAA 勾选执行作战相关任务 |
| 牛牛公招 | LinkStart-Recruiting | 仅公招 |
| 牛牛基建 | LinkStart-Base | 仅基建子项（含换班等，依 MAA 配置） |
| 牛牛信用商店 | LinkStart-Mall | 仅信用商店 |
| 牛牛领取奖励 | LinkStart-Mission | 仅领取报酬（Award） |
| 牛牛肉鸽 | LinkStart-AutoRoguelike | 仅自动肉鸽 |
| 牛牛盐酸 | LinkStart-Reclamation | 仅生息演算 |
| 牛牛截图 / 牛牛立刻截图 | CaptureImage / CaptureImageNow | 排队截图 / 立即截图 |
| 牛牛停止 | StopTask | 结束当前任务 |
| 牛牛心跳 | HeartBeat | 查询当前执行任务 id |
| 牛牛单抽 / 牛牛十连 | Toolbox-Gacha* | 工具箱公招单抽/十连 |
| 牛牛设置连接 \<值\> | Settings-ConnectionAddress | 改连接地址 |
| 牛牛设置关卡 \<关卡…\> | Settings-Stage1 | 设置主关卡并保存候选（远控仅写入第 1 候选） |

### 原始 type（远控协议）

发送 **`牛牛MAA任务 <type> [params]`**，在协议白名单内直接下发，效果等同向 `getTask` 返回对应任务。例如：

- `牛牛MAA任务 Settings-Stage1 1-7`
- `牛牛MAA任务 LinkStart-Recruiting`
- `牛牛MAA任务 CaptureImage`

`Settings-*` 类必须带 `params`；其余 type 不要多余参数。可用 type 与[远程控制协议](https://docs.maa.plus/zh-cn/protocol/remote-control-schema.html)一致。

默认在指令执行后会再排队一张截图（`Settings-*` 设置类口令除外；可在插件配置 `maa_attach_screenshot` 关闭）。

## 插件配置项

支持 **WebUI「插件」页保存后立即生效**（`install_hot_reload_config`）；修改 `maa_get_task_path` / `maa_report_status_path` 会重新挂载 HTTP 路由，并清理帮助图缓存。MAA 客户端若已填写旧 URL，须同步改为帮助页展示的新地址。

### 一般部署：只配基址即可

对外暴露 NoneBot HTTP 且使用插件默认路由时，**只需设置 `maa_public_base_url`**（如 `https://nb.example.com`，末尾勿加斜杠）。牛牛会自动拼出：

- `https://nb.example.com/maa/getTask`
- `https://nb.example.com/maa/reportStatus`

`maa_get_task_endpoint` / `maa_report_status_endpoint` 留空即可；`maa_get_task_path` / `maa_report_status_path` 保持默认。仅在反代路径与默认不一致、或 get/report 必须指向不同主机时，再单独填完整 URL 或改路径。

也可在 WebUI **通用配置 → 服务网关 / 连通性** 中编辑 `maa_public_base_url` 并做连通检测。

| 键 | 默认 | 说明 |
|----|------|------|
| `maa_public_base_url` | （空） | **通常只需此项**：对外基址；与默认路径拼成帮助/绑定中的完整 URL |
| `maa_get_task_endpoint` | （空） | （可选）获取任务完整 URL；优先于基址+路径 |
| `maa_report_status_endpoint` | （空） | （可选）汇报任务完整 URL；优先于基址+路径 |
| `maa_get_task_path` | `/maa/getTask` | 相对路径；默认路由下一般不改 |
| `maa_report_status_path` | `/maa/reportStatus` | 相对路径；默认路由下一般不改 |
| `maa_attach_screenshot` | `true` | 指令后附加截图任务 |
| `maa_combat_auto_prepare` | `true` | 牛牛作战前自动排队作战准备（启用作战、写入已保存关卡候选） |
| `maa_seen_ttl_seconds` | `86400` | 未绑定设备登记保留时间 |

## 命令权限（代码默认）

| ID | 默认等级 |
|----|----------|
| `maa.bind` | everyone |
| `maa.control` | everyone |
| `maa.status` | everyone |

实际等级以 WebUI「命令权限」为准。

## 排障

| 现象 | 说明 |
|------|------|
| 绑定提示未检测到轮询 | MAA 未连上或端点 URL 错误；检查牛牛对外 HTTP 是否可达。 |
| 下发后无任务 | 设备未绑定或用户标识符不是 QQ 号；执行「牛牛MAA状态」确认。 |
| 待拉取很多但 MAA 无反应 | 看状态中「当前选用设备」队列是否为 0（设备 id 不一致）；或 getTask URL/绑定有误。可「牛牛清空MAA队列」后重试。 |
| MAA 提示上传失败 | `reportStatus` 须返回 HTTP 200。 |
| 截图回传失败 | 截图 Base64 体积大，注意反向代理 `client_max_body_size` 等限制。 |

实现见 [`src/plugins/maa/`](../../../src/plugins/maa/)。

## 维护者说明

以下内容供排障与改代码时对照，**不要**写进 `PluginMetadata.usage`、`menu_data.detail_des` 或 `MAA_CONTROL_COMMAND_HELPS.description`（会进「牛牛帮助」）。

### 任务分类（MAA 协议）

| 分类 | type 示例 | MAA 行为 |
|------|-----------|----------|
| 顺序任务 | `LinkStart`、`LinkStart-Combat`、`CaptureImage`、`Settings-*` | 按 `getTask` 返回顺序排队；前面的没跑完，后面的要等 |
| 立即任务 | `CaptureImageNow`、`StopTask`、`HeartBeat` | 可在顺序任务运行中插队执行（协议保证尽快返回） |

牛牛 `enqueue` 只写入内存队列；`pending_tasks_for` 按 `created_at` 排序原样交给 MAA，**不做**立即任务优先重排（插队由 MAA 客户端按 type 处理）。

### 唤醒与子项口令

- **`LinkStart`**（牛牛长草）：完整一键长草，**内含唤醒**，再按 MAA 本地勾选跑子模块。
- **`LinkStart-WakeUp`**（牛牛唤醒）：仅唤醒（连模拟器、登录、尽量回主界面）。
- **`LinkStart-*` 其它子项**（作战、公招、基建等）：**不含唤醒**；假设游戏已连上且界面可被 MAA 识别（通常为主界面）。
- **`LinkStart-Mission`**（牛牛领取奖励）：对应 MAA 任务链 `Award`（领取报酬），非「作战」。

牛牛**不会**在子项口令前自动插入 `LinkStart-WakeUp`。用户直接发「牛牛作战」而游戏未开/停在登录或公告时，MAA 侧常见 `SubTaskError` / `TaskChainError`（界面模板匹配失败）；GUI 可能显示为 combat error 等，属 MAA 执行问题，不是牛牛未下发。

### 作战准备与关卡候选

- **`牛牛设置关卡`**：解析最多 4 个关卡候选（空格/逗号分隔，`-` 表示空位），写入 `maa_stage_plan`；向 MAA **仅下发 `Settings-Stage1`（第 1 个非空候选）**，勿下发 `Stage2`～`Stage4` 或 `FightEnable`，否则 MAA 6.10+ 可能把 `StagePlan` 撑满空位并提示「调用了不存在的任务 id」。
- **`maa_combat_auto_prepare`**（默认开）：发「牛牛作战」时，若本批未含 `Settings-Stage1`，会在作战口令对应任务前自动再排队一次已保存的主关卡（`Settings-Stage1`）。
- **「牛牛作战」临时下发 `LinkStart`**（`tasks.COMBAT_COMMAND_TASK_TYPE`）：与一键长草相同机制、按左侧勾选执行；MAA 官方合并远控 Combat 修复后改回 `LinkStart-Combat`。
- **原始 `LinkStart-Combat`**：仍可通过 `牛牛MAA任务 LinkStart-Combat`；官方 MAA 在含「剩余理智」辅助 `FightTask` 时易 `CombatError`。

维护者排障：看 `debug/asst.log` 中 `taskchain`（如 `Combat`、`Mall`）与 `first` 字段（如 `CombatBegin`、`MallBegin`）的重试耗尽后的 `SubTaskError`。

### 截图与 QQ 通知

- 每项任务结束后 MAA `POST reportStatus` → `http_api.maa_report_status` 向 `NotifyTarget`（群/私聊与下发时一致）发消息。
- **`CaptureImage` / `CaptureImageNow`** 且 `payload` 非空：文字 + `base64://` 图；过大则仅文字（见 `MAA_SCREENSHOT_PAYLOAD_MAX_LEN`）。
- **其它 type**：默认仅文字；若 `maa_attach_screenshot=true`（默认），`enqueue` 会再排队一张 `CaptureImage`（`Settings-*` 除外），截图完成后再发图。
- **`HeartBeat`**：仅文字，带当前顺序任务 id。

### 队列与设备

- 队列在进程内存；重启牛牛清空。`牛牛清空MAA队列` / `牛牛清空MAA队列 当前` 见 `store.clear_pending`。
- 口令下发目标 = `get_active_device(qq)`；`getTask` 按 MAA 上报的 `user`+`device` 过滤。设备 id 在 `normalize_device_id` 中统一为 **32 位小写 hex**（UUID 去连字符），避免绑定与轮询格式不一致导致永远 `tasks: []`。
- `getTask` 在 `is_device_verified` 为 false 时返回空列表（未绑定、用户标识符非 QQ 数字等）。MAA 界面**不展示**待拉取列表。
- `牛牛MAA状态` 的「待拉取」= 未 `reportStatus` 的任务；「当前设备队列」= 仅统计 active device，用于判断任务是否发错设备。

### 代码索引

| 逻辑 | 位置 |
|------|------|
| 口令 → type | `tasks.py`：`MAA_CONTROL_COMMAND_HELPS`、`COMMAND_TASK_MAP` |
| 是否附加截图 | `config.maa_attach_screenshot`；`TASK_TYPES_WITHOUT_AUTO_SCREENSHOT`；`store.enqueue` |
| HTTP | `http_api.py`、`http_routes.py` |
| 绑定/活跃设备 | `store.py` |
