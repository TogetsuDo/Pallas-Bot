# Agent Runtime ToolRegistry / Replay Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 收口 `ToolRegistry` canonical contract，并补齐 `request snapshot + runtime trace + replay payload` 的最小调试闭环。

**Architecture:** `Pallas-Bot` 持有工具定义、transport contract 与调试落盘真相源；`Pallas-Bot-AI` 只消费 `tool_catalog` 执行 tool loop 并产出阶段 trace；`Pallas-Bot-WebUI` 负责展示与导出 replay payload，不承担 contract 计算。首版 replay 默认复用已落盘 tool result，不真实重放带副作用工具。

**Tech Stack:** Python 3.12、Pydantic / dataclass、json/jsonl 轻量持久化、Vue 3 + TypeScript、现有 `pb_webui` API 与 AI history 页面。

---

## File Structure

### `Pallas-Bot`

- Create: `Pallas-Bot/pallas/product/llm/tools/contracts.py`
- Create: `Pallas-Bot/pallas/product/llm/runtime_debug.py`
- Modify: `Pallas-Bot/pallas/product/llm/tools/registry.py`
- Modify: `Pallas-Bot/pallas/product/llm/client.py`
- Modify: `Pallas-Bot/pallas/core/platform/ai_callback/runner.py`
- Modify: `Pallas-Bot/packages/pb_webui/extended_api.py`
- Modify: `Pallas-Bot/pallas/product/llm/behavior_store.py` or sibling store helper if复用已有目录更合适
- Test: `Pallas-Bot/tests/platform/test_ai_callback_runner.py`
- Test: `Pallas-Bot/tests/plugins/pb_webui/test_llm_history_api.py`
- Test: `Pallas-Bot/tests/common/test_llm_session_store.py`

### `Pallas-Bot-AI`

- Create: `Pallas-Bot-AI/app/providers/runtime_trace.py`
- Modify: `Pallas-Bot-AI/app/providers/tools.py`
- Modify: `Pallas-Bot-AI/app/providers/tool_loop.py`
- Modify: `Pallas-Bot-AI/app/providers/chain.py`
- Modify: `Pallas-Bot-AI/app/tasks/llm/chat_tasks.py`
- Test: `Pallas-Bot-AI/tests/providers/test_tool_loop.py`
- Test: `Pallas-Bot-AI/tests/providers/test_tool_schema.py`

### `Pallas-Bot-WebUI`

- Modify: `Pallas-Bot-WebUI/src/api/pallasTypes.ts`
- Modify: `Pallas-Bot-WebUI/src/pages/AiHistoryPage.vue`
- Optional Create: `Pallas-Bot-WebUI/src/api/llmRuntime.ts`（若将 replay payload 导出封装成单独 API helper）
- Test/Build: `Pallas-Bot-WebUI/npm run build`

## Task 1: 定义 Bot 侧 canonical tool contract

**Files:**
- Create: `Pallas-Bot/pallas/product/llm/tools/contracts.py`
- Modify: `Pallas-Bot/pallas/product/llm/tools/registry.py`
- Test: `Pallas-Bot/tests/common/test_llm_session_store.py`（新增 contract roundtrip 测试更合适时可新建 `tests/features/test_llm_tool_contracts.py`）

- [ ] **Step 1: 新建 contract 模型，区分本地可执行定义与 transport 快照**

