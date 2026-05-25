from src.common.webui.corpus_federation_section import (
    CORPUS_FEDERATION_SECTION_ID,
    apply_corpus_federation_patch,
    corpus_federation_payload,
)


def test_corpus_federation_payload_has_groups():
    data = corpus_federation_payload()
    assert data["plugin"] == CORPUS_FEDERATION_SECTION_ID
    names = {f["name"] for f in data["fields"]}
    assert "merge_order" in names
    assert "community_stats_endpoint" in names
    assert len(data["field_groups"]) >= 4


def test_apply_corpus_federation_patch_writes_env(monkeypatch, tmp_path):
    from src.common.config import repo_settings as rs

    webui = tmp_path / "data" / "pallas_config" / "webui.json"
    webui.parent.mkdir(parents=True, exist_ok=True)
    webui.write_text('{"env": {}}', encoding="utf-8")
    monkeypatch.setattr(rs, "repo_webui_settings_path", lambda: webui)
    monkeypatch.setattr(rs, "_REPO_ROOT", tmp_path)

    out = apply_corpus_federation_patch({"community_contribute": "false"})
    assert out["fields"]
    raw = webui.read_text(encoding="utf-8")
    assert "PALLAS_CORPUS_COMMUNITY_CONTRIBUTE" in raw
