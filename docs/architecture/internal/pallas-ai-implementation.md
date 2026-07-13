# Pallas AI 实施与联调

> **目标态与契约**见 **[pallas-final-ai-shape.md](pallas-final-ai-shape.md)**。  
> 本文记录 **集成里程碑（L1）**、**形态收敛（L2）** 与 E2E 签收；**不等于** final 全文已达成。  
> **当前范围**：主仓 `src/` + 双仓联调；**`local/plugins` 站点覆盖暂不纳入 L2 排期**（见 §4 说明）。

## 1. 总原则

1. **先统一运行时边界，再扩 AI 功能** — 不在各插件内各自增强 provider/health/task。
2. **主仓 = 产品策略，AI 仓 = 能力执行** — 触发、权限、冷却、persona 在主仓；routing、queue、熔断在 AI 仓。
3. **先收口 draw，再带动 sing 等媒体** — draw 最易在插件层长歪，是第一收口对象。
4. **按 capability 设计 AI 仓** — 抽象面向 `llm` / `image` / `media task` runtime，不是「给某插件补接口」。

## 2. 完成度分层（与 final 对照）

| 层级 | 含义 | 对应 final | 状态（2026-06） |
|------|------|------------|-----------------|
| **L1 集成可用** | 双栈可切换、callback、probe/WebUI、§5 E2E 签收 | §4 契约 + 联调路径 | **Phase 0–6 已完成** |
| **L2 形态收敛** | 薄插件、默认 AI runtime、统一 capability 信封、memory infra | §3 统一运行时 + §5 插件终态 + §2.4 memory | **Phase 7 进行中** |

**勿混淆**：L1 完成表示「能按 final 契约联调、生产站点可跑」；L2 才接近 final 的「插件不再私有编排、语义全面统一」。

### 2.1 集成里程碑（L1 · Phase 0–6）

| Phase | 目标 | L1 状态 |
|-------|------|---------|
| **0** 口径统一 | AI 仓 = 统一 Runtime，非「可选组件集合」 | 已完成 |
| **1** draw 插件止血 | 抽出 orchestrator、backend state、diagnostics | 已完成（**业务代码在 `pallas-plugin-draw` 扩展仓**） |
| **2** AI Image Runtime MVP | 熔断、`POST /api/images/generate`、health | 已落地 |
| **3** draw 双栈 | `plugin_runtime` / `ai_service_runtime` 可切换 | 已落地（bundled **默认** `ai_service_runtime`；`plugin_runtime` 作兜底） |
| **4** 统一语义（probe/WebUI） | draw/sing 运行态读 AI `/health`；probe 含 `failure_class` / circuit | **L1 已落地**（LLM/sing 仍有多条 legacy API 路径，**L2 收口**） |
| **5** 媒体任务平台化 | `/api/media/tasks`、draw 慢路径 callback、sing `media_task` | 已落地；draw callback **hook 化**（内核见 §4） |
| **6** Bot 控制面 | WebUI 聚合 LLM/image/sing 运行态、网关 probe | 已落地 |

### 2.2 Draw 媒体路径（L1 已验收）

- **快路径**：无参考图、预预算内 → `POST /api/images/generate` 同步出图  
- **慢路径**：有参考图或长超时 → `POST /api/media/tasks` → Celery → Bot callback  
- **参考图**：AI 仓本地下载 + `/images/edits`（见 final §4.3）

### 2.3 形态收敛（L2 · Phase 7）

与 [pallas-final-ai-shape.md](pallas-final-ai-shape.md) §3 / §5 / §2.4 对齐；**不含 local 插件瘦身**。

