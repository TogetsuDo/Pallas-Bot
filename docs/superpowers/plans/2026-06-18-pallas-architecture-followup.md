# Pallas Architecture Follow-up Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the highest-value remaining gaps after the new Pallas core contract audit: plugin governance closure, memory-layer discipline, LLM observability, corpus federation leftovers, and Arknights KB/tool completion.

**Architecture:** Keep the new `pallas-core-contract.md` as the identity layer, then deliver unfinished work through five bounded streams that map directly onto existing code seams. Each stream must preserve the Pallas ordering: `语料底盘` first, `牛格/群味` second, `LLM/memory/tools` as enhancement only.

**Tech Stack:** Python 3.12, NoneBot, FastAPI-style WebUI routes, PostgreSQL-backed repositories, JSON file stores, repo-local Markdown docs, pytest, Ruff.

---

### Task 1: Close Single-Plugin Governance APIs

**Files:**
- Modify: `src/plugins/pb_webui/extended_api.py`
- Modify: `src/features/plugin_capabilities/schema.py`
- Modify: `src/console/webui/plugin_api.py`
- Modify: `docs/architecture/plugin-governance-community-roadmap.md`
- Test: `tests/features/test_plugin_capabilities.py`
- Test: new `tests/plugins/pb_webui/test_plugin_governance_api.py`

- [ ] **Step 1: Write the failing API tests**

Add tests covering:

```python
def test_plugin_governance_get_returns_commands_and_runtime():
    ...
    assert body["ok"] is True
    assert "commands" in body["data"]
    assert "runtime" in body["data"]

def test_plugin_governance_put_filters_only_plugin_prefix():
    ...
    assert saved["command_permission_overrides"] == {"sing.play": "staff"}
    assert "other_plugin.run" not in saved["command_permission_overrides"]
```

- [ ] **Step 2: Run the focused test file to verify failure**

Run: `uv run pytest tests/plugins/pb_webui/test_plugin_governance_api.py -q`
Expected: FAIL because the route or response shape is missing.

- [ ] **Step 3: Implement `GET /plugins/{name}/governance`**

Add a route that returns:

```python
{
    "commands": [...],
    "menu_items": [...],
    "runtime": {
        "global_disable": ...,
        "help_hidden": ...,
    },
    "perm_ui_filtered": [...],
    "limits_ui_filtered": [...],
}
```

Use `build_plugin_capabilities_ui()` as the single command/capability source and filter rows by plugin name.

- [ ] **Step 4: Implement `PUT /plugins/{name}/governance`**

Persist only the selected plugin’s:

```python
command_permission_overrides
command_limit_overrides
global_disable
help_hidden
```

Reject or ignore foreign command IDs that do not start with `<plugin>.`.

- [ ] **Step 5: Run tests and commit**

Run:

```bash
uv run pytest tests/features/test_plugin_capabilities.py tests/plugins/pb_webui/test_plugin_governance_api.py -q
uv run ruff check src/plugins/pb_webui src/features/plugin_capabilities src/console/webui
```

Expected: PASS.

Commit:

```bash
git add src/plugins/pb_webui/extended_api.py src/features/plugin_capabilities/schema.py src/console/webui/plugin_api.py docs/architecture/plugin-governance-community-roadmap.md tests/features/test_plugin_capabilities.py tests/plugins/pb_webui/test_plugin_governance_api.py
git commit -m "feat(webui): add single-plugin governance api"
```

### Task 2: Harden Memory Layers Around `episode_notes`

**Files:**
- Modify: `src/features/llm/memory/store.py`
- Modify: `src/features/llm/memory/teach.py`
- Modify: `src/features/llm/memory/inject.py`
- Modify: `src/features/llm/session_store.py`
- Create: `src/features/llm/memory/policy.py`
- Test: new `tests/features/test_llm_episode_notes.py`

- [ ] **Step 1: Write the failing policy tests**

Cover:

```python
def test_episode_note_accepts_teach_fact():
    assert classify_memory_candidate("记住：本群管银灰厨") == "episode_note"

def test_episode_note_rejects_short_emotion():
    assert classify_memory_candidate("记住：我今天烦") is None

def test_injected_episode_notes_do_not_exceed_cap():
    ...
    assert len(lines) <= 3
```

