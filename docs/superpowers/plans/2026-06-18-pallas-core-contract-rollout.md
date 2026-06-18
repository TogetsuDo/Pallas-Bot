# Pallas Core Contract Rollout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the old 4.0-era architecture entrypoints with a Pallas-branded core contract, migrate unfinished work into current docs, and retire completed phase-only docs without losing navigability.

**Architecture:** Introduce one new canonical architecture entrypoint for product and system identity, then convert legacy 4.0 docs into archive stubs or remove them when fully superseded. Keep specialist docs for AI runtime, persona/LLM, corpus, plugin governance, and knowledge tooling as living subsidiary specs.

**Tech Stack:** Markdown architecture docs, repo-local cross-links, ripgrep-based audit, apply_patch-based edits.

---

### Task 1: Stabilize the New Canonical Entry Doc

**Files:**
- Modify: `docs/architecture/pallas-core-contract.md`
- Test: manual link and terminology audit across architecture docs

- [ ] **Step 1: Audit terminology consistency**

Check that the doc consistently uses:

```text
语料底盘 -> corpus_foundation
牛格 -> persona_profile
群味 -> group_flavor
多牛社交 -> multi_bot_social
会话记忆 -> session_memory
群内旧事 -> episode_notes
关系备注 -> relationship_notes
```

- [ ] **Step 2: Run targeted grep to verify terminology is present**

Run: `rg -n "语料底盘|牛格|群味|多牛社交|corpus_foundation|persona_profile|group_flavor|multi_bot_social|session_memory|episode_notes|relationship_notes" docs/architecture/pallas-core-contract.md`
Expected: PASS with at least one match for each required term.

- [ ] **Step 3: Tighten wording if any section still sounds like a generic AI bot**

If the grep or manual review shows generic language like “陪伴 bot” without the Pallas contrast, revise the affected paragraphs so they explicitly preserve:

```md
Pallas 的品牌核心不是单体陪伴，而是以语料底盘为根、以牛格与群味为形、以多牛社交为主场的 AI 体。
```

- [ ] **Step 4: Re-run grep after wording edits**

Run: `rg -n "单体陪伴|语料底盘|多牛社交|群聊社交" docs/architecture/pallas-core-contract.md`
Expected: PASS with explicit contrast language present.

- [ ] **Step 5: Commit**

```bash
git add docs/architecture/pallas-core-contract.md
git commit -m "docs(architecture): add pallas core contract"
```

### Task 2: Convert `pallas-4.0-roadmap.md` into an Archive Stub

**Files:**
- Modify: `docs/architecture/pallas-4.0-roadmap.md`
- Test: cross-link audit via `rg`

- [ ] **Step 1: Replace the body with an archive header**

Rewrite the file to a short archive stub with these sections:

```md
# Pallas-Bot 4.0 路线图（归档）

> **状态**：归档，不再作为现行总入口维护。
> **现行入口**：`pallas-core-contract.md`

## 为什么归档

- 4.0 瘦身、插件分家、控制台视觉等阶段性目标已基本完成
- 仍持续建设的能力已经迁入现行文档

## 现行文档

- `pallas-core-contract.md`
- `pallas-final-ai-shape.md`
- `persona-llm-roadmap.md`
- `llm-efficiency-roadmap.md`
- `plugin-governance-community-roadmap.md`
- `control-plane-corpus-federation.md`
- `arknights-knowledge-mcp.md`
```

- [ ] **Step 2: Preserve minimal historical context**

Keep a short bullet list of what 4.0 historically meant:

```md
- 本体瘦身与插件分家
- 牛格、群风格与 LLM 接话统一
- 官方扩展、WebUI、CLI 与 AI 仓分责
```

- [ ] **Step 3: Run link audit**

Run: `rg -n "pallas-4\\.0-roadmap\\.md" docs`
Expected: PASS showing references still exist, but the file remains present as a stable archive target.

- [ ] **Step 4: Manual review of outgoing links**

Open the stub and verify every “现行文档” link path is valid relative to `docs/architecture/`.

- [ ] **Step 5: Commit**

```bash
git add docs/architecture/pallas-4.0-roadmap.md
git commit -m "docs(architecture): archive 4.0 roadmap"
```

### Task 3: Convert `pallas-4.0-slim.md` into an Archive + Migration Stub

