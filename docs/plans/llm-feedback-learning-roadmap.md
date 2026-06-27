# LLM 反哺 → Repeater 自动学习路线图

## 背景

`llm_chat` 与 repeater 共享 conversation kernel；维护者样本经采集、加权、写回影响接话偏好。本文档覆盖已落地、本次增强与远期计划。

## 阶段 A — 已落地（基线 + 首轮自动化）

| 能力 | 模块 | 说明 |
| --- | --- | --- |
| 样本采集 | `repeater_feedback.py` | llm_chat + repeater select/polish 回调落盘 |
| @ 闲聊样本注入 | `feedback_chat_hint.py` | 【维护者样本参考】 |
| 弱加权 + 触发匹配 | `responder.py` | top / matched / partial 倍率 |
| 校正写回 | WebUI + API | 期望回复参与 bias |
| 自动写回 | `promotion_candidates.py` | support≥3 或校正加权≥2 |

## 阶段 B — 本次实现（高性价比 + 中等投入）

### B1 高性价比

1. **Repeater LLM hint**：`select` / `polish` / `polish_lite` system prompt 注入样本参考（`load_repeater_feedback_system_suffix`）。
2. **场景分桶**：`classify_behavior_scene` + `feedback_learning.weighted_reply_counter` 按 scene 衰减跨场景权重。
3. **时间衰减**：14 天半衰期，90 天过期；加权统计 top_replies。
4. **负样本自动沉淀**：排除≥2 次或颜文字模式 → `penalized_replies`，接话 ×0.45。

### B2 中等投入

5. **向量近似匹配**：`LLM_VECTOR_RETRIEVE=hybrid|embedding|vector` 时对 trigger 做 embedding 近邻，命中 ×1.12。
6. **Trigger–Reply 成对写回**：晋升候选 key = `(group_id, trigger_keywords, reply)`，避免同句不同 trigger 混聚。
7. **牛格塑形联动**：behavioral learning 开启时 auto-writeback 限制 ≤24 字、禁 ASCII 颜文字尾缀。
8. **可观测**：`opportunity_trace.feedback_bias_multiplier`；snapshot `learning_stats`（7 日命中率、auto_promote 次数）。

核心模块：`pallas/product/llm/feedback_learning.py`。

## 阶段 C — 远期（见 Notion 里程碑「LLM 反哺接话自动学习 · 远期」）

| 编号 | 方向 | 目标 | 风险/依赖 |
| --- | --- | --- | --- |
| C1 | Shadow 写回 | 只加权不写语料，对比 trace 后再自动写 | 需 A/B 指标与回滚 |
| C2 | 跨群迁移 | hub 汇总好句，冷群 bootstrap | 群风串味 |
| C3 | 社区语料同步 | 匿名 upload community-stats corpus | 隐私与审核 |
| C4 | 在线倍率调参 | 按复读/追问/排除自动调 bias 倍率 | 反馈环放大 |
| C5 | 维护者 UX | 相似会话批量校正、专家模式默认 writeback | WebUI |
| C6 | 冲突消解 | 同 trigger 多 reply 按加权 support 仲裁 | 数据模型 |
| C7 | Repeater eval 闭环 | `eval_repeater_local` 对接 learning_stats 回归 | 工具链 |

## 配置建议

```toml
# webui.json / 对话策略
LLM_REPEATER_FEEDBACK_ENABLED=true
LLM_REPEATER_BIAS_ENABLED=true
LLM_REPEATER_WRITEBACK_ENABLED=true
LLM_VECTOR_RETRIEVE=hybrid   # 可选，启用语义近似
```

## 验证

```bash
uv run pytest tests/features/test_feedback_learning.py tests/features/test_llm_promotion_candidates.py tests/features/test_llm_repeater_feedback.py tests/plugins/repeater/test_responder.py -q
uv run ruff check pallas/product/llm/ packages/repeater/
```
