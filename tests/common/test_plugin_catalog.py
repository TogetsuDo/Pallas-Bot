from pallas.console.webui.plugin_catalog import (
    build_plugin_catalog_rows,
    discover_extra_plugin_packages,
    discover_plugin_packages,
    discover_pyproject_plugin_modules,
    expected_loaded_in_catalog_process,
    infer_plugin_source,
    package_load_role,
    plugin_source_from_module_path,
)


def test_discover_bundled_packages():
    pkgs = discover_plugin_packages()
    assert "draw" not in pkgs  # pip 扩展，不在 packages/
    assert "pb_webui" in pkgs
    assert "ingress_gate" not in pkgs


def test_package_load_role_sharded(monkeypatch):
    monkeypatch.setenv("PALLAS_SHARD_ENABLED", "true")
    monkeypatch.setenv("PALLAS_BOT_ROLE", "hub")
    from pallas.core.platform.shard.registry.config import get_shard_registry_settings

    get_shard_registry_settings.cache_clear()
    assert package_load_role("draw") == "worker"
    assert package_load_role("ingress_gate") == "worker"
    assert package_load_role("pb_webui") == "hub"


def test_expected_loaded_in_catalog_hub_vs_worker():
    assert expected_loaded_in_catalog_process("worker", "hub") is False
    assert expected_loaded_in_catalog_process("hub", "hub") is True
    assert expected_loaded_in_catalog_process("infra", "hub") is True
    assert expected_loaded_in_catalog_process("worker", "worker") is True
    assert expected_loaded_in_catalog_process("hub", "worker") is False


def test_expected_loaded_in_catalog_unified():
    assert expected_loaded_in_catalog_process("both", "unified") is True
    assert expected_loaded_in_catalog_process("infra", "unified") is True
    assert expected_loaded_in_catalog_process("hub", "unified") is False
    assert expected_loaded_in_catalog_process("worker", "unified") is False
    assert expected_loaded_in_catalog_process("internal", "unified") is False


def test_catalog_hides_shard_only_in_unified(monkeypatch):
    monkeypatch.delenv("PALLAS_SHARD_ENABLED", raising=False)
    monkeypatch.delenv("PALLAS_BOT_ROLE", raising=False)
    monkeypatch.setattr(
        "pallas.core.foundation.config.repo_settings.read_bootstrap_extra_plugin_dirs",
        list,
    )
    from pallas.core.platform.shard.registry.config import get_shard_registry_settings

    get_shard_registry_settings.cache_clear()
    rows = build_plugin_catalog_rows()
    names = {r["name"] for r in rows}
    assert "relogin_forward" not in names
    assert "maa_hub" not in names
    assert "ingress_gate" not in names
    assert "pallas_console_metrics" not in names
    assert "relogin_bot" in names
    assert "maa" in names
    assert rows[0]["catalog_process_role"] == "unified"


def test_catalog_shows_shard_only_on_sharded_hub(monkeypatch):
    monkeypatch.setenv("PALLAS_SHARD_ENABLED", "true")
    monkeypatch.setenv("PALLAS_BOT_ROLE", "hub")
    monkeypatch.setattr(
        "pallas.core.foundation.config.repo_settings.read_bootstrap_extra_plugin_dirs",
        list,
    )
    from pallas.core.platform.shard.registry.config import get_shard_registry_settings

    get_shard_registry_settings.cache_clear()
    rows = build_plugin_catalog_rows()
    names = {r["name"] for r in rows}
    assert "relogin_forward" in names
    assert "maa_hub" in names
    assert "ingress_gate" not in names


def test_catalog_lists_worker_plugin(monkeypatch):
    monkeypatch.setenv("PALLAS_SHARD_ENABLED", "true")
    monkeypatch.setenv("PALLAS_BOT_ROLE", "hub")
    monkeypatch.setattr(
        "pallas.core.foundation.config.repo_settings.read_bootstrap_extra_plugin_dirs",
        list,
    )
    from pallas.core.platform.shard.registry.config import get_shard_registry_settings

    get_shard_registry_settings.cache_clear()
    rows = build_plugin_catalog_rows()
    by_name = {r["name"]: r for r in rows}
    assert "duel" in by_name
    assert by_name["duel"]["load_role"] == "worker"
    assert by_name["duel"]["metadata"] is not None
    assert by_name["duel"]["plugin_source"] == "extra"
    assert by_name["duel"].get("extra_package") == "pallas-plugin-duel"
    assert by_name["duel"]["catalog_process_role"] == "hub"
    assert by_name["duel"]["expected_in_catalog_process"] is False
    assert by_name["pb_webui"]["expected_in_catalog_process"] is True


def test_infer_plugin_source_local_dir(tmp_path, monkeypatch) -> None:
    root = tmp_path / "repo"
    pkg = root / "local" / "plugins" / "demo"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("x = 1\n", encoding="utf-8")
    monkeypatch.setattr("pallas.console.webui.plugin_catalog.PROJECT_ROOT", root)
    monkeypatch.setattr(
        "pallas.core.foundation.config.repo_settings.read_bootstrap_extra_plugin_dirs",
        lambda: ["local/plugins"],
    )
    extra = discover_extra_plugin_packages()
    assert "demo" in extra
    src, dir_posix = infer_plugin_source("demo", None, extra_pkgs=extra)
    assert src == "local"
    assert dir_posix == "local/plugins/demo"