**Files:**
- Modify: `docs/architecture/pallas-4.0-slim.md`
- Test: cross-link audit via `rg`

- [ ] **Step 1: Rewrite as archive stub with migration context**

Replace the file body with:

```md
# Pallas-Bot 4.0 · 本体瘦身与插件分家（归档）

> **状态**：归档，安装与迁移信息仍保留。
> **现行总纲**：`pallas-core-contract.md`

## 本文仍保留什么

- core / extra / local 的历史迁移背景
- 旧 3.x/4.0 升级说明入口
- 扩展安装路径的历史说明

## 当前结论

- 插件分家已成为既有现实，不再作为阶段路线维护
- 后续只在现行文档中维护仍未完成的事项
```

- [ ] **Step 2: Keep only the still-useful operator guidance**

Retain a compressed section with these operational facts:

```md
- `local/plugins` 仍是最高优先级覆盖路径
- 官方扩展可通过 WebUI 商店或 `uv sync --extra ...` 安装
- core / extra / local 加载规则以运行时代码为准
```

- [ ] **Step 3: Point unfinished items to living docs**

Add a “仍在持续建设” section:

```md
- 插件治理页：见 `plugin-governance-community-roadmap.md`
- AI 扩展运行时收口：见 `pallas-ai-implementation.md`
- 总契约：见 `pallas-core-contract.md`
```

- [ ] **Step 4: Run link audit**

Run: `rg -n "pallas-4\\.0-slim\\.md" docs`
Expected: PASS showing the file remains as a stable target for old links.

- [ ] **Step 5: Commit**

```bash
git add docs/architecture/pallas-4.0-slim.md
git commit -m "docs(architecture): archive 4.0 slim roadmap"
```

### Task 4: Remove the Completed Visual Phase Roadmap

**Files:**
- Delete: `docs/architecture/webui-gs-shadcn-roadmap.md`
- Modify: all docs that reference it
- Test: `rg` for broken references

- [ ] **Step 1: Identify all references before deletion**

Run: `rg -n "webui-gs-shadcn-roadmap\\.md" docs`
Expected: PASS listing every incoming reference.

- [ ] **Step 2: Replace each incoming reference with a stable successor**

Use these replacements:

```text
`webui-gs-shadcn-roadmap.md` -> `pallas-core-contract.md` when the reference is about overall completion
`webui-gs-shadcn-roadmap.md` -> `Pallas-Bot-WebUI` docs when the reference is specifically about UI implementation details
```

- [ ] **Step 3: Delete the file**

Delete `docs/architecture/webui-gs-shadcn-roadmap.md` after all inbound links are updated.

- [ ] **Step 4: Verify no references remain**

Run: `rg -n "webui-gs-shadcn-roadmap\\.md" docs`
Expected: no output.

- [ ] **Step 5: Commit**

```bash
git add docs
git commit -m "docs(architecture): retire completed webui gs roadmap"
```

### Task 5: Repoint Documentation Entry Surfaces

**Files:**
- Modify: `docs/README.md`
- Modify: `docs/develop/README.md`
- Modify: `docs/develop/workflow.md`
- Modify: `docs/guide/4.0-start.md`
- Modify: `docs/plugins/persona/README.md`
- Test: targeted grep and manual review

- [ ] **Step 1: Replace old “4.0 总览” references with the new canonical entry**

Update lines that currently present:

```md
[4.0 路线图](...)
[本体瘦身](...)
```

to instead present:

```md
[Pallas 核心契约](../architecture/pallas-core-contract.md)
[AI 终态架构](../architecture/pallas-final-ai-shape.md)
```

Adjust relative paths per file location.

- [ ] **Step 2: Preserve historical migration links where still useful**

If a page is specifically about upgrading from 3.x/4.0, keep one archive link:

```md
历史迁移背景见 [4.0 瘦身归档](../architecture/pallas-4.0-slim.md)
```

- [ ] **Step 3: Run audit for old entrypoint references**

Run: `rg -n "\\[4\\.0 路线图\\]|pallas-4\\.0-roadmap\\.md|pallas-4\\.0-slim\\.md" docs/README.md docs/develop docs/guide/4.0-start.md docs/plugins/persona/README.md`
Expected: PASS with only intentional archive references remaining.