```python
# Pallas-Bot/pallas/product/llm/tools/contracts.py
from __future__ import annotations

from enum import StrEnum
from pydantic import BaseModel, ConfigDict, Field


class ToolCapability(StrEnum):
    READ_ONLY = "read_only"
    SIDE_EFFECTING = "side_effecting"
    REQUIRES_GROUP_CONTEXT = "requires_group_context"


class ToolAuditInfo(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    command_id: str | None = None
    plugin_name: str | None = None
    provider_name: str | None = None


class ToolCatalogEntry(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    name: str
    description: str
    parameters: dict
    source: str
    domains: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)
    audit: ToolAuditInfo = Field(default_factory=ToolAuditInfo)


class ToolCatalogSelection(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    tools_enabled: bool = False
    selective_enabled: bool = False
    inferred_domains: list[str] = Field(default_factory=list)
    schema_count: int = 0


class ToolCatalogSnapshot(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    version: str = "tool_catalog/v1"
    tools: list[ToolCatalogEntry] = Field(default_factory=list)
    selection: ToolCatalogSelection = Field(default_factory=ToolCatalogSelection)


class ToolResultEnvelope(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    ok: bool
    result: dict | None = None
    error: str = ""
    source: str = ""
    audit: ToolAuditInfo = Field(default_factory=ToolAuditInfo)
```

- [ ] **Step 2: 扩展 `LlmToolSpec` 的静态元数据，但不要把 handler 混进 transport 对象**

```python
# Pallas-Bot/pallas/product/llm/tools/registry.py
@dataclass(frozen=True)
class LlmToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]
    domains: frozenset[str]
    handler: ToolHandler
    source: LlmToolSource = LlmToolSource.BUILTIN
    command_id: str | None = None
    visible_in_ui: bool = True
    capabilities: frozenset[str] = frozenset()
    plugin_name: str | None = None
    provider_name: str | None = None
```

- [ ] **Step 3: 补一个从 `LlmToolSpec` 到 `ToolCatalogEntry` 的转换函数**

```python
def tool_catalog_entry_from_spec(spec: LlmToolSpec) -> ToolCatalogEntry:
    return ToolCatalogEntry(
        name=spec.name,
        description=spec.description,
        parameters=spec.parameters,
        source=spec.source.value,
        domains=sorted(spec.domains),
        capabilities=sorted(spec.capabilities),
        audit=ToolAuditInfo(
            command_id=spec.command_id,
            plugin_name=spec.plugin_name,
            provider_name=spec.provider_name,
        ),
    )
```

- [ ] **Step 4: 让执行结果统一包成 `ToolResultEnvelope`，旧返回结构继续兼容**

```python
def normalize_tool_result(raw: Any, *, spec: LlmToolSpec | None = None) -> dict[str, Any]:
    envelope = ToolResultEnvelope(
        ok=isinstance(raw, dict) and bool(raw.get("ok", True)),
        result=(raw.get("result") if isinstance(raw, dict) and "result" in raw else raw) if raw is not None else None,
        error=str(raw.get("error") or "") if isinstance(raw, dict) else "",
        source=spec.source.value if spec is not None else "",
        audit=ToolAuditInfo(
            command_id=spec.command_id if spec is not None else None,
            plugin_name=spec.plugin_name if spec is not None else None,
            provider_name=spec.provider_name if spec is not None else None,
        ),
    )
    return envelope.model_dump(mode="json")
```

- [ ] **Step 5: 为 contract 加 roundtrip 测试**

```python
def test_tool_catalog_snapshot_roundtrip() -> None:
    snap = ToolCatalogSnapshot(
        tools=[
            ToolCatalogEntry(
                name="arknights.operator.get",
                description="查询干员",
                parameters={"type": "object", "properties": {"name": {"type": "string"}}},
                source="builtin",
                domains=["arknights"],
                capabilities=["read_only"],
            )
        ],
        selection=ToolCatalogSelection(tools_enabled=True, schema_count=1, inferred_domains=["arknights"]),
    )
    payload = snap.model_dump(mode="json")
    assert ToolCatalogSnapshot.model_validate(payload).tools[0].name == "arknights.operator.get"
```

- [ ] **Step 6: 运行 Bot 侧 contract 测试**

Run:

```bash
cd /root/Projects/Bots/Pallas-Bot && uv run pytest tests/features/test_llm_tool_contracts.py -q
```

Expected: PASS，至少覆盖 `ToolCatalogSnapshot` 与 `ToolResultEnvelope` 的序列化。