| # | 项 | 终态要点 | 状态 |
|---|-----|----------|------|
| 7.1 | **draw 扩展薄化** | 官方扩展 [`pallas-plugin-draw`](https://github.com/TogetsuDo/pallas-plugin-draw)：`ai_execute` / `plugin_gateway` 分路径；AI 路径不 Bot 侧下载参考图 | 已落地（主仓 `src/plugins/draw` 已移除） |
| 7.2 | **默认 AI runtime** | 扩展默认 `ai_service_runtime`；`plugin_runtime` 仅紧急兜底 | 已落地（扩展仓 `4.0.2`） |
| 7.3 | **LLM legacy 收口** | Bot→AI 全面 capability 信封；弃用或隔离 `/ollama/*` 等 path-only 路径 | 已落地（统一 chat capability 外壳；legacy/ollama 弃用日志；AI 端点支持 envelope 解包） |
| 7.4 | **sing 统一 media task** | 默认 `media_task`；legacy  singing HTTP 仅兼容期 | 已落地（bundled 默认） |
| 7.5 | **插件侧熔断去重** | draw/sing 以 AI `/health` + probe 为事实源；削减插件内 parallel circuit 状态机 | 已落地（probe 与 draw 扩展只读 AI health 缓存；LLM probe 本就只读 `/health`） |
| 7.6 | **memory infra** | 运行时 session / task state 在 AI 仓；产品记忆策略仍在 Bot（final §2.4） | 已落地（Bot：hybrid 检索 + embedding 缓存、启发式 auto_episode、`memory.search`/`memory.save` tools、`data/pallas_knowledge` ingest；见 [llm-and-ai.md](../../maintainer/operate/llm-and-ai.md)） |
| 7.7 | **strict 门禁（可选）** | `PALLAS_DUPLICATE_PREFIX_STRICT=true` 等硬失败策略 | 已落地（实现见 `duplicate_prefix_check`；生产推荐见 [站点定制 §strict](site-customization-and-updates.md)） |

**L2 完成标志**（摘自 final 意图）：

- 新媒体能力 **从 AI Runtime capability 接入**，不从插件私有编排起步  
- 运维在 WebUI 一眼看到 LLM / image / sing queue 与 degraded，**不必**分别猜三套插件内状态  

## 3. 仓库职责（实施时对照）

**留在 Pallas-Bot**：persona/style 业务、ingress/分片、cmd_perm、插件入口、callback 消费与群消息、WebUI 聚合、平台侧参考图 URL 提取。

**进 Pallas-Bot-AI**：provider 差异、backend 路由与熔断、image/sing 上游调用、media task 队列、runtime metrics、会话/运行时记忆执行。

**进官方扩展仓**：`pallas-plugin-draw` 的口令 handler、AI/plugin 执行路径、插件配置默认值、`startup`/`media_callback` 注册。

**明确不做**：在 draw 插件内继续堆供应商细节；为每种媒体各自发明 task 状态机；把 persona 最终解释权放进 AI 仓。

> **bundled `src/plugins/draw`**：4.0 起已迁出；slim 通过插件商店、`uv run pallas ext install pallas-plugin-draw` 或 `local/plugins/draw` 加载。**L2 draw 形态收敛在扩展仓维护**。

## 4. 内核槽位 API（`src/`，与 local 无关）

> **范围说明**：本节验收 **主仓内核 + bundled 插件** 的槽位机制。  
> **`local/plugins` 整包覆盖**仍按 [site-customization-and-updates.md](../site-customization-and-updates.md) 运维，**不纳入 Phase 7 L2 排期**（站点自行跟进即可）。

### 4.1 问题

| 机制 | 决定什么 |
|------|----------|
| **plugin_loader** | NoneBot 注册哪个包的 matcher |
| **内核 import** | callback、WebUI、probe 读哪份 Python 模块 |

整包 override 时若内核仍 hardcode `src.plugins.draw.*`，会出现：**命令走 local，收尾走 src**；或 import 拉起主仓 `__init__.py` → **重复 matcher**。

### 4.2 目标 API（主仓）

| API | 用途 |
|-----|------|
| `import_plugin_submodule(plugin_id, submodule)` | 优先 loaded 包，否则 `src.plugins.<id>.<sub>` |
| `register_media_task_hooks(task_type, on_success, on_failure)` | callback 扣次/归档/熔断计数回到 loaded 插件 |
| 启动 `duplicate_prefix_check` | 同一 prefix 多 module → ERROR（可 strict 抛错） |

Task metadata 最小约定：`plugin`、`task_type`、`count_usage`、`metadata`（插件扩展，runner 不解释）。

### 4.3 内核收敛进度（`src/`）

| 项 | 状态 |
|----|------|
| `ai_callback.runner` hook 化 + 扩展 `draw/startup.py` | 已落地 |
| probe / draft / WebUI 网关段 `import_plugin_submodule` | 已落地 |
| duplicate prefix 启动自检 | 已落地 |
| 参考图 Bot 侧统一 resolve（`platform/media/reference_resolve`） | 已落地 |
| draw 参考图下载选项（`platform/media/draw_reference`） | 已落地 |
| `delivery.py` / `handlers.py` / `dream` 去 hardcode | 已落地 |
| bundled draw `__init__.py` 薄化 | 已迁出（扩展仓自载 `draw` + `startup`） |
| `pb_webui` draw 配置检测走 `probe_image_gateways` | 已落地 |

### 4.4 local 站点（暂缓纳入 L2）

- 整包 override 时须避免 `import src.plugins.<同名>` 拉活主仓 `__init__.py`（会重复 matcher）  
- 内核 hook 已就绪；**local 包是否瘦身由站点维护者决定**，不在当前 Phase 7 主仓任务内  
- 细节见 [site-customization-and-updates.md](../site-customization-and-updates.md)  

## 5. 端到端联调 Checklist

### 5.1 环境

| 项 | 要求 |
|----|------|
| **Pallas-Bot** | `dev`，media task callback + health 聚合 |
| **Pallas-Bot-AI** | `feat/4.0`，`/api/media/tasks` + callback |
| **Pallas-Bot-WebUI** | `feat/4.0`，AI 配置 Hub + 运行态页 |
| **进程** | Bot、AI API、AI Celery（sing 必须）、可选 Redis |

重启 Bot 后对 `/pallas/` **硬刷新**，确认 `console-version.json` 与 WebUI 分支一致。

### 5.2 配置

**AI 仓**：`IMAGE_ENABLED=true`，`CALLBACK_HOST` / `CALLBACK_PORT` 指向 Bot 可达地址。

**Bot（webui.json）**：

| 键 | 联调值 |
|----|--------|
| `pallas_image_runtime_mode` | `ai_service_runtime`（扩展默认） |
| `pallas_image_ai_runtime_fallback_to_plugin` | `false`（扩展默认；需兜底时在 WebUI 开启） |
| `sing_enable` | `true` |
| `sing_runtime_mode` | `media_task`（bundled 默认；legacy 仅兼容） |

### 5.3 Draw

| # | 场景 | 预期 |
|---|------|------|
| 快路径 | 纯文生图、无参考图 | 同步出图，`/api/images/generate` |
| 3.1 | 带参考图 | 先回「欢呼吧！」 |
| 3.2 | AI 日志 | task accepted → callback success；edits 上游 |
| 3.3 | 群消息 | 异步收到图片；参考图影响结果 |
| 3.4 | Bot | 无长时间轮询 task |

### 5.4 Sing

- `legacy` → `牛牛唱歌` → callback 分段语音  
- `media_task` → `POST /api/media/tasks` → Celery → callback（**2026-06-18 群测签收**：铁花飞、Life is like a boat；callback 语音经 `MessageSegment.record`）  
- Worker 崩溃：task failed，Bot 应收 failed callback  

### 5.5 WebUI（AI配置 → 运行态总览）

刷新无报错；媒体任务分 capability chip；draw/sing 熔断与 AI `/health` 一致；服务网关 probe 含 runtime 字段。

### 5.6 API 抽测

```bash
curl -s http://<AI>/health | jq '.media_tasks, .llm, .image'
curl -s http://<AI>/api/media/tasks/runtime | jq .
```

### 5.7 自动化测试

```bash
# Bot（内核 + 需已装 pallas-plugin-draw 的集成测）
uv run pytest tests/features/llm/test_ai_health_parse.py \
  tests/features/service_gateways/test_probe_collect.py \
  tests/platform/test_ai_callback_runner.py \
  tests/platform/test_media_task_hooks.py \
  tests/platform/test_duplicate_prefix_check.py -q

# draw 扩展仓
uv run pytest tests/ -q
```

# AI
uv run pytest tests/test_api_media_tasks.py \
  tests/test_media_task_callback_service.py \
  tests/test_media_task_runtime_sing.py \
  tests/test_image_runtime_reference.py \
  tests/test_api_images.py -q
```

### 5.8 签收清单

**L1 · 集成（Phase 0–6）**

- [x] Draw 慢路径 callback 全链路（含参考图 edits）  
- [x] Draw 快路径仍可用  
- [x] Sing legacy + media_task 各一轮  
- [x] WebUI 运行态信息完整  
- [x] 两仓自动化测试全绿（见 §5.7；CI 全量以仓库 workflow 为准）  

**L2 · 形态收敛（Phase 7）**

- [x] draw 扩展薄化（`pallas-plugin-draw` · §2.3 · 7.1）  
- [x] 扩展默认 `ai_service_runtime`（§2.3 · 7.2）  
- [x] LLM/sing capability 信封与 legacy 路径收口（§2.3 · 7.3–7.4 部分：sing 默认 `media_task` 已落地）  
- [x] 插件侧熔断与 AI health 单一事实源（§2.3 · 7.5）  
- [x] memory infra（§2.3 · 7.6）  

## 6. 相关文档

- **[pallas-final-ai-shape.md](pallas-final-ai-shape.md)** — 终态架构与 API 契约  
- [site-customization-and-updates.md](../site-customization-and-updates.md) — local 插件  
- [plugin-convention.md](../plugin-convention.md) — 插件目录约定  