def test_plugin_source_from_core_path() -> None:
    from pallas.core.foundation.paths import PROJECT_ROOT

    main_py = PROJECT_ROOT / "packages" / "help" / "__init__.py"
    assert main_py.is_file()
    assert plugin_source_from_module_path(str(main_py)) == "core"


def test_discover_pyproject_includes_status():
    modules = discover_pyproject_plugin_modules()
    assert "nonebot_plugin_status" in modules


def test_catalog_lists_pyproject_status_on_hub(monkeypatch):
    monkeypatch.setenv("PALLAS_SHARD_ENABLED", "true")
    monkeypatch.setenv("PALLAS_BOT_ROLE", "hub")
    monkeypatch.setattr(
        "pallas.core.foundation.config.repo_settings.read_bootstrap_extra_plugin_dirs",
        list,
    )
    from pallas.core.platform.shard.registry.config import get_shard_registry_settings

    get_shard_registry_settings.cache_clear()
    rows = build_plugin_catalog_rows()
    by_name = {r["name"]: r for r in rows}
    assert "nonebot_plugin_status" in by_name
    row = by_name["nonebot_plugin_status"]
    assert row["plugin_source"] == "pip"
    assert row["load_role"] == "infra"


def test_resolve_catalog_prefers_local_draw(tmp_path, monkeypatch) -> None:
    root = tmp_path / "repo"
    local_pkg = root / "local" / "plugins" / "draw"
    local_pkg.mkdir(parents=True)
    (local_pkg / "__init__.py").write_text("x = 1\n", encoding="utf-8")
    src_pkg = root / "packages" / "draw"
    src_pkg.mkdir(parents=True)
    (src_pkg / "__init__.py").write_text("x = 1\n", encoding="utf-8")
    monkeypatch.setattr("pallas.console.webui.plugin_catalog.PROJECT_ROOT", root)
    monkeypatch.setattr(
        "pallas.core.foundation.config.repo_settings.read_bootstrap_extra_plugin_dirs",
        lambda: ["local/plugins"],
    )
    from pallas.console.webui.plugin_catalog import resolve_catalog_plugin_module

    assert resolve_catalog_plugin_module("draw") == "local.plugins.draw"


def test_catalog_marks_pyproject_plugin_with_config(monkeypatch) -> None:
    monkeypatch.setattr(
        "pallas.console.webui.plugin_catalog.discover_plugin_packages",
        list,
    )
    monkeypatch.setattr(
        "pallas.console.webui.plugin_catalog.discover_extra_plugin_packages",
        dict,
    )
    monkeypatch.setattr(
        "pallas.console.webui.plugin_catalog.discover_pyproject_plugin_modules",
        lambda: ["acme_demo_plugin"],
    )
    monkeypatch.setattr(
        "pallas.console.webui.plugin_catalog._loaded_plugin_index",
        lambda: ({}, {}),
    )
    monkeypatch.setattr(
        "pallas.console.webui.plugin_catalog._pip_plugin_metadata_stub",
        lambda _module_path: {"name": "acme_demo_plugin"},
    )
    monkeypatch.setattr(
        "pallas.console.webui.plugin_catalog.package_has_config_module",
        lambda package, *, package_root=None: False,
    )
    monkeypatch.setattr(
        "pallas.console.webui.plugin_catalog.module_has_config_module",
        lambda module_name: module_name == "acme_demo_plugin",
    )

    rows = build_plugin_catalog_rows()
    by_name = {r["name"]: r for r in rows}

    assert by_name["acme_demo_plugin"]["plugin_source"] == "pip"
    assert by_name["acme_demo_plugin"]["has_config"] is True


def test_catalog_exposes_resolved_identity_for_official_pip_plugin(monkeypatch) -> None:
    class FakeLoadedPlugin:
        name = "pallas_plugin_draw"
        module = type(
            "Mod",
            (),
            {"__name__": "pallas_plugin_draw", "__file__": "/tmp/site-packages/pallas_plugin_draw/__init__.py"},
        )()
        metadata = None

    monkeypatch.setattr(
        "pallas.console.webui.plugin_catalog.discover_plugin_packages",
        list,
    )
    monkeypatch.setattr(
        "pallas.console.webui.plugin_catalog.discover_extra_plugin_packages",
        dict,
    )
    monkeypatch.setattr(
        "pallas.console.webui.plugin_catalog.discover_pyproject_plugin_modules",
        lambda: ["pallas_plugin_draw"],
    )
    monkeypatch.setattr(
        "pallas.console.webui.plugin_catalog._loaded_plugin_index",
        lambda: ({}, {"draw": FakeLoadedPlugin()}),
    )
    monkeypatch.setattr(
        "pallas.console.webui.plugin_catalog._pip_plugin_metadata_stub",
        lambda _module_path: {"name": "牛牛画画"},
    )
    monkeypatch.setattr(
        "pallas.console.webui.plugin_catalog.module_has_config_module",
        lambda module_name: module_name == "pallas_plugin_draw",
    )

    rows = build_plugin_catalog_rows()
    by_name = {r["name"]: r for r in rows}
    row = by_name["draw"]

    assert row["resolved_plugin_id"] == "draw"
    assert row["resolved_module"] == "pallas_plugin_draw"
    assert row["configurable"] is True
    assert row["extra_package"] == "pallas-plugin-draw"
