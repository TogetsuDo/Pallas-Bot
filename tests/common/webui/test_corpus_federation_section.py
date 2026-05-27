from src.console.webui.corpus_federation_section import (
    CORPUS_FEDERATION_SECTION_ID,
    apply_corpus_federation_patch,
    corpus_federation_payload,
)


def test_corpus_federation_payload_phase1():
    data = corpus_federation_payload()
    assert data["plugin"] == CORPUS_FEDERATION_SECTION_ID
    assert data.get("hot_reload") is True
    names = {f["name"] for f in data["fields"]}
    assert "merge_order" in names
    assert "community_enabled" in names
    assert "fed_enabled" not in names
    assert "on_remote_failure" not in names
    assert len(data["field_groups"]) == 3
    community = next(f for f in data["fields"] if f["name"] == "community_enabled")
    assert community["kind"] == "bool"
    assert community["current"] is False
    merge_order = next(f for f in data["fields"] if f["name"] == "merge_order")
    assert merge_order["kind"] == "enum"
    assert merge_order["choices"] == ["local,community", "local"]


def test_apply_corpus_federation_patch_writes_env(monkeypatch, tmp_path):
    from src.foundation.config import repo_settings as rs

    webui = tmp_path / "data" / "pallas_config" / "webui.json"
    webui.parent.mkdir(parents=True, exist_ok=True)
    webui.write_text('{"env": {}}', encoding="utf-8")
    monkeypatch.setattr(rs, "repo_webui_settings_path", lambda: webui)
    monkeypatch.setattr(rs, "_REPO_ROOT", tmp_path)

    out = apply_corpus_federation_patch({"community_contribute": "false", "community_enabled": False})
    assert out["fields"]
    raw = webui.read_text(encoding="utf-8")
    assert "PALLAS_CORPUS_COMMUNITY_CONTRIBUTE" in raw
    assert "PALLAS_CORPUS_COMMUNITY_ENABLED" in raw


def test_apply_corpus_federation_patch_rejects_unknown():
    import pytest

    with pytest.raises(ValueError, match="未知配置项"):
        apply_corpus_federation_patch({"fed_enabled": "true"})
