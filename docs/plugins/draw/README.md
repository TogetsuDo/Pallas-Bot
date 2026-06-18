# draw（牛牛画画）

> **官方扩展**：[`pallas-plugin-draw`](https://github.com/TogetsuDo/pallas-plugin-draw)（`uv sync --extra plugins-draw`）

群内按文字描述生图，或带参考图改图；默认走 AI 服务 `image.generate`，`plugin_runtime` 仅兼容兜底。

## 用户命令

| 口令 | 场景 | 说明 |
| --- | --- | --- |
| 牛牛画画 … | 群内 | 生图或改图（可附图/回复图） |

## 命令权限

| 命令 ID | 默认等级 |
| --- | --- |
| `draw.draw` | everyone |

## 配置

WebUI **插件 → 牛牛画画** 或 **服务网关 / 连通性**；字段前缀 `pallas_image_*`。

## 排障

| 现象 | 处理 |
| --- | --- |
| 失败 | 看返回提示；发 **牛牛连通** 测画画服务 |
| 次数用尽 | 等待重置或调配额 |

## 实现

源码在扩展仓 [`src/pallas_plugin_draw/`](https://github.com/TogetsuDo/pallas-plugin-draw/tree/main/src/pallas_plugin_draw)。  
主仓仅保留内核槽位（`import_plugin_submodule`、`ai_callback` hook、`platform/media/draw_reference`）。