- [ ] **Step 7: 检查点**

检查点内容：
- `registry.py` 仍能注册和执行旧工具
- 新 contract 文件不引入运行时循环依赖
- 先把 commit 留作后续实现阶段，在提交前按仓库约定先给维护者看提交信息草案

## Task 2: Bot 侧输出 `tool_catalog` 并保留旧字段兼容

**Files:**
- Modify: `Pallas-Bot/pallas/product/llm/client.py`
- Modify: `Pallas-Bot/pallas/product/llm/tools/registry.py`
- Test: `Pallas-Bot/tests/features/test_llm_tool_contracts.py`

- [ ] **Step 1: 新增 `tool_catalog_for_chat()`，不要再只返回裸 `tool_schemas`**

```python
def tool_catalog_for_chat(*, task: str | None = None, user_text: str = "") -> ToolCatalogSnapshot | None:
    normalized = str(task or "").strip().lower()
    if normalized in _NO_TOOL_TASKS:
        return None
    cfg = get_llm_config()
    domains: frozenset[str] | None = None
    inferred_domains: list[str] = []
    if cfg.llm_tools_selective:
        inferred = infer_tool_domains(user_text)
        if not inferred:
            return None
        domains = inferred
        inferred_domains = sorted(inferred)
    specs = iter_registered_tools(domains=domains)
    entries = [tool_catalog_entry_from_spec(spec) for spec in specs]
    if not entries:
        return None
    return ToolCatalogSnapshot(
        tools=entries,
        selection=ToolCatalogSelection(
            tools_enabled=True,
            selective_enabled=bool(cfg.llm_tools_selective),
            inferred_domains=inferred_domains,
            schema_count=len(entries),
        ),
    )
```

- [ ] **Step 2: 让现有 `tool_openai_schemas()` 从 `tool_catalog` 派生，而不是重复遍历 registry**

```python
def openai_schemas_from_catalog(catalog: ToolCatalogSnapshot) -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": item.name,
                "description": trim_tool_description(item.description, max_len=get_llm_config().llm_tools_desc_max_len),
                "parameters": item.parameters,
            },
        }
        for item in catalog.tools
    ]
```

- [ ] **Step 3: 在 `client.py` metadata 里同时写入新旧字段**

```python
catalog = tool_catalog_for_chat(task=str(metadata.get("task") or ""), user_text=user_text)
if catalog is not None:
    metadata["tool_catalog"] = catalog.model_dump(mode="json")
    metadata["tools_enabled"] = True
    metadata["tool_schemas"] = openai_schemas_from_catalog(catalog)
    metadata["tool_schema_count"] = int(catalog.selection.schema_count)
```

- [ ] **Step 4: 给 `runtime_debug` 预留 request debug 开关**

```python
metadata["runtime_debug"] = {
    "request_snapshot_enabled": True,
    "replay_enabled": True,
    "trace_level": "standard",
}
```

- [ ] **Step 5: 为兼容层写测试，确认 AI 尚未改造前请求仍可用**

```python
def test_tool_catalog_for_chat_keeps_legacy_tool_schemas() -> None:
    meta = tool_metadata_for_chat(task="llm_chat", user_text="查一下银灰")
    assert meta["tools_enabled"] is True
    assert isinstance(meta["tool_catalog"], dict)
    assert isinstance(meta["tool_schemas"], list)
    assert meta["tool_schema_count"] == len(meta["tool_schemas"])
```

- [ ] **Step 6: 运行 Bot 侧相关测试与 lint**

Run:

```bash
cd /root/Projects/Bots/Pallas-Bot && uv run pytest tests/features/test_llm_tool_contracts.py tests/platform/test_ai_callback_runner.py -q
```

Expected: PASS，`tool_catalog` 已进入 metadata，且旧字段仍存在。

- [ ] **Step 7: 检查点**

