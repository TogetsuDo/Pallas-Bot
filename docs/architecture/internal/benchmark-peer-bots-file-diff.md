# Pallas 4.0 前辈对标 — 逐文件 Diff 补充

> **主文档**：[benchmark-peer-bots-roadmap.md](benchmark-peer-bots-roadmap.md)  
> **版本**：2026-06-24  
> **路径根**：Pallas 主仓 + `/tmp` 下对标仓

本文按 **WebUI / LLM / 架构** 三域列出可操作的文件级对照，供实施时直接打开 diff。

---

## 1. WebUI 逐文件对照

> Pallas 前端源码在独立仓 **Pallas-Bot-WebUI**；主仓 `packages/pb_webui/` 为 API + 静态挂载。

### 1.1 Auth

| 能力域 | Pallas 文件 | 前辈参考文件 | 差距 | 建议动作 | 优先级 |
|--------|-------------|--------------|------|----------|--------|
| 口令与会话 | `pallas/console/webui/console_login.py`<br>`packages/pb_webui/public.py`<br>`packages/pb_webui/extended_api.py` | GsUID: `gsuid_core/webconsole/auth_api.py`<br>MaiBot: `src/webui/core/auth.py`<br>AstrBot: `astrbot/dashboard/services/auth_service.py` | 单用户口令；无 TOTP/API Key | setup 引导；中期 API Key scope | P1 |
| 传输安全 | `console_login.py` | GsUID: `gsuid_hub/src/lib/authCrypto.ts` | 无 ECDH 加密登录体 | 可选 ECDH + HTTPS 提示 | P2 |
| 首次运行 | `console_login.py` | MaiBot: `src/webui/routes.py` `/setup/*`<br>AstrBot: `openspec/openapi-v1.yaml` `/auth/setup*` | 无多步 setup | OPT-WEB-003 | P0 |
| 前端鉴权 | `Pallas-Bot-WebUI/src/api/http.ts` | GsUID: `pages/Login.tsx` | 401 整页跳转 | 可选内嵌 Login 路由 | P3 |

### 1.2 OpenAPI / API Client

| 能力域 | Pallas 文件 | 前辈参考文件 | 差距 | 建议动作 | 优先级 |
|--------|-------------|--------------|------|----------|--------|
| 机器契约 | `packages/pb_webui/extended_api.py` | AstrBot: `openspec/openapi-v1.yaml`<br>GsUID: `webconsole/docs/*.md` | 无独立 OpenAPI YAML | OPT-WEB-001 | P0 |
| 类型客户端 | `Pallas-Bot-WebUI/src/api/consoleApi.ts` | AstrBot: `dashboard/src/api/generated/openapi-v1/` | 手写易漂移 | OPT-WEB-002 | P0 |
| 外部 Open API | `extended_api.py` | AstrBot: `services/open_api_service.py` | 无第三方 API Key | OPT-WEB-024 | P2 |
| 错误语义 | `http.ts` | AstrBot: `responses.py` | 响应格式不统一 | OPT-WEB-013 | P1 |

### 1.3 Plugin Config UI

| 能力域 | Pallas 文件 | 前辈参考文件 | 差距 | 建议动作 | 优先级 |
|--------|-------------|--------------|------|----------|--------|
| Schema 推导 | `pallas/console/webui/field_meta.py`<br>`field_labels.py` | GsUID: `webconsole/docs/39-plugin-config-types.md` | 类型集偏少 | 扩展 json_schema_extra 约定 | P2 |
| 读写 API | `plugin_api.py`<br>`plugin_config.py` | MaiBot: `routers/plugin/config_routes.py` | 无 TOML 双模式 | OPT-WEB-014 | P1 |
| 前端编辑器 | `ConfigFieldRenderer.vue`<br>`PluginConfigWorkspace.vue` | GsUID: `DynamicConfigPanel.tsx` | 深层嵌套弱 | OPT-WEB-011 | P1 |
| 插件自定义页 | — | AstrBot: `services/plugin_page_service.py` | 无 plugin page | OPT-WEB-023 | P2 |

### 1.4 Plugin Store

