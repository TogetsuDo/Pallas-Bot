# @ 闲聊牛格塑形增强计划

> 参考 `/tmp/MaiBot` 的 identity / reply_style / scene 分层 + 表达习惯注入；在 Pallas 现有 `compile_persona_prompt` + `affect_axes` 上补强，不引入 MaiBot 的双阶段 Planner。

## 问题

- `@` 闲聊已走 `compile_persona_prompt_for`，但群画像常为空、轴在默认档时几乎只剩「禁止客服腔」。
- `PersonaAffectContract` 的 stance / 长度 / 禁腔调 **未写入 system prompt**（仅 opener 去重进 variation_hint）。
- 后处理硬裁 emoji/颜文字 + 大量负向规则 → 输出趋同、像 bland 人机。

## MaiBot 可借鉴（已映射）

| MaiBot | Pallas 对应 | 本次动作 |
|--------|-------------|----------|
| identity / reply_style / scene 分层 | `base` + `bot_behavior` + `at_chat` | 保持；新增 **【本轮牛格塑形】** 块 |
| 表达习惯 ReferenceMessage | `expression_habits` + corpus ending | 已有；空 profile 时给默认可感知 hint |
| 关键词 reaction | `affect_triggers` | Phase 2：按消息匹配注入 |
| 确定性后处理 | `llm_rewrite` | 保持反客服；Phase 2 加「保留口语个性」白名单 |

## 分期

### Phase 1（本次）— 让牛格「写进 prompt」

1. `build_persona_affect_system_block(contract)` → stance、长度、禁腔调、收口约束。
2. `build_persona_affect_contract` 默认也产出可感知 length/接话 hint（轴为 0 时不空）。
3. `llm_chat` 在 compile 后注入塑形块 + 群 style hints；variation_hint 仍只管去重。
4. 群 profile 未 ready 时 `group_expression` 给「新群默认群味」而非纯「样本不足」。
5. `at_chat_system_prompt` 补一句正向个性（庆典感/接梗），平衡负向规则。
6. 单测 + ruff。

### Phase 2 — 动态表达（MaiBot expression selector 思路）

1. 按当前 user_text 从 `affect_triggers` + 语料 near-field 召回 1–3 条「情境→说法」。（`dynamic_expression.py` + `build_llm_chat_dynamic_expression_hint`）
2. 关键词 trigger 单次注入：`build_affect_trigger_turn_hint` 匹配当前消息追加短 hint。
3. `llm_rewrite_metadata` 传 `persona_affect_block` / `variation_hint` 给 AI rewrite，塑形开启时跳过过度缩短。

### Phase 3 — 可观测（已完成）

1. runtime snapshot 写入 `persona_shaping`；`/runtime-debug/{request_id}` 返回塑形摘要。
2. WebUI 会话历史「详情 / 行为标注」与 Replay 弹窗展示牛格塑形摘要；含 @ vs repeater 对比说明。

## 验收

- 默认 persona（轴≈0）的 @ 回复 system 中含 **【本轮牛格塑形】** 且非空。
- warmth/chaos 偏离 0 或群 style ready 时，塑形块与 neutral 群可区分。
- 仍禁止 emoji / ASCII 颜文字 / 客服腔（不回归模板牛）。
