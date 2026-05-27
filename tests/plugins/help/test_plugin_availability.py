from types import SimpleNamespace
from unittest.mock import patch

from src.plugins.help.plugin_availability import is_plugin_help_available


def test_config_gated_plugin_hidden_when_disabled():
    cfg = SimpleNamespace(ollama_enable=False)
    with patch("src.plugins.ollama.config.get_ollama_config", return_value=cfg):
        assert is_plugin_help_available("ollama") is False


def test_config_gated_plugin_shown_when_enabled():
    cfg = SimpleNamespace(sing_enable=True)
    with patch("src.plugins.sing.config.get_sing_config", return_value=cfg):
        assert is_plugin_help_available("sing") is True


def test_unlisted_plugin_always_available():
    assert is_plugin_help_available("draw") is True