| 能力域 | Pallas 文件 | 前辈参考文件 | 差距 | 建议动作 | 优先级 |
|--------|-------------|--------------|------|----------|--------|
| 官方扩展 | `plugin_registry.py`<br>`extension_install.py` | AstrBot: `services/plugin_service.py` | 缺安装进度 SSE | OPT-ARCH-011 | P1 |
| 社区索引 | `community_plugin_index.py` | Zhenxun: `api/tabs/plugin_manage/store.py` | 元数据可扩展 | stars/last_commit | P2 |
| 商店 UI | `PluginStorePage.vue` | MaiBot: `MarketplaceTab.tsx` | 缺镜像源 UI | 参考 `plugin-mirrors.tsx` | P3 |

### 1.5 AI Config Pages

| 能力域 | Pallas 文件 | 前辈参考文件 | 差距 | 建议动作 | 优先级 |
|--------|-------------|--------------|------|----------|--------|
| 配置分段 | `env_sections.py`<br>`extended_api.py` `/common-config/llm/*` | GsUID: `pages/AIConfig/`（15+ section） | 入口偏碎 | 对齐独立路由 + 侧栏 | P2 |
| Provider | `AiConfigProviderSection.vue`<br>`useLlmProviders.ts` | GsUID: `provider_config_api.py` | 缺探测 wizard | OPT-WEB-004 | P0 |
| 人格/记忆 | `AiConfigPersonaSection.vue`<br>`AiHistoryPage.vue` | GsUID: `persona_api.py`<br>MaiBot: `routes/resource/knowledge-base/` | 缺 Kanban/Skills 专页 | 按产品择项 | P2 |
| 运行态一屏 | 分散多页 | GsUID: `Dashboard.tsx`<br>AstrBot: `api/stats.py` | 无聚合页 | OPT-LLM-004 | P0 |

### 1.6 Runtime Monitoring

| 能力域 | Pallas 文件 | 前辈参考文件 | 差距 | 建议动作 | 优先级 |
|--------|-------------|--------------|------|----------|--------|
| 实时指标 | `console_live_stats.py`<br>`daily_stats_store.py` | GsUID: `dashboard_api.py` | 无统一健康分 | Runtime Overview | P0 |
| 分片/入口 | `extended_api.py` `/shard-observability` | — | **Pallas 领先** | OpenAPI 暴露 | P2 |
| 链路追踪 | `AiHistoryPage.vue` | GsUID: `TracesPage.tsx` | 缺全局 trace UI | OPT-LLM-012 | P1 |
| 推理监控 | — | MaiBot: `maisaka-monitor.tsx` | 无实时推理可视化 | P2 可选 | P3 |

### 1.7 Logs / SSE

| 能力域 | Pallas 文件 | 前辈参考文件 | 差距 | 建议动作 | 优先级 |
|--------|-------------|--------------|------|----------|--------|
| 历史拉取 | `extended_api.py` `GET /logs` | GsUID: `logs_api.py` | 级别持久化弱 | visible_levels API | P2 |
| 实时流 | `GET /logs/stream`<br>`LogsPage.vue` | AstrBot: `api/logs.py` | 无 Last-Event-ID | OPT-WEB-012 | P1 |
| WebSocket | — | MaiBot: `logs_ws.py` | 仅 SSE | OPT-WEB-022 | P2 |

### 1.8 Setup Wizard

| 能力域 | Pallas 文件 | 前辈参考文件 | 差距 | 建议动作 | 优先级 |
|--------|-------------|--------------|------|----------|--------|
| 多步向导 | `login_page.py` | MaiBot: `routes/setup/*.tsx` | 无向导 | OPT-WEB-003 | P0 |
| 完成状态 | — | MaiBot: `is_first_setup()` | 无 setup_completed | setup_state.json | P0 |
| AI 体检 | — | GsUID: `ai_wizard_api.py` | 无 | OPT-WEB-004 | P0 |

### 1.9 i18n

| 能力域 | Pallas 文件 | 前辈参考文件 | 差距 | 建议动作 | 优先级 |
|--------|-------------|--------------|------|----------|--------|
| 前端 i18n | 组件内中文 | GsUID: `i18n/locales/`（129 文件） | 无多语言 | OPT-WEB-020 | P2 |
| 字段标签 | `field_labels.py` | GsUID API title/desc | 后端中文写死 | Accept-Language 或前端映射 | P3 |

