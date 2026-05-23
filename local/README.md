# 站点本地扩展（不随主仓 git 更新覆盖）

将自有 NoneBot 插件放在 `local/plugins/<name>/`（需含 `__init__.py`），并在 `config/pallas.toml` 的 `[bootstrap]` 中启用：

```toml
extra_plugin_dirs = ["local/plugins"]
```

`patches/` 仅作文档与手工补丁说明，不会被 Bot 自动加载。详见 [站点定制与更新](../docs/architecture/site-customization-and-updates.md)。