检查点内容：
- Bot 到 AI 的 payload 不要求 AI 同步上线后才可运行
- `tool_schemas` 的生成逻辑只剩一条派生链，避免双口径

## Task 3: AI 仓改为消费 `tool_catalog`，并输出结构化 stage trace

**Files:**
- Create: `Pallas-Bot-AI/app/providers/runtime_trace.py`
- Modify: `Pallas-Bot-AI/app/providers/tools.py`
- Modify: `Pallas-Bot-AI/app/providers/tool_loop.py`
- Modify: `Pallas-Bot-AI/app/providers/chain.py`
- Test: `Pallas-Bot-AI/tests/providers/test_tool_loop.py`

- [ ] **Step 1: 新建 AI 侧 trace 模型，保留 `rounds` 兼容现有 WebUI**

```python
# Pallas-Bot-AI/app/providers/runtime_trace.py
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ToolCallTrace(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")
    tool: str
    args_keys: list[str] = Field(default_factory=list)
    ok: bool = True
    error: str = ""
    result_preview: str = ""


class StageTrace(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")
    stage: str
    status: str
    provider: str = ""
    model: str = ""
    latency_ms: int = 0
    tool_calls: list[ToolCallTrace] = Field(default_factory=list)


class AgentRuntimeTrace(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")
    version: str = "agent_trace/v1"
    agent_stage_plan: list[str] = Field(default_factory=list)
    tool_schema_count: int = 0
    tool_call_count: int = 0
    final_stage: str | None = None
    request_snapshot_id: str | None = None
    rounds: list[dict] = Field(default_factory=list)
    stages: list[StageTrace] = Field(default_factory=list)
    status: str = "success"
```

- [ ] **Step 2: 优先从 `tool_catalog` 解析 schema，旧 `tool_schemas` 只兜底**

```python
def resolve_tool_schemas(*, task: str, metadata: dict[str, Any] | None = None, user_text: str = "") -> list[dict[str, Any]]:
    meta = metadata if isinstance(metadata, dict) else {}
    catalog = meta.get("tool_catalog")
    if isinstance(catalog, dict):
        tools = list(catalog.get("tools") or [])
        if tools:
            return [
                {
                    "type": "function",
                    "function": {
                        "name": str(item.get("name") or "").strip(),
                        "description": str(item.get("description") or "").strip(),
                        "parameters": item.get("parameters") or {"type": "object", "properties": {}},
                    },
                }
                for item in tools
                if str(item.get("name") or "").strip()
            ]
    raw = meta.get("tool_schemas")
    return [item for item in raw if isinstance(item, dict)] if isinstance(raw, list) else []
```

- [ ] **Step 3: 在 `tool_loop.py` 里把裸 dict trace 换成模型驱动**

```python
trace = AgentRuntimeTrace(
    agent_stage_plan=list(resolve_agent_stage_plan(metadata)),
    tool_schema_count=len(tool_schemas),
    request_snapshot_id=str(meta.get("runtime_debug", {}).get("request_snapshot_id") or "") or None,
)
```

- [ ] **Step 4: 每轮工具执行后补 `StageTrace` 与 `ToolCallTrace`**

```python
stage = StageTrace(stage="tool_loop", status="success", provider=provider_name, model=model)
stage.tool_calls.append(
    ToolCallTrace(
        tool=tool_name,
        args_keys=sorted(args.keys()),
        ok=bool(tool_result.get("ok")),
        error=str(tool_result.get("error") or ""),
        result_preview=str(tool_result.get("result") or "")[:160],
    )
)
trace.stages.append(stage)
```

- [ ] **Step 5: 把 `plan` 与 `generate` 也记录成阶段，不只记录 `rounds`**

```python
trace.stages.append(StageTrace(stage="plan", status="success", provider=provider_name, model=model))
trace.final_stage = "generate"
trace.stages.append(StageTrace(stage="generate", status="success", provider=provider_name, model=model))
```

- [ ] **Step 6: 更新测试，断言新 trace 字段存在且旧 UI 字段不回退**

