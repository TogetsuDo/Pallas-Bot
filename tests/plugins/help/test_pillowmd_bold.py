import importlib

from src.plugins.help import pillowmd_bold as bold_mod

custom_markdown_renderer = importlib.import_module("pillowmd.CustomMarkdownRenderer")


def test_apply_help_light_bold_patch_once() -> None:
    bold_mod._PATCHED = False
    bold_mod.apply_help_light_bold_patch(0.5)
    assert custom_markdown_renderer.ImageDrawPro.text is not custom_markdown_renderer.ImageDraw.ImageDraw.text
    fn = custom_markdown_renderer.ImageDrawPro.text
    bold_mod.apply_help_light_bold_patch(0.5)
    assert custom_markdown_renderer.ImageDrawPro.text is fn
