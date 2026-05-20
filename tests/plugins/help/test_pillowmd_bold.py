import pillowmd.CustomMarkdownRenderer as cmr

from src.plugins.help import pillowmd_bold as bold_mod


def test_apply_help_light_bold_patch_once() -> None:
    bold_mod._PATCHED = False
    bold_mod.apply_help_light_bold_patch(0.5)
    assert cmr.ImageDrawPro.text is not cmr.ImageDraw.ImageDraw.text
    fn = cmr.ImageDrawPro.text
    bold_mod.apply_help_light_bold_patch(0.5)
    assert cmr.ImageDrawPro.text is fn
