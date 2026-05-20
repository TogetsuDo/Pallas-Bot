"""一次性规范化各插件 __init__.py 中的 homepage / menu_template。"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "src" / "plugins"
HOMEPAGE_NEW = "https://github.com/PallasBot/Pallas-Bot"
MENU_TEMPLATE_MISSING = {"maa", "block", "callback", "pallas_protocol", "pallas_webui"}


def patch_init(init: Path) -> bool:
    name = init.parent.name
    text = init.read_text(encoding="utf-8")
    orig = text
    text = text.replace('homepage="https://github.com/PallasBot"', f'homepage="{HOMEPAGE_NEW}"')
    if name in MENU_TEMPLATE_MISSING and '"menu_template"' not in text:
        for ver in ("3.0.0", "0.3.0"):
            needle = f'"version": "{ver}",'
            if needle in text:
                text = text.replace(needle, f'{needle}\n        "menu_template": "default",', 1)
                break
    if text != orig:
        init.write_text(text, encoding="utf-8")
        return True
    return False


def main() -> None:
    for init in sorted(ROOT.glob("*/__init__.py")):
        if init.parent.name == "ncm_login":
            continue
        if patch_init(init):
            print("updated", init.relative_to(ROOT.parents[1]))


if __name__ == "__main__":
    main()