- [ ] **Step 4: Manually review entrypoint readability**

Confirm a newcomer landing on docs now sees:

```text
1. Pallas 核心契约
2. AI 终态架构
3. persona / LLM / 插件治理 / 语料联邦 等专项文档
```

- [ ] **Step 5: Commit**

```bash
git add docs/README.md docs/develop/README.md docs/develop/workflow.md docs/guide/4.0-start.md docs/plugins/persona/README.md
git commit -m "docs: repoint architecture entry surfaces"
```

### Task 6: Align Specialist Docs to the New Contract

**Files:**
- Modify: `docs/architecture/pallas-final-ai-shape.md`
- Modify: `docs/architecture/persona-llm-roadmap.md`
- Modify: `docs/architecture/llm-efficiency-roadmap.md`
- Modify: `docs/architecture/plugin-governance-community-roadmap.md`
- Modify: `docs/architecture/arknights-knowledge-mcp.md`
- Modify: `docs/architecture/control-plane-corpus-federation.md`
- Test: manual link and terminology audit

- [ ] **Step 1: Add “现行总纲” backlink to each specialist doc**

At the top of each file, add or revise a line like:

```md
> **现行总纲**：见 [Pallas 核心契约](pallas-core-contract.md)。
```

- [ ] **Step 2: Update wording that still implies generic 4.0 umbrella ownership**

Replace wording like:

```md
目标版本：4.0
见 4.0 路线图
```

with wording like:

```md
本专项由 `pallas-core-contract.md` 统领
```

Retain explicit version notes only where historically necessary.

- [ ] **Step 3: Preserve unfinished work in the specialist doc, not the old 4.0 roadmap**

Ensure each of these remains documented in a living location:

```text
plugin governance unfinished work -> plugin-governance-community-roadmap.md
memory / queue / token / gate work -> llm-efficiency-roadmap.md
AI runtime收口 -> pallas-ai-implementation.md / pallas-final-ai-shape.md
corpus federation unfinished work -> control-plane-corpus-federation.md
arknights KB unfinished work -> arknights-knowledge-mcp.md
```

- [ ] **Step 4: Run grep for lingering stale framing**

Run: `rg -n "见 \\[pallas-4\\.0-roadmap|目标版本：4\\.0|4\\.0 总览" docs/architecture`
Expected: only intentional archive/historical mentions remain.

- [ ] **Step 5: Commit**

```bash
git add docs/architecture
git commit -m "docs(architecture): align specialist docs to core contract"
```

### Task 7: Produce the Post-Audit Coding Plan

**Files:**
- Modify: `docs/superpowers/plans/2026-06-18-pallas-core-contract-rollout.md`
- Create: `docs/superpowers/plans/2026-06-18-pallas-architecture-followup.md`
- Test: plan self-review

- [ ] **Step 1: Create a follow-up implementation plan for unfinished architecture work**

Write `docs/superpowers/plans/2026-06-18-pallas-architecture-followup.md` with these workstreams:

```text
1. plugin governance closing work
2. memory layers contract implementation
3. llm observability and token metrics
4. corpus federation remaining work
5. arknights kb / tool / mcp completion
```

Use the same implementation-plan header format and checkbox task structure.

- [ ] **Step 2: Include exact file touch lists per workstream**

The follow-up plan must mention concrete starting points such as:

```text
src/plugins/pb_webui/extended_api.py
src/features/plugin_capabilities/schema.py
src/features/llm/memory/
src/features/llm/session_store.py
src/features/llm/governance.py
src/features/llm/llm_daily_stats_store.py
src/features/persona/compile_persona_prompt.py
src/features/corpus/
src/domain/arknights/
```

- [ ] **Step 3: Self-review the new follow-up plan**

Check:

```text
- no TODO/TBD placeholders
- every named subsystem maps to a task
- every task has files, commands, and expected outcomes
```

- [ ] **Step 4: Run plan existence check**

Run: `ls docs/superpowers/plans/2026-06-18-pallas-*.md`
Expected: both rollout and follow-up plans are present.

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/plans/2026-06-18-pallas-core-contract-rollout.md docs/superpowers/plans/2026-06-18-pallas-architecture-followup.md
git commit -m "docs(plan): add pallas architecture follow-up plans"
```
