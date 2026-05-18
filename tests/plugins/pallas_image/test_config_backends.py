from src.plugins.pallas_image.config import Config, ImageGenSettings


def test_api_backends_dedupe_same_url_key_model() -> None:
    cfg = Config(
        pallas_image_base_url="https://api.example.com/v1",
        pallas_image_api_key="sk-a",
        pallas_image_model="m1",
        pallas_image_api_backends=[
            {"base_url": "https://api.example.com/v1", "api_key": "sk-a", "model": "m1"},
        ],
    )
    backends = ImageGenSettings(cfg).api_backends()
    assert len(backends) == 1
    assert backends[0].label == "primary"