### 1.10 Mobile / Narrow（≤560px）

| 能力域 | Pallas 文件 | 前辈参考文件 | 差距 | 建议动作 | 优先级 |
|--------|-------------|--------------|------|----------|--------|
| 全局断点 | `Pallas-Bot-WebUI/src/styles/app.css` | AGENTS 560px 规范 | **Pallas 最系统** | 保持 | — |
| 宽表格 | `CmdPermMatrix.vue` | MaiBot: `overflow-x-auto` | 窄屏挤 | 卡片列表视图 | P0 |
| Hub 布局 | `console-hub.css` | — | 长表单溢出 | OPT-WEB-005 | P0 |

### 1.11 WebUI 路径速查

| 项目 | 后端 | 前端 | 契约 |
|------|------|------|------|
| Pallas | `packages/pb_webui/`<br>`pallas/console/webui/` | `Pallas-Bot-WebUI/src/` | `extended_api.py` 局部 schema |
| AstrBot | `astrbot/dashboard/` | `dashboard/src/` | `openspec/openapi-v1.yaml` |
| GsUID | `gsuid_core/webconsole/` | `gsuid_hub/src/` | `webconsole/docs/` + `lib/api.ts` |
| Zhenxun | `zhenxun/builtin_plugins/web_ui/` | 无（dist 外链） | REST + Result |
| MaiBot | `src/webui/` | `dashboard/src/` | Pydantic + `@/lib/http` |

---

## 2. LLM / AI 逐文件对照

### 2.1 能力总表

| 能力 | Pallas | 前辈 | 差距 | 建议 ID | 优先级 |
|------|--------|------|------|---------|--------|
| Provider 抽象 | `pallas/product/llm/client.py`<br>`config.py`<br>`model_admin.py` | AstrBot: `provider/manager.py`<br>Zhenxun: `adapters/factory.py` | Bot 内无 adapter 注册表 | Sidecar 契约文档 | P2 |
| Routing/Fallback | `task_routing.py`<br>`fallback.py`<br>`kernel/generation.py` | GsUID: `ai_router.py`<br>MaiBot: `service_task_resolver.py` | 无 provider failover | OPT-LLM-013 | P1 |
| Session/Memory | `session_store.py`<br>`memory/retrieve.py`（关键词） | AstrBot: `conversation_mgr.py`<br>MaiBot: `A_memorix/`<br>GsUID: `memory/` | 无向量/episode | OPT-LLM-003/010 | P0/P1 |
| RAG/Knowledge | `knowledge/declare.py`<br>`knowledge/retrieve.py` | AstrBot: `knowledge_base/kb_mgr.py`<br>GsUID: `rag/knowledge.py` | 无 ingest/hybrid | OPT-LLM-010 | P1 |
| Tools/MCP | `tools/registry.py`<br>`tools/mcp_bootstrap.py` | AstrBot: `agent/mcp_client.py`<br>GsUID: `mcp/client.py` | 仅 stdio MCP | OPT-LLM-014 | P2 |
| Agent Loop | `kernel/decision.py`（规划） | AstrBot: `tool_loop_agent_runner.py`<br>GsUID: `gs_agent.py`<br>MaiBot: `reasoning_engine.py` | loop 在 AI 服务黑盒 | OPT-LLM-012 | P1 |
| Streaming | `client.py` callback | AstrBot: `text_chat_stream` | 无 stream | OPT-LLM-020 | P2 |
| Persona | `persona/*`（34 文件） | GsUID: `persona/`<br>MaiBot: `person_profile.py` | **Pallas 领先** | OPT-LLM-024 | P3 |
| Timing/Proactive | `repeater/opportunity_gate.py` | GsUID: `heartbeat/`<br>MaiBot: `timing_gate` | 无主动心跳 | OPT-LLM-011/023 | P1/P2 |
| Health/Circuit | `startup_probe.py`<br>`ai_health_parse.py` | AstrBot: `request_retry.py` | LLM 无 circuit | OPT-LLM-002/013 | P0 |
| Callback/Async | `client.submit_chat_task`<br>`ai_callback/` | GsUID: `handle_ai.py` 队列 | callback 调试复杂 | OPT-LLM-021 | P2 |

