from src.plugins.pallas_webui.config import Config


def test_pallas_webui_api_token_coerces_numeric_to_str() -> None:
    assert Config(pallas_webui_api_token=1234).pallas_webui_api_token == "1234"
    assert Config(pallas_webui_api_token=12.5).pallas_webui_api_token == "12.5"
    assert Config(pallas_webui_api_token=None).pallas_webui_api_token == ""
    assert Config(pallas_webui_api_token="abc").pallas_webui_api_token == "abc"
