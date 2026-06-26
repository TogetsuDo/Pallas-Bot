# 帮助图 v3 升级计划

> 状态：Phase 1–5 已完成 · 路线：PIL 卡片合成（GsCore 图标思路 + 明晰 Clarity 色板）

## 背景

- QQ「牛牛帮助」成图在 **Pallas-Bot** `packages/help/`，非 WebUI。
- 现状：pillowmd + Markdown 宽表，无插件封面/头像，观感像文档表格。
- WebUI 与帮助图已通过 `resolve_catalog_visuals()` 打通 icon/cover/avatar（含包内 `assets/` → `/pallas/plugin-assets/`）。

## 目标

1. 一级总览改为**卡片网格**，每插件展示图标 + 状态 + 简介。
2. 复用控制台插件视觉资源（cover → icon → 品牌 fallback）。
3. 保留明晰 Clarity 色板；二/三级页与 WebUI 预览已接入。

## 参考取舍

| 项目 | 借鉴 | 不采纳 |
|------|------|--------|
| GsCore | Banner 图标、命令卡片、PIL 轻量 | 预制 texture 贴图体系 |
| 真寻 | 分类顶栏、信息分区、主题化 | Playwright 全量迁移（Phase 6 再评估） |
| MaiBot | — | 无统一帮助图 |

## 架构

```text
handlers.py (牛牛帮助 无参)
  → build_help_menu_rows()
  → draw_plugin_menu_image()     # PIL 卡片
  → render_help_image_bytes()    # 缓存 + 编码

handlers.py (牛牛帮助 <插件>)
  → build_plugin_detail_data()
  → draw_plugin_detail_image()

handlers.py (牛牛帮助 <插件> <功能>)
  → build_function_detail_data()
  → draw_function_detail_image()

GET /pallas/api/help/preview
  → render_help_preview_bytes()
```

### 新增模块

| 文件 | 职责 |
|------|------|
| `packages/help/help_theme.py` | VISUAL.md 色板与间距常量 |
| `packages/help/plugin_visuals.py` | 插件图标 URL → 本地路径 → PIL |
| `packages/help/draw_plugin_menu.py` | 一级总览 PIL 合成 |
| `packages/help/menu_rows.py` | 菜单行数据 + 分页（`MENU_PAGE_SIZE=20`） |
| `packages/help/plugin_detail_data.py` | 二/三级结构化数据 |
| `packages/help/draw_plugin_detail.py` | 二级插件页 PIL |
| `packages/help/draw_function_detail.py` | 三级功能详情 PIL |
| `packages/help/preview.py` | WebUI / API 预览编排 |
| `packages/help/console_routes.py` | `GET …/help/preview` |

## 分期

### Phase 1 — 视觉数据层 ✅ 本 PR

- [x] `plugin_visuals.py`：对接 `resolve_catalog_visuals`、商店快照、本地插件 assets
- [x] `help_theme.py`：色板 / 字体路径
- [x] 单元测试 `test_plugin_visuals.py`

### Phase 2 — 一级卡片化 ✅ 本 PR

- [x] `draw_plugin_menu.py`：3 列卡片、圆角图标、状态点、导航/footer
- [x] `handlers.py` / `renderer.py` 接入
- [x] 测试 `test_draw_plugin_menu.py`

### Phase 3 — 二级插件页 ✅

- [x] Banner + 2 列功能卡片（替代五列表格）
- [x] `draw_plugin_detail.py` + `handlers` / `renderer` 接入
- [x] 测试 `test_draw_plugin_detail.py`

### Phase 4 — 三级详情统一 ✅

- [x] KV 卡片 +「怎么用」区块
- [x] `draw_function_detail.py` + `handlers` 接入

### Phase 5 — WebUI 预览 API ✅

- [x] `GET /pallas/api/help/preview?level=menu|plugin|function`
- [x] WebUI `HelpImagePreview.vue`（help 插件配置页）

### Phase 6 — HTML 渲染器评估（可选）

- Jinja + Playwright POC

## 分页

- 每页 **20** 个插件（3 列网格）；序号仍为全局编号。
- 翻页口令：`牛牛帮助 2页` / `p2` / `第2页` / `页2`（不与 `牛牛帮助 2` 插件序号冲突）。

## 缓存

- v3 与 pillowmd 共用 `data/help/<群号|private>/` 下 PNG 磁盘缓存；`render_v3_image_bytes()` 先 `load_cached_image()`，未命中再 PIL 编码并 `save_image_to_cache()`。
- cache key：业务键（如 `menu_v1|…`）+ `style_name` + `_help_image_cache_suffix()`（含字体 mtime、样式文件 mtime、立绘配置、**插件包内 assets 摘要 `pkgvis=`** 等）。`pkgvis` 进程内约 **5 分钟** TTL，单次扫描各插件根目录下实际命中的 cover/icon/avatar（非全候选路径穷举）。
- 默认字体：`resource/fonts/SourceHanSerifCN-Regular.otf`（思源宋体 CN Regular）；可用 `PALLAS_HELP_V3_FONT` 覆盖。

## 样张

`docs/plugins/help/samples/`：

- `help-menu-v3-preview.png` / `help-menu-v3-preview-20.png`
- `help-plugin-detail-v3-*.png` / `help-function-detail-v3-*.png`

## 验收

- `牛牛帮助` 总览为卡片图，每插件有图标或色块 fallback
- 状态为绿/灰圆点 +「已启用/已停用」，与群开关一致
- 二/三级为 PIL 卡片，不再走 pillowmd 宽表
- WebUI help 配置页可预览 menu / plugin / function
- `uv run ruff check packages/help/` + `tests/plugins/help/test_draw_*.py` 等通过
