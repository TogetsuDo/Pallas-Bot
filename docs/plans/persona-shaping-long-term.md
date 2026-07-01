# Repeater / @ 人设塑形 · 远期计划

> 前 6 点（统一 repeater 塑形入口、动态表达、rewrite 元数据、群味文案、eval、学习闭环）已完成。本文档规划后续 OPT 与污染治理。

## 背景

- 写入侧已有 `corpus_contamination` 门控 + 定时扫库（PG + Mongo）。
- Repeater 全路径已走 `build_repeater_llm_persona_context`；`eval_repeater_persona.py` 可对真实群抽样。
- AI 仓 `llm_rewrite` 已识别 `persona_shaping_active`，但 `preserve_colloquial_rewrite` 需显式对齐。

## 分期

### Phase A — 资产标准（OPT-LLM-024）✅ 本次

| 项 | 说明 |
|----|------|
| `PersonaAssetBundleV1` | `prompt_bundle` + 可选 `repeater_overlay` |
| JSON Schema | `persona_asset_bundle_json_schema()` + `tools/export_persona_bundle.py --schema-only` |
| CLI 导出 | `uv run python tools/export_persona_bundle.py --bot-id … --group-id …` |

**DoD**：单测覆盖序列化；schema 可被 WebUI / 外部站 import。

### Phase B — AI rewrite 白名单闭环（本次）

| 项 | 说明 |
|----|------|
| `preserve_colloquial_rewrite` | AI `_persona_shaping_active` 同时认此键 |
| repeater task | 塑形开启时跳过长度裁切、客服腔修剪、scaffold 剥离 |
| 单测 | Pallas-Bot-AI `test_llm_rewrite.py` 补 preserve 键用例 |

**DoD**：Bot 传 `preserve_colloquial_rewrite=true` 时，repeater 回复不被 rewrite 缩短。

### Phase C — 间接污染（表达参考过滤）✅ 本次

| 项 | 说明 |
|----|------|
| `is_expression_reference_safe` | 语料收尾 / 动态表达候选过滤庆典腔短语 |
| 接入点 | `near_field_scorer.select_scored_expression_candidates` |
| 不扫 style_profile 数值 | profiler 只产统计，不存原文；污染主要来自 answers / live 消息 |

**DoD**：含「希望每个庆典」的 answer 不会进入【语料收尾参考】。

### Phase D — 群 profiler 增强（后续）✅ 本次

1. `build_group_style_profile` 计算前过滤污染 answer / message 样本。
2. `cross_group_profiler` 加权时降权「污染率高」群（`contamination_skipped`）。
3. `compile_group_style_snapshot` 暴露 `contamination_skipped_count` 供 WebUI 只读展示。

### Phase E — 纯语料 select 质量（后续）✅ 本次

1. select 路径过滤污染候选；跳过时写入 `select_pool_observations.jsonl`。
2. promotion 聚合候选时跳过污染回复（writeback 门控保留）。
3. `eval_repeater_persona.py` 输出 `dynamic_hit_rate` / `dynamic_warn`。

## 依赖与仓库

| Phase | Repos |
|-------|-------|
| A, C, D, E | Pallas-Bot |
| B | Pallas-Bot-AI |

## 验收清单

- [x] `export_persona_bundle.py` 在真实 bot/group 可导出合法 JSON
- [x] AI rewrite 认 `preserve_colloquial_rewrite`
- [x] 污染短语不出现在 corpus ending / dynamic expression 候选
- [x] eval 抽样 `all_ok: true`（已验证 bot=727130160, group=2927116873）
- [x] profiler 过滤污染样本并写入 `contamination_skipped`
- [x] select 跳过时落盘 `select_pool_observations.jsonl`
- [x] eval 输出 `dynamic_hit_rate` / `dynamic_warn`
