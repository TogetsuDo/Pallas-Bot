"""从主仓 docs/plugins 读取已加载插件的 bundled README。"""

from __future__ import annotations

from pallas.core.foundation.paths import PROJECT_ROOT


def bundled_plugin_readme_relative_path(plugin_id: str) -> str | None:
    from pallas.core.platform.bot_runtime.plugin_matrix import (
        OFFICIAL_EXTENSION_README_PATHS,
        extra_package_for_plugin,
    )
    from pallas.core.platform.bot_runtime.plugin_package_aliases import canonical_plugin_package

    clean = canonical_plugin_package((plugin_id or "").strip())
    if not clean:
        return None

    pkg = extra_package_for_plugin(clean)
    if pkg:
        rel = OFFICIAL_EXTENSION_README_PATHS.get(pkg)
        if rel and (PROJECT_ROOT / rel).is_file():
            return rel

    candidates: list[str] = []
    for candidate in (clean, (plugin_id or "").strip()):
        if candidate and candidate not in candidates:
            candidates.append(candidate)
    for candidate in candidates:
        rel = f"docs/plugins/{candidate}/README.md"
        if (PROJECT_ROOT / rel).is_file():
            return rel
    return None


def read_bundled_plugin_readme(plugin_id: str) -> dict[str, str] | None:
    rel = bundled_plugin_readme_relative_path(plugin_id)
    if not rel:
        return None
    try:
        markdown = (PROJECT_ROOT / rel).read_text(encoding="utf-8")
    except OSError:
        return None
    if not markdown.strip():
        return None
    return {
        "plugin": canonical_plugin_id(plugin_id),
        "relative_path": rel,
        "markdown": markdown,
        "source": "bundled",
    }


def canonical_plugin_id(plugin_id: str) -> str:
    from pallas.core.platform.bot_runtime.plugin_package_aliases import canonical_plugin_package

    return canonical_plugin_package((plugin_id or "").strip())