### 2.2 子系统路径映射

| 子系统 | Pallas | AstrBot | GsUID | MaiBot | Zhenxun |
|--------|--------|---------|-------|--------|---------|
| 入口 | `packages/llm_chat/chat_message.py`<br>`packages/repeater/handlers/message.py` | plugin 层 | `handle_ai.py` | `reasoning_engine.py` | `api.py` |
| 客户端 | `llm/client.py` | `provider/manager.py` | `gs_agent.py` | `services/llm_service.py` | `core.py` |
| 会话 | `llm/session_store.py` | `conversation_mgr.py` | `session_registry.py` | `context/history.py` | `session.py` |
| 记忆 | `llm/memory/*` | `knowledge_base/*` | `memory/*` | `A_memorix/*` | `memory.py` |
| 工具 | `llm/tools/*` | `agent/mcp_client.py` | `mcp/*` | `builtin_tool/*` | `tools.py` |
| Agent | `llm/kernel/*` | `agent/runners/` | `gs_agent.py` | `chat_loop_service.py` | `session.py` |
| Persona | `persona/*` | persona_mgr | `persona/*` | `person_profile` | — |
| 主动 | `repeater/opportunity_gate.py` | — | `heartbeat/*` | `runtime.py` | — |

### 2.3 L2 收口文件锚点（Phase 7）

| 项 | Pallas 关键文件 | AI 仓应对文件（概念） |
|----|-----------------|----------------------|
| 7.3 capability 信封 | `pallas/product/llm/client.py` | 统一 `/api/v1/chat/completions` 外壳 |
| 7.5 熔断去重 | `packages/repeater/llm_pipeline.py`<br>`pallas/product/service_gateways/` | 只读 `/health` |
| 7.6 memory infra | `llm/memory/*`<br>`llm/session_store.py` | task state / runtime memory |
| 7.7 strict | `pallas/core/platform/bot_runtime/` duplicate check | 启动门禁 |

---

## 3. 架构逐文件对照

### 3.1 能力总表

| 领域 | Pallas | 前辈 | 差距 | 建议 ID | 优先级 |
|------|--------|------|------|---------|--------|
| 插件加载 | `plugin_loader.py`<br>`plugin_matrix.py` | AstrBot: `star_manager.py`<br>GsUID: `server.py`<br>MaiBot: `plugin_loader.py` | 弱于运行时安装/子进程隔离 | OPT-ARCH-011 | P1 |
| 生命周期 | `runtime/boot.py` | AstrBot: `core_lifecycle.py`<br>MaiBot: `main.py` | 缺单一门面 | OPT-ARCH-020 | P2 |
| 消息管道 | `platform/ingress/*` | AstrBot: `pipeline/`<br>Zhenxun: `auth_checker.py` | **Pallas ingress 领先** | OPT-ARCH-012 | P2 |
| 权限 | `pallas/core/perm/*` | Zhenxun: `hooks/auth/`<br>GsUID: `sv.py` pm | 缺经济/群开关一体 | P2 | P2 |
| 热重载 | `plugin_reload/reload_ops.py` | GsUID: `reload_plugin.py`<br>MaiBot: `supervisor.py` | 副作用清理清单弱 | OPT-ARCH-010 | P1 |
| 分片 | `platform/shard/*`（30+ 文件） | — | **显著领先** | 维护+测试 | P3 |
| 配置 | `foundation/config/repo_settings.py` | MaiBot: `config.py` FileWatcher<br>Zhenxun: `plugins2config.yaml` | 监视热载可借鉴 | P2 | P2 |
| 扩展商店 | `plugin_registry.py`<br>`community_plugin_*` | Zhenxun: `plugin_store/`<br>MaiBot: `webui/routers/plugin/` | 社区 UX 弱 | OPT-ARCH-011 | P1 |
| Hub/Worker | `roles.py`<br>`bot_hub.py` / `bot_worker.py` | MaiBot Host+Runner（不同维度） | **业务向 hub 最完整** | OPT-DOC-010 | P2 |
| 测试 | `tests/**`（~394 文件） | AstrBot ~108 | **领先** | 补 install E2E | P2 |