- [ ] **Step 2: Run the tests to verify failure**

Run: `uv run pytest tests/features/test_llm_episode_notes.py -q`
Expected: FAIL because `policy.py` and classification functions do not exist.

- [ ] **Step 3: Add memory policy classification**

Create `policy.py` with small explicit helpers:

```python
def classify_memory_candidate(text: str) -> str | None: ...
def normalize_episode_note(text: str, *, max_len: int) -> str: ...
def episode_note_has_group_value(text: str) -> bool: ...
```

The first version should stay simple and deterministic:

- accept explicit `记住:` teaches
- reject too-short, purely emotional, or obviously perishable fragments
- normalize into `episode_notes` wording only

- [ ] **Step 4: Wire policy into `teach.py`, `store.py`, and `inject.py`**

Ensure:

- explicit teach goes through policy before save
- stored rows for this path are treated as `episode_notes`
- injected memory block stays capped and clearly labeled as reference-only

- [ ] **Step 5: Run tests and commit**

Run:

```bash
uv run pytest tests/features/test_llm_episode_notes.py tests/common/test_llm_session_store.py -q
uv run ruff check src/features/llm
```

Expected: PASS.

Commit:

```bash
git add src/features/llm/memory/policy.py src/features/llm/memory/store.py src/features/llm/memory/teach.py src/features/llm/memory/inject.py src/features/llm/session_store.py tests/features/test_llm_episode_notes.py
git commit -m "feat(llm): harden episode notes memory policy"
```

### Task 3: Add Token and LLM Daily Observability Closure

**Files:**
- Modify: `src/features/llm/llm_daily_stats_store.py`
- Modify: `src/features/llm/task_metrics.py`
- Modify: `src/plugins/pb_webui/extended_api.py`
- Modify: `src/features/llm/status.py`
- Test: new `tests/features/test_llm_daily_stats_store.py`
- Test: existing `tests/plugins/pb_webui/test_console_daily_stats_flush.py`

- [ ] **Step 1: Write failing stats tests**

Add tests for:

```python
def test_merge_side_snapshot_keeps_prompt_and_completion_tokens():
    ...
    assert merged["totals"]["prompt_tokens"] == 100
    assert merged["totals"]["completion_tokens"] == 20

def test_load_range_returns_token_fields():
    ...
    assert rows[0]["bot"]["totals"]["prompt_tokens"] == 100
```

- [ ] **Step 2: Run focused tests**

Run: `uv run pytest tests/features/test_llm_daily_stats_store.py -q`
Expected: FAIL because token fields are not consistently persisted or exposed.

- [ ] **Step 3: Extend daily stats schema**

Persist and merge:

```python
prompt_tokens
completion_tokens
tools_rounds
reply_gate_skip
reply_gate_defer
```

Do not redesign the store; extend the current snapshot shape.

- [ ] **Step 4: Expose token summaries in status and WebUI payloads**

Add lightweight summaries to:

- LLM status text
- console daily stats payload

Keep them read-only and additive.

- [ ] **Step 5: Run tests and commit**

Run:

```bash
uv run pytest tests/features/test_llm_daily_stats_store.py tests/plugins/pb_webui/test_console_daily_stats_flush.py -q
uv run ruff check src/features/llm src/plugins/pb_webui
```

Expected: PASS.

Commit:

```bash
git add src/features/llm/llm_daily_stats_store.py src/features/llm/task_metrics.py src/plugins/pb_webui/extended_api.py src/features/llm/status.py tests/features/test_llm_daily_stats_store.py tests/plugins/pb_webui/test_console_daily_stats_flush.py
git commit -m "feat(llm): expose token daily observability"
```

### Task 4: Close Remaining Corpus Federation Control-Plane Gaps

**Files:**
- Modify: `docs/architecture/control-plane-corpus-federation.md`
- Modify: `src/features/corpus/` modules that own merge/read/write routing
- Modify: control-plane heartbeat/bootstrap adapters under `src/features/control_plane/` if needed
- Test: add focused federation tests under `tests/features/` or `tests/common/`

- [ ] **Step 1: Write one failing test for remote snapshot merge**

The first closing step should be narrow:

