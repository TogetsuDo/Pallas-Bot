# maa（MAA 远控）

实现 [MAA 远程控制协议](https://docs.maa.plus/zh-cn/protocol/remote-control-schema.html)：提供 `getTask` / `reportStatus` HTTP 端点，并通过 QQ 绑定设备、排队任务、回传截图与执行结果。

## 配置 MAA

1. 在 MAA「设置 → 远程控制」填写：
   - **用户标识符**：你的 QQ 号（与绑定命令使用的账号一致）
   - **获取任务端点**：`http(s)://<牛牛可访问地址>/maa/getTask`（POST JSON）
   - **汇报任务端点**：`http(s)://<牛牛可访问地址>/maa/reportStatus`（POST JSON）
2. 保存后 MAA 会每秒轮询；此时设备尚未绑定，接口返回空 `tasks`。
3. 私聊牛牛：`牛牛绑定MAA <设备标识符>`（复制 MAA「设备标识符（只读）」整段，一般为 **32 位十六进制**，不是 QQ 号）。

## 常用口令

| 口令 | MAA 任务 type |
|------|----------------|
| 牛牛长草 / 牛牛一键长草 | LinkStart |
| 牛牛唤醒 | LinkStart-WakeUp |
| 牛牛作战 | LinkStart-Combat |
| 牛牛公招 | LinkStart-Recruiting |
| 牛牛换班 / 牛牛基建 | LinkStart-Base |
| 牛牛信用商店 / 牛牛信用商店领取 | LinkStart-Mall |
| 牛牛任务 | LinkStart-Mission |
| 牛牛肉鸽 | LinkStart-AutoRoguelike |
| 牛牛盐酸 | LinkStart-Reclamation |
| 牛牛截图 / 牛牛立刻截图 | CaptureImage / CaptureImageNow |
| 牛牛停止 / 牛牛停止任务 | StopTask |
| 牛牛心跳 | HeartBeat |
| 牛牛单抽 / 牛牛十连 | Toolbox-GachaOnce / Toolbox-GachaTenTimes |
| 牛牛设置连接 \<值\> | Settings-ConnectionAddress |
| 牛牛设置关卡 \<值\> | Settings-Stage1 |

默认在指令执行后会再排队一张截图（可在插件配置 `maa_attach_screenshot` 关闭）。

## 插件配置项

| 键 | 默认 | 说明 |
|----|------|------|
| `maa_get_task_path` | `/maa/getTask` | 获取任务路径 |
| `maa_report_status_path` | `/maa/reportStatus` | 汇报路径 |
| `maa_attach_screenshot` | `true` | 指令后附加截图任务 |
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
| MAA 提示上传失败 | `reportStatus` 须返回 HTTP 200。 |
| 截图回传失败 | 截图 Base64 体积大，注意反向代理 `client_max_body_size` 等限制。 |

实现见 [`src/plugins/maa/`](../../../src/plugins/maa/)。
