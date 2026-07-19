# 消息审查部署模板

依赖：

```bash
uv sync --extra message-scrub
```

应用：

```bash
uv run python tools/apply_deploy_profile.py message-scrub
```

重启 Bot 后，WebUI「通用配置 → 消息审查」可用。再配置词表或远程审查 API。

若已有 `PALLAS_SCRUB_*` 等历史配置，未设 `PALLAS_MESSAGE_SCRUB_ENABLED=false` 时仍会按旧行为启用审查（向后兼容）。

文档：[message_scrub](../../docs/common/message_scrub/README.md)