### 3.2 框架路径速查

| 框架 | 插件 | 生命周期 | 管道 | 权限 | 热重载 | 分片 | 配置 | 商店 |
|------|------|----------|------|------|--------|------|------|------|
| **Pallas** | `bot_runtime/plugin_loader.py` | `runtime/boot.py` | `platform/ingress/` | `core/perm/` | `plugin_reload/` | `platform/shard/` | `foundation/config/repo_settings.py` | `console/webui/plugin_registry.py` |
| **AstrBot** | `star/star_manager.py` | `core_lifecycle.py` | `pipeline/` | `star/filter/permission.py` | watchfiles | — | `config/` | `star/updator.py` |
| **GsUID** | `server.py`, `sv.py` | server hooks | `handler.py` | `sv.py` pm | `plugins_update/reload_plugin.py` | `pool.py` | `config.py` | `webconsole/plugins_api.py` |
| **MaiBot** | `plugin_runtime/runner/plugin_loader.py` | `main.py` | `platform_io/manager.py` | `host/authorization.py` | `supervisor.py` | — | `config/config.py` | `webui/routers/plugin/` |
| **Zhenxun** | `init/init_plugin.py` | `cli.py` | `hooks/auth_checker.py` | `hooks/auth/` | `reload_setting.py` | cli worker | `configs/config.py` | `plugin_store/` |

### 3.3 Pallas 独有文件（不必对标删除）

| 文件/目录 | 说明 |
|-----------|------|
| `pallas/core/platform/ingress/gate.py` | 联邦/分片 claim、舰队 @ 过滤 |
| `pallas/core/platform/ingress/matcher_dispatch.py` | patch handle_event |
| `pallas/core/platform/shard/coord/ai_callback_forward.py` | 分片 AI callback 转发 |
| `pallas/product/corpus/` | 语料联邦底盘 |
| `pallas/product/persona/affect_kernel.py` | 牛格情感内核 |
| `packages/repeater/opportunity_gate.py` | 接话时机门控 |

---

## 4. 建议 diff 工作流（维护者）

1. 从主文档清单取 **OPT-ID**。
2. 在本表找到 **Pallas 文件** 与 **前辈参考文件**。
3. 本地执行：`diff -ru` 或 IDE compare（路径见上表）。
4. 实施时优先 **移植模式/契约**，避免复制前辈插件体系（SV/Star）。
5. 完成后更新 Notion 任务状态，并在主文档修订记录注明。

---

## 6. 深度 diff 节选（关键模块）

> 以下为 2026-06-24 实仓扫描的结构对比，供评审时快速感知「体量差」与「职责差」。

### 6.1 WebUI API 面

| 指标 | Pallas | AstrBot | GsUID hub |
|------|--------|---------|-----------|
| 后端 API 体量 | `extended_api.py` **7634 行**（单文件聚合） | `openapi-v1.yaml` **6042 行**（契约先行） | `lib/api.ts` **4321 行**（前端 client） |
| 契约方式 | FastAPI 局部 `include_in_schema` | OpenAPI → codegen `@hey-api` | 40+ 篇 `webconsole/docs/*.md` + 手写 client |
| **diff 结论** | 功能面已不输前辈，但 **契约外置与 codegen 缺失** 是 drift 主因 | — | DynamicConfigPanel 是配置 UX 标杆 |

**Pallas 应对**：OPT-WEB-001/002 — 从 `extended_api.py` 导出 OpenAPI，WebUI 核心域改生成 client；长期可按域拆 router（参考 AstrBot `dashboard/services/*`）。

### 6.2 LLM 客户端层

| 指标 | Pallas `llm/client.py` | AstrBot `provider/manager.py` | GsUID `gs_agent.py` | 真寻 `llm/api.py` |
|------|------------------------|-------------------------------|---------------------|-------------------|
| 行数 | **296** | **894** | **1625** | **407** |
| 职责 | HTTP submit + callback；**无进程内 adapter** | 多 provider 注册/切换/初始化 | pydantic-ai agent + 工具池 + history | 无状态 chat/generate/embed |
| 入口函数 | `submit_chat_task()` | `ProviderManager.initialize()` | `GsCoreAIAgent` | `chat()`, `generate_structured()` |

