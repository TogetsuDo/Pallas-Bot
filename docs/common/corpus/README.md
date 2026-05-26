# 语料联邦（corpus）

自托管部署默认使用 **本地 PostgreSQL/Mongo 语料**（`local`）。可选接入 **stats 中心社区池**（`community`）作多读源 complement；**联邦 PG**（`fed`）为 Phase 2，当前未接入读写。

设计细节见 [控制面与语料联邦](../architecture/control-plane-corpus-federation.md)；中心服务见 [Pallas-Bot-Community-Stats](https://github.com/TogetsuDo/Pallas-Bot-Community-Stats)。

## 三档语料源

| 源 | 存储 | 典型用途 | 当前状态 |
| --- | --- | --- | --- |
| **local** | 本部署业务库 | 主读写、ban/清理 | ✅ 默认 |
| **fed** | 第二 PG（`PG_CORPUS_FED_*`） | 同联邦多部署共享 | ⏳ Phase 2，未接第二连接 |
| **community** | stats 中心 `/v1/corpus` | opt-in 公共池 | ✅ WebUI 开启后 auto enroll |

默认读顺序：`local → community`（Phase 1 WebUI 默认 `local,community`；未开 community 时仅 local）。远端失败时 `on_remote_failure = local_only`，不阻塞启动。

## 默认行为（升级后）

- **[community_stats](../common/community_stats.md)** 默认开启：hub/单进程向 `stats.pallasbot.top` 上报心跳（备案前自动回退 `pallas.togetsudo.com`）；**不出现在用户帮助总览**。
- **社区语料默认关闭**：需在 WebUI **语料联邦** 打开 `community_enabled` 后才会 auto enroll 与读 community 源。
- 开启 community 后 **auto enroll** 默认 `auto`：向 stats `POST /v1/corpus/enroll`，token 落盘 `community_stats.json` 的 `corpus_community` 段。
- **community_contribute** 默认 **auto（开）**：学习结果可异步 mirror 到社区池（`group_id=0`）；可显式 `false` 关闭写回。
- 语料 HTTP 读路径与心跳共用主/备域名 **failover**。

手动配置 `[corpus.community] token` + `api_base` 时跳过 auto enroll。

## 配置

### WebUI（推荐）

控制台 **数据与扩展 → 语料联邦**（`/pallas/corpus-config`）：多读源开关、merge、community、心跳 interval 等；保存写入 `webui.json`。

首页 **社区与语料** 面板为只读状态；**语料配置** 链到上述页面。

### `config/pallas.toml`（可选）

```toml
[corpus]
community_enabled = false       # 默认关；true 或在 WebUI 开启后接入 community
auto_enroll = "auto"
community_contribute = "auto"   # 开启 community 后默认允许写回；关闭写回：false
on_remote_failure = "local_only"

# 手动 token（跳过 auto enroll）：
# [corpus.community]
# api_base = "https://stats.pallasbot.top/v1/corpus"
# token = "pc_..."
```

等价环境变量：`PALLAS_CORPUS_*`（见 `src/common/corpus/config.py`）。

### 开启社区语料

控制台 **语料联邦** 打开「社区语料」开关，或：

```toml
[corpus]
community_enabled = true
```

### 关闭社区语料

```toml
[corpus]
community_enabled = false
# 或仅关写回：
# community_contribute = false
```

关闭心跳（同时不再有 auto enroll）：

```toml
[community_stats]
enabled = false
```

## 运维与 API

| 项 | 说明 |
| --- | --- |
| 状态 API | `GET /pallas/api/corpus-status`（含中心 `GET /v1/corpus/usage` 代理的本部署用量） |
| 社区聚合 | `GET /pallas/api/community-stats`（含中心 `corpus.*` 计数） |
| 预灌工具 | `uv run python tools/seed_community_corpus.py`（运维向中心贡献样本） |
| 落盘 | `data/pallas_config/community_stats.json`（`deployment_id` + `corpus_community`） |

## 隐私

- contribute 仅上传 `keywords` 与短句，匿名 `group_id=0`。
- 中心不可达时接话/学习仍走 local；mirror 失败不 retry 风暴。

## 相关

- [社区统计 heartbeat](../common/community_stats.md)
- [配置存储](../architecture/settings-storage.md)
