from src.common.webui.env_sections import get_webui_env_section
from src.plugins.repeater.learn_runtime_config import (
    RepeaterLearnRuntimeConfig,
    clear_repeater_learn_runtime_config_cache,
    get_repeater_learn_runtime_config,
)


def test_repeater_learn_webui_section_registered():
    s = get_webui_env_section("repeater_learn")
    assert s.id == "repeater_learn"
    assert "PALLAS_REPEATER_LEARN_CONCURRENCY" in s.field_to_env.values()


def test_repeater_learn_from_env(monkeypatch):
    monkeypatch.setenv("PALLAS_REPEATER_LEARN_CONCURRENCY", "8")
    monkeypatch.setenv("PALLAS_REPEATER_LEARN_QUEUE_SIZE", "512")
    clear_repeater_learn_runtime_config_cache()
    cfg = get_repeater_learn_runtime_config()
    assert cfg.learn_concurrency == 8
    assert cfg.learn_queue_max_size == 512
    assert RepeaterLearnRuntimeConfig.model_fields["learn_concurrency"].description