**diff 结论**：

- Pallas **刻意薄化** — 符合双仓契约；缺口在 **7.3 capability 信封**尚未全面替换 legacy URL（`client.py` 内仍有多路径 submit）。
- 真寻 `api.py` 是 Bot 内内核服务的良好参照：社区插件应走 `pallas.api.llm` 而非直调 `client.py`（OPT-ARCH-001）。

### 6.3 消息管道 / Ingress

| 指标 | Pallas | AstrBot |
|------|--------|---------|
| 核心文件 | `ingress/gate.py` **273 行** + `matcher_dispatch.py` + `route_index.py` + `dispatch_lanes.py` | `pipeline/scheduler.py` **96 行** + 25 个 stage 文件 |
| 模型 | **L1 gate → L2 dispatch → L3 budget**（分片/多牛一等公民） | **洋葱 Stage**（唤醒→限流→安全→Agent→装饰→发送） |
| 文件数 | `platform/shard/` **55 个 py** | pipeline 目录 **25 个 py** |

**diff 结论**：

- Pallas ingress **广度领先**（分片、联邦、fanout）；AstrBot pipeline **阶段抽象更清晰**。
- 建议：不照搬 Stage 框架，在 `central-ingress-dispatch.md` 补「与 AstrBot stage 概念对照表」（OPT-ARCH-012）；横切 concern（scrub/rate-limit）文档化归属。

### 6.4 Persona（Pallas 优势域）

| 指标 | Pallas `persona/` | GsUID `persona/` | MaiBot |
|------|-------------------|------------------|--------|
| 文件规模 | **34 文件**（affect、profiler、scorer…） | ~10 文件（prompt + mood） | `person_profile.py` + prompt i18n |
| 与 LLM 桥接 | `llm/persona_context.py` + `compile_persona_prompt.py` | `ai_core/persona/` | planner 注入 |

**diff 结论**：**不必对标补齐**；优先 OPT-LLM-024 导出 schema，便于 WebUI 与跨站复用。

### 6.5 插件加载

| 框架 | 核心文件 | 特色 |
|------|----------|------|
| Pallas | `plugin_loader.py` + `plugin_matrix.py` | hub/worker 角色白名单、`activation_policy` |
| AstrBot | `star_manager.py` | pip 依赖智能装、watchfiles 热更、版本约束 |
| GsUID | `server.py` `load_plugins()` | `_module_cache`、Git 更新一体化 |
| MaiBot | `plugin_runtime/runner/plugin_loader.py` | `_manifest.json`、拓扑排序、**子进程** |
| 真寻 | `init_plugin.py` | 元数据 → DB + `PluginExtraData` 驱动 |

**diff 结论**：Pallas 治理最强；向 AstrBot/MaiBot 借鉴 **安装进度 SSE**（OPT-ARCH-011），不向 MaiBot 借鉴子进程（OPT-ARCH-030 backlog）。

### 6.6 推荐 diff 命令（本地）

```bash
# WebUI 契约
diff -u <(rg -l 'router\.(get|post)' /root/Projects/Bots/Pallas-Bot/packages/pb_webui/extended_api.py | head -1) \
  /tmp/AstrBot/openspec/openapi-v1.yaml  # 粗对比需配合 OpenAPI 导出后

# LLM 客户端
diff -u /root/Projects/Bots/Pallas-Bot/pallas/product/llm/client.py \
  /tmp/zhenxun_bot/zhenxun/services/llm/api.py

# Ingress vs Pipeline
ls /root/Projects/Bots/Pallas-Bot/pallas/core/platform/ingress/
ls /tmp/AstrBot/astrbot/core/pipeline/
```

---

## 7. 修订记录

| 日期 | 说明 |
|------|------|
| 2026-06-24 | 初版：WebUI 10 域 + LLM 11 能力 + 架构 10 领域 |
| 2026-06-24 | §6 深度 diff 节选：API 体量、client 层、ingress vs pipeline |