```python
def test_complete_with_tool_loop_records_stage_trace() -> None:
    reply, message = asyncio.run(...)
    trace = message["_agent_trace"]
    assert trace["version"] == "agent_trace/v1"
    assert trace["stages"][0]["stage"] in {"plan", "tool_loop", "generate"}
    assert trace["rounds"][0]["tool_calls"] == ["arknights.operator.get"]
```

- [ ] **Step 7: 运行 AI 仓测试**

Run:

```bash
cd /root/Projects/Bots/Pallas-Bot-AI && uv run pytest tests/providers/test_tool_loop.py tests/providers/test_tool_schema.py -q
```

Expected: PASS，新 `tool_catalog` 输入与 `agent_trace/v1` 同时被覆盖。

## Task 4: Bot 侧落盘 request snapshot / runtime trace，并提供 replay payload API

**Files:**
- Create: `Pallas-Bot/pallas/product/llm/runtime_debug.py`
- Modify: `Pallas-Bot/pallas/product/llm/client.py`
- Modify: `Pallas-Bot/pallas/core/platform/ai_callback/runner.py`
- Modify: `Pallas-Bot/packages/pb_webui/extended_api.py`
- Test: `Pallas-Bot/tests/platform/test_ai_callback_runner.py`
- Test: `Pallas-Bot/tests/plugins/pb_webui/test_llm_history_api.py`

- [ ] **Step 1: 新建轻量落盘 helper，沿用 `jsonl` 风格**

```python
# Pallas-Bot/pallas/product/llm/runtime_debug.py
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any

from pallas.core.foundation.paths import plugin_data_dir


def runtime_debug_dir() -> Path:
    path = plugin_data_dir("pb_webui", create=True) / "llm_runtime"
    path.mkdir(parents=True, exist_ok=True)
    return path


def request_snapshot_path() -> Path:
    return runtime_debug_dir() / "request_snapshots.jsonl"


def runtime_trace_path() -> Path:
    return runtime_debug_dir() / "runtime_traces.jsonl"
```

- [ ] **Step 2: 在 Bot 提交 AI 请求前写 request snapshot**

```python
def append_request_snapshot(*, request_id: str, task: str, system_prompt: str, messages: list[dict[str, Any]], metadata: dict[str, Any]) -> str:
    snapshot_id = f"reqsnap_{uuid.uuid4().hex[:16]}"
    row = {
        "request_snapshot_id": snapshot_id,
        "request_id": request_id,
        "created_at": int(time.time()),
        "task": task,
        "system_prompt": system_prompt,
        "messages": messages,
        "agent_stage_plan": list(metadata.get("agent_stage_plan") or []),
        "tool_catalog": metadata.get("tool_catalog") or {},
        "metadata_subset": {
            "task": metadata.get("task"),
            "mode": metadata.get("mode"),
            "bot_id": metadata.get("bot_id"),
            "group_id": metadata.get("group_id"),
            "user_id": metadata.get("user_id"),
        },
    }
    with request_snapshot_path().open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return snapshot_id
```

- [ ] **Step 3: 在 `client.py` 把 `request_snapshot_id` 写回 metadata 给 AI 使用**

```python
snapshot_id = append_request_snapshot(
    request_id=request.request_id,
    task=str(metadata.get("task") or "llm_chat"),
    system_prompt=request.system_prompt,
    messages=[{"role": item.role, "content": item.content} for item in messages],
    metadata=metadata,
)
metadata.setdefault("runtime_debug", {})
metadata["runtime_debug"]["request_snapshot_id"] = snapshot_id
```

- [ ] **Step 4: callback 收到 `agent_trace` 后单独落 runtime trace**

```python
def append_runtime_trace(*, request_id: str, trace: dict[str, Any]) -> None:
    row = {
        "request_id": request_id,
        "request_snapshot_id": trace.get("request_snapshot_id"),
        "created_at": int(time.time()),
        "trace": trace,
    }
    with runtime_trace_path().open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
```

