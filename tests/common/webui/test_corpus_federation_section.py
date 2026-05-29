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
    assert "remote_find_enabled" in names
    assert "fed_enabled" not in names
    assert "on_remote_failure" not in names
    assert "reply_messages_cap" in names
    assert "reply_answers_cap" in names
    assert "find_cache_ttl_sec" in names
    assert len(data["field_groups"]) == 4
    reply_perf_group = next(g for g in data["field_groups"] if g["id"] == "reply_perf")
    assert reply_perf_group["title"] == "接话与查询性能"
    community = next(f for f in data["fields"] if f["name"] == "community_enabled")
    assert community["kind"] == "bool"
    assert isinstance(community["current"], bool)
    merge_order = next(f for f in data["fields"] if f["name"] == "merge_order")
    assert merge_order["kind"] == "enum"
    assert merge_order["choices"] == ["local,community", "local"]
    remote_find = next(f for f in data["fields"] if f["name"] == "remote_find_enabled")
    assert remote_find["kind"] == "enum"
    assert remote_find["choices"] == ["auto", "false", "prefetch", "sync"]


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


def test_apply_corpus_federation_patch_reply_perf(monkeypatch, tmp_path):
    from src.foundation.config import repo_settings as rs

    webui = tmp_path / "data" / "pallas_config" / "webui.json"
    webui.parent.mkdir(parents=True, exist_ok=True)
    webui.write_text('{"env": {}}', encoding="utf-8")
    monkeypatch.setattr(rs, "repo_webui_settings_path", lambda: webui)
    monkeypatch.setattr(rs, "_REPO_ROOT", tmp_path)

    out = apply_corpus_federation_patch({"reply_messages_cap": 32, "find_cache_ttl_sec": 60})
    cap_field = next(f for f in out["fields"] if f["name"] == "reply_messages_cap")
    assert cap_field["current"] == 32
    raw = webui.read_text(encoding="utf-8")
    assert "PALLAS_CORPUS_REPLY_MESSAGES_CAP" in raw
    assert "PALLAS_CORPUS_FIND_CACHE_SEC" in raw


def test_apply_corpus_federation_patch_rejects_unknown():
    import pytest

    with pytest.raises(ValueError, match="未知配置项"):
        apply_corpus_federation_patch({"fed_enabled": "true"})
