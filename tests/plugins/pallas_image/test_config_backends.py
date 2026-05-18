from src.plugins.pallas_image.config import Config, ImageGenSettings


def test_api_backends_dedupe_same_url_key_model() -> None:
    cfg = Config(
        pallas_image_base_url="https://api.example.com/",
        pallas_image_api_key="sk-a",
        pallas_image_model="m1",
        pallas_image_api_backends=[
            {"base_url": "https://api.example.com/", "api_key": "sk-a", "model": "m1"},
        ],
    )
    backends = ImageGenSettings(cfg).api_backends()
    assert len(backends) == 1
    assert backends[0].label == "primary"


def test_api_backends_propagate_omit_response_format() -> None:
    cfg = Config(
        pallas_image_base_url="https://api.example.com/",
        pallas_image_api_key="sk-a",
        pallas_image_model="m1",
        pallas_image_api_backends=[
            {
                "base_url": "https://gateway.example.net/api/",
                "api_key": "sk-b",
                "model": "m2",
                "omit_response_format": True,
            },
        ],
    )
    backends = ImageGenSettings(cfg).api_backends()
    assert len(backends) == 2
    assert backends[0].omit_response_format is False
    assert backends[1].omit_response_format is True