- [ ] **Step 5: 在 `extended_api.py` 提供查询与导出接口**

```python
@router.get(f"{x}/llm/runtime-debug/{request_id}", include_in_schema=True)
async def _llm_runtime_debug(request_id: str) -> JSONResponse:
    data = load_runtime_debug_bundle(request_id=request_id)
    return JSONResponse({"ok": True, "data": data})


@router.get(f"{x}/llm/runtime-debug/{request_id}/replay", include_in_schema=True)
async def _llm_runtime_replay_payload(request_id: str) -> JSONResponse:
    payload = build_replay_payload(request_id=request_id, mode="mock_tools")
    return JSONResponse({"ok": True, "data": payload})
```

- [ ] **Step 6: 给 API 写测试，至少断言 request snapshot id 串起来**

```python
async def test_llm_runtime_debug_api_returns_snapshot_and_trace(client):
    resp = await client.get("/pallas/api/llm/runtime-debug/req-1")
    payload = resp.json()
    assert payload["ok"] is True
    assert payload["data"]["trace"]["request_snapshot_id"] == payload["data"]["snapshot"]["request_snapshot_id"]
```

- [ ] **Step 7: 运行 Bot 侧 callback / API 测试**

Run:

```bash
cd /root/Projects/Bots/Pallas-Bot && uv run pytest tests/platform/test_ai_callback_runner.py tests/plugins/pb_webui/test_llm_history_api.py -q
```

Expected: PASS，`agent_trace` 不仅进入 behavior run，也能被 runtime debug API 查询到。

## Task 5: WebUI 展示 stage trace，并导出 replay payload

**Files:**
- Modify: `Pallas-Bot-WebUI/src/api/pallasTypes.ts`
- Modify: `Pallas-Bot-WebUI/src/pages/AiHistoryPage.vue`
- Optional Create: `Pallas-Bot-WebUI/src/api/llmRuntime.ts`
- Test/Build: `Pallas-Bot-WebUI/npm run build`

- [ ] **Step 1: 扩展前端类型，给 `agent_trace` 增加 `version` / `stages` / `request_snapshot_id`**

```ts
export interface LlmHistoryBehaviorAgentTraceToolCall {
  tool?: string;
  args_keys?: string[];
  ok?: boolean;
  error?: string | null;
  result_preview?: string | null;
}

export interface LlmHistoryBehaviorAgentTraceStage {
  stage?: string;
  status?: string;
  provider?: string;
  model?: string;
  latency_ms?: number;
  tool_calls?: LlmHistoryBehaviorAgentTraceToolCall[];
}

export interface LlmHistoryBehaviorAgentTrace {
  version?: string;
  agent_stage_plan?: string[];
  request_snapshot_id?: string | null;
  tool_schema_count?: number;
  tool_call_count?: number;
  rounds?: LlmHistoryBehaviorAgentTraceRound[];
  stages?: LlmHistoryBehaviorAgentTraceStage[];
  final_stage?: string | null;
}
```

- [ ] **Step 2: 在 `AiHistoryPage.vue` 增加 stage 摘要渲染**

```ts
function behaviorAgentStageHighlights(trace?: LlmHistoryBehaviorAgentTrace | null) {
  if (!trace?.stages?.length) return [];
  return trace.stages.map((item) => ({
    label: item.stage || "unknown",
    value: [item.status, item.provider, item.model, item.latency_ms ? `${item.latency_ms}ms` : ""]
      .filter(Boolean)
      .join(" / "),
  }));
}
```

- [ ] **Step 3: 增加“复制 replay payload”按钮，先只调导出 API**

```ts
async function copyReplayPayload(requestId: string) {
  const resp = await fetchPallasJson(`/pallas/api/llm/runtime-debug/${encodeURIComponent(requestId)}/replay`);
  await navigator.clipboard.writeText(JSON.stringify(resp.data, null, 2));
}
```

