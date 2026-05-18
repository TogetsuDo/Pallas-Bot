from src.plugins.pallas_image.image_request_options import (
    ImageGenRequestOptions,
    image_gen_request_attempts,
    response_format_attempts,
)


def test_response_format_attempts_b64_json() -> None:
    assert response_format_attempts("b64_json") == ["b64_json", "url"]


def test_image_gen_request_attempts_starts_with_config() -> None:
    attempts = image_gen_request_attempts(with_ref_urls=False)
    assert attempts
    assert attempts[0] == ImageGenRequestOptions.from_config()


def test_image_gen_request_attempts_includes_alt_response_format() -> None:
    attempts = image_gen_request_attempts(with_ref_urls=False)
    formats = {a.response_format for a in attempts if a.response_format}
    assert "b64_json" in formats
    assert "url" in formats


def test_image_gen_request_attempts_ref_image_variant() -> None:
    attempts = image_gen_request_attempts(with_ref_urls=True)
    assert any(not a.include_ref_images for a in attempts)


def test_image_gen_request_attempts_relaxed_minimal() -> None:
    attempts = image_gen_request_attempts(with_ref_urls=False)
    assert any(
        not a.size and not a.aspect_ratio and not a.quality and a.response_format
        for a in attempts
    )