```python
def test_remote_snapshot_merge_prefers_local_on_failure():
    ...
    assert merged["source"] == "local"
```

Use existing local/fed/community concepts; do not invent new federation types.

- [ ] **Step 2: Run the focused test**

Run the exact new test with `uv run pytest ... -q`
Expected: FAIL until merge behavior is explicit in code.

- [ ] **Step 3: Implement one small merge rule at a time**

Prefer this order:

1. remote snapshot merge semantics
2. heartbeat `actions`
3. optional `write_fanout`

Do not attempt `corpus_fed` second PG and all remote features in one PR.

- [ ] **Step 4: Update the corpus architecture doc**

Mark exactly which of these are now complete:

```text
fleet 远程快照合并
heartbeat actions
write_fanout 增强
```

- [ ] **Step 5: Run tests and commit**

Run:

```bash
uv run pytest tests/features -q
uv run ruff check src/features
```

Expected: PASS for the touched federation area.

Commit:

```bash
git add src/features docs/architecture/control-plane-corpus-federation.md tests
git commit -m "feat(corpus): close federation control-plane merge gap"
```

### Task 5: Complete Arknights Query → Tool → Chat Path

**Files:**
- Modify: `src/domain/arknights/` query modules
- Modify: `src/features/llm/tools/arknights.py`
- Modify: `src/features/llm/tools/registry.py`
- Modify: `docs/architecture/arknights-knowledge-mcp.md`
- Test: `tests/features/test_llm_tools_arknights.py`
- Test: new `tests/domain/arknights/test_query_operator.py`

- [ ] **Step 1: Write failing query parity tests**

Add:

```python
def test_query_operator_matches_alias():
    result = query_operator("银灰")
    assert result["name"] == "银灰"

def test_llm_tool_result_matches_query_operator():
    tool = execute_tool("arknights.operator.get", {"name": "银灰"})
    assert tool["ok"] is True
    assert tool["result"]["name"] == "银灰"
```

- [ ] **Step 2: Run focused tests**

Run:

```bash
uv run pytest tests/domain/arknights/test_query_operator.py tests/features/test_llm_tools_arknights.py -q
```

Expected: FAIL until the unified query surface is complete.

- [ ] **Step 3: Implement a single canonical query path**

Ensure:

- command-style lookups
- tool handlers
- future MCP exposure

all consume the same query function surface from `src/domain/arknights/`.

- [ ] **Step 4: Keep tool injection selective**

Do not widen `tool_metadata_for_chat()` globally; only inject Arknights tools when domain inference says they are relevant.

- [ ] **Step 5: Run tests and commit**

Run:

```bash
uv run pytest tests/domain/arknights/test_query_operator.py tests/features/test_llm_tools_arknights.py -q
uv run ruff check src/domain/arknights src/features/llm/tools
```

Expected: PASS.

Commit:

```bash
git add src/domain/arknights src/features/llm/tools docs/architecture/arknights-knowledge-mcp.md tests/domain/arknights/test_query_operator.py tests/features/test_llm_tools_arknights.py
git commit -m "feat(arknights): unify query and tool path"
```

### Task 6: Final Architecture Sync Pass

**Files:**
- Modify: `docs/architecture/pallas-core-contract.md`
- Modify: specialist docs touched by previous tasks
- Test: grep audit only

- [ ] **Step 1: Re-audit unfinished items after implementation**

Run:

```bash
rg -n "\\[ \\]|未开始|部分|骨架|遗留|拟定" docs/architecture
```

Expected: a smaller, more accurate unfinished set than the pre-contract audit.

- [ ] **Step 2: Update the core contract status tables**

Move items from:

```text
已有骨架但未收口
明确还未完成
```

to completed where justified by code, and keep wording concrete.

- [ ] **Step 3: Verify that no completed work still points to deleted stage docs**

Run:

```bash
rg -n "webui-gs-shadcn-roadmap\\.md" docs
```

Expected: no output outside historical plans if retained intentionally.

- [ ] **Step 4: Run final doc lint pass**

Run:

```bash
uv run ruff check src/
```

Expected: PASS; docs-only tasks should not break code lint.

- [ ] **Step 5: Commit**

```bash
git add docs/architecture
git commit -m "docs(architecture): sync contract with delivered work"
```
