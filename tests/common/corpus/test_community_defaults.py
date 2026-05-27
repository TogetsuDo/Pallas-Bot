from src.features.corpus.config import clear_corpus_config_cache, is_community_corpus_wanted


def test_community_corpus_default_off(monkeypatch):
    monkeypatch.setattr(
        "src.features.corpus.config.repo_env_raw_value",
        lambda _key: None,
    )
    clear_corpus_config_cache()
    assert is_community_corpus_wanted() is False
    clear_corpus_config_cache()


def test_corpus_federation_payload_community_default_false():
    from src.console.webui.corpus_federation_section import corpus_federation_payload

    data = corpus_federation_payload()
    row = next(f for f in data["fields"] if f["name"] == "community_enabled")
    assert row["kind"] == "bool"
    assert row["current"] is False
