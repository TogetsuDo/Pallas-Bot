from __future__ import annotations

from src.platform.bot_runtime.load_policy import merge_startup_skip_plugins


def test_merge_startup_skip_plugins_merges_global_disable(tmp_path, monkeypatch) -> None:
    from src.plugins.help import global_disable

    monkeypatch.setattr(global_disable, "plugin_data_dir", lambda _name: tmp_path / "help")
    global_disable.save_global_disabled_plugins(["chat", "ollama"])

    merged = merge_startup_skip_plugins(frozenset({"maa_hub"}))
    assert merged == frozenset({"maa_hub", "chat", "ollama"})


def test_merge_startup_skip_plugins_keeps_protected_out(tmp_path, monkeypatch) -> None:
    from src.plugins.help import global_disable

    monkeypatch.setattr(global_disable, "plugin_data_dir", lambda _name: tmp_path / "help")
    global_disable.save_global_disabled_plugins(["help", "ingress_gate", "chat"])

    merged = merge_startup_skip_plugins(frozenset())
    assert "help" not in merged
    assert "ingress_gate" not in merged
    assert "chat" in merged
