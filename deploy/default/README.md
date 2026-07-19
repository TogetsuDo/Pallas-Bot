# 默认部署（单进程）

```bash
uv sync
cp config/pallas.example.toml config/pallas.toml
nb run
```

不设置 `PALLAS_SHARD_ENABLED`、不启用 `PALLAS_MESSAGE_SCRUB_ENABLED`（且无历史审查配置）时，Bot 以 unified 角色运行全部插件。
