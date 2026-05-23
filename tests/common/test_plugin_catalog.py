from src.common.webui.plugin_catalog import (
    build_plugin_catalog_rows,
    discover_extra_plugin_packages,
    discover_plugin_packages,
    infer_plugin_source,
    package_load_role,
    plugin_source_from_module_path,
)


def test_discover_includes_pallas_image():
    pkgs = discover_plugin_packages()
    assert "pallas_image" in pkgs
    assert "pallas_webui" in pkgs
    assert "_ingress_gate" in pkgs
    assert "pallas_console_metrics" in pkgs


def test_package_load_role_sharded(monkeypatch):
    monkeypatch.setenv("PALLAS_SHARD_ENABLED", "true")
    monkeypatch.setenv("PALLAS_BOT_ROLE", "hub")
    from src.common.shard.registry.config import get_shard_registry_settings

    get_shard_registry_settings.cache_clear()
    assert package_load_role("pallas_image") == "worker"
    assert package_load_role("pallas_webui") == "hub"
    assert package_load_role("callback") == "hub"


def test_catalog_lists_worker_plugin(monkeypatch):
    monkeypatch.setenv("PALLAS_SHARD_ENABLED", "true")
    monkeypatch.setenv("PALLAS_BOT_ROLE", "hub")
    monkeypatch.setattr(
        "src.common.config.repo_settings.read_bootstrap_extra_plugin_dirs",
        lambda: [],
    )
    from src.common.shard.registry.config import get_shard_registry_settings

    get_shard_registry_settings.cache_clear()
    rows = build_plugin_catalog_rows()
    by_name = {r["name"]: r for r in rows}
    assert "pallas_image" in by_name
    assert by_name["pallas_image"]["load_role"] == "worker"
    assert by_name["pallas_image"]["metadata"] is not None
    assert by_name["pallas_image"]["plugin_source"] == "main"


def test_infer_plugin_source_local_dir(tmp_path, monkeypatch) -> None:
    root = tmp_path / "repo"
    pkg = root / "local" / "plugins" / "demo"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("x = 1\n", encoding="utf-8")
    monkeypatch.setattr("src.common.webui.plugin_catalog.PROJECT_ROOT", root)
    monkeypatch.setattr(
        "src.common.config.repo_settings.read_bootstrap_extra_plugin_dirs",
        lambda: ["local/plugins"],
    )
    extra = discover_extra_plugin_packages()
    assert "demo" in extra
    src, dir_posix = infer_plugin_source("demo", None, extra_pkgs=extra)
    assert src == "local"
    assert dir_posix == "local/plugins/demo"


def test_plugin_source_from_main_path() -> None:
    from src.common.paths import PROJECT_ROOT

    main_py = PROJECT_ROOT / "src" / "plugins" / "callback" / "handler.py"
    if main_py.is_file():
        assert plugin_source_from_module_path(str(main_py)) == "main"


def test_resolve_catalog_prefers_local_pallas_image(tmp_path, monkeypatch) -> None:
    root = tmp_path / "repo"
    local_pkg = root / "local" / "plugins" / "pallas_image"
    local_pkg.mkdir(parents=True)
    (local_pkg / "__init__.py").write_text("x = 1\n", encoding="utf-8")
    src_pkg = root / "src" / "plugins" / "pallas_image"
    src_pkg.mkdir(parents=True)
    (src_pkg / "__init__.py").write_text("x = 1\n", encoding="utf-8")
    monkeypatch.setattr("src.common.webui.plugin_catalog.PROJECT_ROOT", root)
    monkeypatch.setattr(
        "src.common.config.repo_settings.read_bootstrap_extra_plugin_dirs",
        lambda: ["local/plugins"],
    )
    from src.common.webui.plugin_catalog import resolve_catalog_plugin_module

    assert resolve_catalog_plugin_module("pallas_image") == "local.plugins.pallas_image"
