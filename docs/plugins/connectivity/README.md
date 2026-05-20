# 牛牛连通检测 (Connectivity)

群内检测画画网关、MAA 远控端点与唱歌服务的连通性与延迟；WebUI **通用配置 → 服务网关 / 连通性** 可集中编辑相关地址并一键检测。

## 功能

- **牛牛连通**：并行探测画画 API 网关、MAA `getTask` / `reportStatus`、唱歌 AI 服务。
- **牛牛网关**：与「牛牛连通」相同（兼容旧口令）；权限可使用 `connectivity.probe` 或历史的 `pallas_image.gateway`。

输出示例：

```text
牛牛画画：主网关：85ms
MAA远控：获取任务：42ms
MAA远控：汇报任务：38ms
唱歌：根路径：12ms
```

## 配置入口

| 入口 | 说明 |
| :--- | :--- |
| WebUI **通用配置 → 服务网关 / 连通性** | 画画主/备网关、MAA 对外地址、唱歌主机与端口；支持**检测连通**（可不保存先测草稿）。 |
| WebUI **插件 → 牛牛画画** | 完整画画参数 + 网关列表编辑 + **仅画画网关**检测（`config-check`）。 |
| WebUI **插件 → MAA远控 / 牛牛唱歌** | 各插件全部配置项。 |

通用配置段写入的仍是各插件对应的大写 `.env` 键，保存后会热重载对应插件。

## 命令权限

| 命令 ID | 默认等级 |
| :--- | :--- |
| `connectivity.probe` | everyone |

可在 WebUI「通用配置 → 命令权限」或环境变量 `PALLAS_COMMAND_PERMISSION_OVERRIDES` 中覆盖。

## 探测说明

- **画画**：对各网关 GET `models` / `v1/models`（与插件内 `gateway_probe` 一致，支持 httpx / curl-cffi）。
- **MAA**：对解析后的完整 URL 发 POST JSON（空 `user` / `device`）；HTTP 2xx 视为可达。
- **唱歌**：`sing_enable=false` 时仅提示未启用；启用后 GET AI 服务的 `/health`（Pallas-Bot-AI 默认可用）。不对 `request_endpoint` / `play_endpoint` 做探测：前者仅 POST `…/request/{id}`，后者 GET 会真实触发播放任务。

## 相关文档

- [牛牛画画](../pallas_image/README.md)
- [MAA 远控](../maa/README.md)
- [牛牛唱歌](../sing/README.md)
- [WebUI 通用配置](../../common/webui/README.md)

实现见 [`src/plugins/connectivity/`](../../../src/plugins/connectivity/)、[`src/common/service_probe/`](../../../src/common/service_probe/)、[`src/common/webui/service_gateways_section.py`](../../../src/common/webui/service_gateways_section.py)。
