from packages.repeater.learn_runtime_config import (
    RepeaterLearnRuntimeConfig,
    clear_repeater_learn_runtime_config_cache,
    get_repeater_learn_runtime_config,
)
from pallas.console.webui.env_sections import get_webui_env_section


def test_repeater_learn_webui_section_registered():
    s = get_webui_env_section("repeater_learn")
    assert s.id == "repeater_learn"
    assert "PALLAS_REPEATER_LEARN_CONCURRENCY" in s.field_to_env.values()


def test_repeater_learn_from_env(monkeypatch):
    def fake_raw(name_upper: str):
        if name_upper == "PALLAS_REPEATER_LEARN_CONCURRENCY":
            return "8"
        if name_upper == "PALLAS_REPEATER_LEARN_QUEUE_SIZE":
            return "512"
        return None

    monkeypatch.setattr(
        "packages.repeater.learn_runtime_config.repo_env_raw_value",
        fake_raw,
    )
    clear_repeater_learn_runtime_config_cache()
    cfg = get_repeater_learn_runtime_config()
    assert cfg.learn_concurrency == 8
    assert cfg.learn_queue_max_size == 512
    assert RepeaterLearnRuntimeConfig.model_fields["learn_concurrency"].description