- [ ] **Step 4: UI 上优先展示 `request_snapshot_id` 与 stage 列表，不新增复杂入口**

```vue
<div v-if="trace?.request_snapshot_id" class="kv-chip">
  <span class="label">Snapshot</span>
  <code>{{ trace.request_snapshot_id }}</code>
</div>
```

- [ ] **Step 5: 跑 WebUI build**

Run:

```bash
cd /root/Projects/Bots/Pallas-Bot-WebUI && npm run build
```

Expected: PASS，AI history 页面类型和模板都能通过构建。

- [ ] **Step 6: 窄屏自检**

Run/Check:

```text
在 ≤560px 宽度下确认 agent trace 面板摘要不挤爆标题区，复制按钮不与既有操作冲突。
```

Expected: 窄屏下 stage 列表可换行，不遮挡现有行为记录卡片。

## Task 6: 文档、回归验证与上线前检查

**Files:**
- Modify: `Pallas-Bot/docs/architecture/internal/agent-runtime-toolregistry-replay-plan.md`（执行中勾选）
- Optional Modify: `Pallas-Bot/docs/architecture/internal/pallas-ai-implementation.md`
- Optional Modify: `Pallas-Bot/docs/develop/README.md` 或相关开发文档

- [ ] **Step 1: 更新现有内部文档，把新 contract 名称与 replay 边界写回**

```markdown
- ToolRegistry 终态：Bot 持有 canonical contract，AI 只消费 `tool_catalog`
- Replay 首版：默认 `mock_tools`，不真实重放带副作用工具
```

- [ ] **Step 2: 运行 Bot 仓 lint / format / targeted tests**

Run:

```bash
cd /root/Projects/Bots/Pallas-Bot && uv run ruff check pallas/ packages/ tests/ && uv run ruff format --check pallas/ packages/ tests/
```

Expected: PASS，无新增 lint / format 问题。

- [ ] **Step 3: 运行 AI 仓 lint / format / targeted tests**

Run:

```bash
cd /root/Projects/Bots/Pallas-Bot-AI && uv run ruff check app tests && uv run ruff format --check app tests && uv run pytest tests/providers/test_tool_loop.py tests/providers/test_tool_schema.py -q
```

Expected: PASS，tool loop contract 与 stage trace 相关测试通过。

- [ ] **Step 4: 运行 WebUI build**

Run:

```bash
cd /root/Projects/Bots/Pallas-Bot-WebUI && npm run build
```

Expected: PASS，无类型或模板错误。

- [ ] **Step 5: 手工联调 checklist**

Run/Check:

```text
1. 发起一次 llm_chat 工具调用请求
2. 在 Bot 落盘目录确认 request snapshot 与 runtime trace 已生成
3. 在 AI history 页面看到 agent trace stages
4. 点击复制 replay payload，确认 payload 包含 request_snapshot_id 与 tool replay mode
```

Expected: 整条链路可观测、可导出、不中断现有回复路径。

- [ ] **Step 6: 预提交检查点**

检查点内容：
- 若存在历史 failing tests，区分“历史问题”与“本次引入问题”
- 若格式化波及无关文件，停止并缩小范围
- 实际提交前先给维护者看提交信息草案，例如：

```text
feat(llm-runtime): 收口 ToolRegistry 契约与调试回放链路
```

## Execution Notes

- 建议实现顺序严格按 Task 1 → 5 执行，不要先写 WebUI 再补 contract。
- 若任务需要拆分提交，推荐最少拆为：
  1. `feat(llm-tools): 收口 tool contract 与 tool_catalog`
  2. `feat(llm-runtime): 增加 request snapshot 与 stage trace`
  3. `feat(webui): 展示 agent runtime trace 并导出 replay payload`
- 若执行中发现 `request snapshot` 应落在 AI 仓而非 Bot 仓，先停下复核边界；本计划默认 Bot 为真相源，不建议中途反转。
