#!/usr/bin/env python3
"""将主仓 docs/ 同步到 Pallas-Bot-Docs 的 VitePress src/。"""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS = REPO_ROOT / "docs"

# docs/ 相对路径 -> VitePress src/ 相对路径
# 权威入口：maintainer/ + developer/；guide/plugins/common/architecture 保留兼容与素材
FILE_MAP: dict[str, str] = {
    # --- Maintainer（运维权威）---
    "maintainer/quickstart.md": "maintainer/quickstart.md",
    "maintainer/install/bot.md": "maintainer/install/bot.md",
    "maintainer/install/webui.md": "maintainer/install/webui.md",
    "maintainer/install/protocol.md": "maintainer/install/protocol.md",
    "maintainer/install/official-extensions.md": "maintainer/install/official-extensions.md",
    "maintainer/install/ai-runtime.md": "maintainer/install/ai-runtime.md",
    "maintainer/install/ga-install-checklist.md": "maintainer/install/ga-install-checklist.md",
    "maintainer/deploy/single-process.md": "maintainer/deploy/single-process.md",
    "maintainer/deploy/docker.md": "maintainer/deploy/docker.md",
    "maintainer/deploy/sharded.md": "maintainer/deploy/sharded.md",
    "maintainer/deploy/upgrade.md": "maintainer/deploy/upgrade.md",
    "maintainer/operate/webui.md": "maintainer/operate/webui.md",
    "maintainer/operate/llm-and-ai.md": "maintainer/operate/llm-and-ai.md",
    "maintainer/operate/command-permissions.md": "maintainer/operate/command-permissions.md",
    "maintainer/operate/plugin-governance.md": "maintainer/operate/plugin-governance.md",
    "maintainer/operate/troubleshooting.md": "maintainer/operate/troubleshooting.md",
    "maintainer/operate/hot-reload-pre-reload-checklist.md": (
        "maintainer/operate/hot-reload-pre-reload-checklist.md"
    ),
    "maintainer/reference/config.md": "maintainer/reference/config.md",
    "maintainer/reference/cli.md": "maintainer/reference/cli.md",
    "maintainer/reference/api.md": "maintainer/reference/api.md",
    "maintainer/reference/glossary.md": "maintainer/reference/glossary.md",
    # --- Developer（开发权威）---
    "developer/index.md": "developer/index.md",
    "developer/author/index.md": "developer/author/index.md",
    "developer/architecture/overview.md": "developer/architecture/overview.md",
    "developer/architecture/core-vs-extensions.md": "developer/architecture/core-vs-extensions.md",
    "developer/architecture/config-storage.md": "developer/architecture/config-storage.md",
    "developer/architecture/plugin-governance.md": "developer/architecture/plugin-governance.md",
    "developer/architecture/shard-runtime.md": "developer/architecture/shard-runtime.md",
    "developer/plugin-development/getting-started.md": (
        "developer/plugin-development/getting-started.md"
    ),
    "developer/plugin-development/first-plugin.md": (
        "developer/plugin-development/first-plugin.md"
    ),
    "developer/plugin-development/golden-plugin.md": (
        "developer/plugin-development/golden-plugin.md"
    ),
    "developer/plugin-development/metadata.md": "developer/plugin-development/metadata.md",
    "developer/plugin-development/config-and-webui.md": (
        "developer/plugin-development/config-and-webui.md"
    ),
    "developer/plugin-development/dynamic-config-panel.md": (
        "developer/plugin-development/dynamic-config-panel.md"
    ),
    "developer/plugin-development/reload-and-activation.md": (
        "developer/plugin-development/reload-and-activation.md"
    ),
    "developer/plugin-development/knowledge-sources.md": (
        "developer/plugin-development/knowledge-sources.md"
    ),
    "developer/plugin-development/pallas-api-cookbook.md": (
        "developer/plugin-development/pallas-api-cookbook.md"
    ),
    "developer/plugin-development/testing.md": "developer/plugin-development/testing.md",
    "developer/plugin-development/publishing.md": "developer/plugin-development/publishing.md",
    "developer/reference/repo-layout.md": "developer/reference/repo-layout.md",
    "developer/reference/platform-api.md": "developer/reference/platform-api.md",
    "developer/reference/internal-api.md": "developer/reference/internal-api.md",
    "developer/reference/console-api-response.md": "developer/reference/console-api-response.md",
    # --- 兼容：根部署页 / FAQ ---
    "Deployment.md": "deploy/deployment.md",
    "DockerDeployment.md": "deploy/docker.md",
    "Config.md": "deploy/config.md",
    "FAQ.md": "deploy/faq.md",
    "Migration-v3.md": "about/migration.md",
    # --- 素材：architecture / common / develop 兼容 ---
    "architecture/settings-storage.md": "architecture/settings-storage.md",
    "architecture/bot_process_sharding.md": "architecture/bot-process-sharding.md",
    "architecture/site-customization-and-updates.md": (
        "architecture/site-customization-and-updates.md"
    ),
    "architecture/plugin-convention.md": "architecture/plugin-convention.md",
    "architecture/hot-reload-tiers.md": "architecture/hot-reload-tiers.md",
    "architecture/ingress-pipeline.md": "architecture/ingress-pipeline.md",
    "common/community_stats.md": "common/community_stats.md",
    "common/corpus/README.md": "common/corpus.md",
    "common/cmd_perm/README.md": "common/cmd_perm.md",
    "common/command_limits/README.md": "common/command_limits.md",
    "common/webui/README.md": "common/webui.md",
    "common/message_scrub/README.md": "common/message_scrub.md",
    # --- Architecture internal（开发者深度材料，须上站避免 404）---
    "architecture/internal/pallas-core-contract.md": "architecture/internal/pallas-core-contract.md",
    "architecture/internal/core-plugin-unification-design.md": (
        "architecture/internal/core-plugin-unification-design.md"
    ),
    "architecture/internal/pallas-package-layout.md": "architecture/internal/pallas-package-layout.md",
    "architecture/internal/central-ingress-dispatch.md": (
        "architecture/internal/central-ingress-dispatch.md"
    ),
    "architecture/internal/pallas-final-ai-shape.md": "architecture/internal/pallas-final-ai-shape.md",
    "architecture/internal/pallas-ai-implementation.md": (
        "architecture/internal/pallas-ai-implementation.md"
    ),
    "plugins/README.md": "plugins/index.md",
    "develop/README.md": "develop/index.md",
    "develop/environment.md": "develop/environment.md",
    "develop/workflow.md": "develop/workflow.md",
    "develop/webui.md": "develop/webui.md",
    "develop/knowledge-sources.md": "develop/knowledge-sources.md",
    # --- Guide 上手 ---
    "guide/quickstart.md": "guide/quickstart.md",
    "guide/connect-qq.md": "guide/connect-qq.md",
    "guide/install-extensions.md": "guide/install-extensions.md",
    "guide/install-plugins.md": "guide/install-plugins.md",
    "guide/advanced.md": "guide/advanced.md",
    "guide/web-console.md": "guide/web-console.md",
    "guide/ai.md": "guide/ai.md",
    "guide/usage.md": "guide/usage.md",
    "guide/concepts.md": "guide/concepts.md",
    "guide/welcome.md": "guide/welcome.md",
    "guide/4.0-start.md": "guide/4.0-start.md",
    "guide/4.0-migration.md": "guide/4.0-migration.md",
    "guide/community-plugin-store.md": "guide/community-plugin-store.md",
    "guide/community-plugin-author.md": "guide/community-plugin-author.md",
    "guide/llm-and-repeater.md": "guide/llm-and-repeater.md",
    "guide/llm-migrate-from-ollama.md": "guide/llm-migrate-from-ollama.md",
    "user/README.md": "guide/usage-admin.md",
    "develop/extension-pypi-publish.md": "develop/extension-pypi-publish.md",
}

PLUGIN_NAMES = [
    "blacklist",
    "bot_status",
    "chat",
    "dream",
    "drink",
    "duel",
    "greeting",
    "help",
    "maa",
    "draw",
    "pb_protocol",
    "pb_webui",
    "pb_core",
    "pb_stats",
    "relogin_bot",
    "repeater",
    "request_handler",
    "roulette",
    "sing",
    "who_is_spy",
    "llm_chat",
    "persona",
    "take_name",
]

for name in PLUGIN_NAMES:
    FILE_MAP[f"plugins/{name}/README.md"] = f"plugins/{name}.md"

# 历史站内路径别名（Docs 仓旧链接）
FILE_MAP["plugins/pb_webui/README.md"] = "plugins/pb_webui.md"
FILE_MAP["plugins/pb_protocol/README.md"] = "plugins/pb_protocol.md"

GITHUB_SRC = "https://github.com/PallasBot/Pallas-Bot/tree/main/pallas/"


def transform_for_vitepress(text: str) -> str:
    """相对链接 -> VitePress 站内路径；源码路径 -> GitHub。"""
    # 插件 README 头像：主仓相对路径 -> Docs 公共静态资源（勿用站 logo）
    text = text.replace("../assets/brand-avatar.png", "/assets/brand-avatar.png")
    text = text.replace("./assets/brand-avatar.png", "/assets/brand-avatar.png")
    text = re.sub(r"(?<![./])assets/brand-avatar\.png", "/assets/brand-avatar.png", text)
    # 深度架构 / 技能 / 源码：站内或 GitHub，避免相对路径 404
    text = re.sub(
        r"\]\((?:\.\./)*(architecture/internal/[a-z0-9_-]+)\.md([^)]*)\)",
        r"](/\1\2)",
        text,
    )
    text = re.sub(
        r"\]\((?:\.\./)*architecture/hot-reload-tiers\.md([^)]*)\)",
        r"](/architecture/hot-reload-tiers\1)",
        text,
    )
    text = re.sub(
        r"\]\((?:\.\./)*architecture/settings-storage\.md([^)]*)\)",
        r"](/architecture/settings-storage\1)",
        text,
    )
    text = re.sub(
        r"\]\((?:\.\./)*architecture/bot_process_sharding\.md([^)]*)\)",
        r"](/architecture/bot-process-sharding\1)",
        text,
    )
    text = re.sub(
        r"\]\((?:\.\./)*common/command_limits/README\.md([^)]*)\)",
        r"](/common/command_limits\1)",
        text,
    )
    text = re.sub(
        r"\]\((?:\.\./)*skills/([^)#]+)\)",
        r"](https://github.com/PallasBot/Pallas-Bot/blob/main/docs/skills/\1)",
        text,
    )
    text = re.sub(
        r"\]\((?:\.\./)*packages/([^)#]+)\)",
        r"](https://github.com/PallasBot/Pallas-Bot/tree/main/packages/\1)",
        text,
    )
    text = re.sub(
        r"\]\(\.\./CHANGELOG\.md([^)]*)\)",
        r"](https://github.com/PallasBot/Pallas-Bot/blob/main/CHANGELOG.md\1)",
        text,
    )
    text = re.sub(
        r"\]\(\.\./\.\./architecture/\)",
        r"](/developer/architecture/overview)",
        text,
    )
    text = re.sub(
        r"\]\(\.\./\.\./\.\./(?:src|pallas)/([^)#]+)\)",
        rf"]({GITHUB_SRC}\1)",
        text,
    )
    text = re.sub(
        r"\]\(\.\./\.\./(?:src|pallas)/([^)#]+)\)",
        rf"]({GITHUB_SRC}\1)",
        text,
    )
    text = re.sub(
        r"\]\(\.\./(?:src|pallas)/([^)#]+)\)",
        rf"]({GITHUB_SRC}\1)",
        text,
    )
    text = re.sub(
        r"\]\(\.\./\.\./plugins/([a-z0-9_]+)/README\.md([^)]*)\)",
        r"](/plugins/\1\2)",
        text,
    )
    text = re.sub(
        r"\]\(\.\./plugins/([a-z0-9_]+)/README\.md([^)]*)\)",
        r"](/plugins/\1\2)",
        text,
    )
    text = re.sub(
        r"\]\(plugins/([a-z0-9_]+)/README\.md([^)]*)\)",
        r"](/plugins/\1\2)",
        text,
    )
    text = re.sub(
        r"\]\(\.\./\.\./common/([a-z0-9_]+)/README\.md([^)]*)\)",
        r"](/common/\1\2)",
        text,
    )
    text = re.sub(
        r"\]\(\.\./common/([a-z0-9_]+)/README\.md([^)]*)\)",
        r"](/common/\1\2)",
        text,
    )
    text = re.sub(
        r"\]\(common/([a-z0-9_]+)/README\.md([^)]*)\)",
        r"](/common/\1\2)",
        text,
    )
    text = re.sub(
        r"\]\(\.\./\.\./common/community_stats\.md([^)]*)\)",
        r"](/common/community_stats\1)",
        text,
    )
    text = re.sub(
        r"\]\(\.\./common/corpus/README\.md([^)]*)\)",
        r"](/common/corpus\1)",
        text,
    )
    text = re.sub(
        r"\]\(\.\./\.\./common/corpus/README\.md([^)]*)\)",
        r"](/common/corpus\1)",
        text,
    )
    text = re.sub(
        r"\]\(common/corpus/README\.md([^)]*)\)",
        r"](/common/corpus\1)",
        text,
    )
    text = re.sub(
        r"\]\(corpus/README\.md([^)]*)\)",
        r"](/common/corpus\1)",
        text,
    )
    text = re.sub(
        r"\]\(architecture/bot_process_sharding\.md([^)]*)\)",
        r"](/architecture/bot-process-sharding\1)",
        text,
    )
    text = re.sub(
        r"\]\(architecture/([a-z0-9_-]+)\.md([^)]*)\)",
        r"](/architecture/\1\2)",
        text,
    )
    text = re.sub(
        r"\]\(\./([a-z0-9_]+)/README\.md([^)]*)\)",
        r"](/plugins/\1\2)",
        text,
    )
    text = re.sub(
        r"\]\(\.\./FAQ\.md([^)]*)\)",
        r"](/deploy/faq\1)",
        text,
    )
    text = re.sub(
        r"\]\(\.\./DockerDeployment\.md([^)]*)\)",
        r"](/deploy/docker\1)",
        text,
    )
    text = re.sub(
        r"\]\(\.\./Deployment\.md([^)]*)\)",
        r"](/deploy/deployment\1)",
        text,
    )
    text = re.sub(
        r"\]\(\./TEMPLATE\.md([^)]*)\)",
        r"](https://github.com/PallasBot/Pallas-Bot/blob/main/docs/plugins/TEMPLATE.md\1)",
        text,
    )
    text = re.sub(
        r"\]\(\./VISUAL\.md([^)]*)\)",
        r"](https://github.com/PallasBot/Pallas-Bot/blob/main/docs/plugins/help/VISUAL.md\1)",
        text,
    )
    text = re.sub(
        r"\]\(\.\./\.\./FAQ\.md([^)]*)\)",
        r"](/deploy/faq\1)",
        text,
    )
    text = re.sub(
        r"\]\(\.\./(?:pallas_protocol|pb_protocol)/README\.md([^)]*)\)",
        r"](/plugins/pb_protocol\1)",
        text,
    )
    text = re.sub(r"\]\(Deployment\.md([^)]*)\)", r"](/deploy/deployment\1)", text)
    text = re.sub(r"\]\(DockerDeployment\.md([^)]*)\)", r"](/deploy/docker\1)", text)
    text = re.sub(r"\]\(Config\.md([^)]*)\)", r"](/deploy/config\1)", text)
    text = re.sub(r"\]\(FAQ\.md([^)]*)\)", r"](/deploy/faq\1)", text)
    text = re.sub(r"\]\(Migration-v3\.md([^)]*)\)", r"](/about/migration\1)", text)
    text = re.sub(
        r"\]\(\.\./README\.md([^)]*)\)",
        r"](https://github.com/PallasBot/Pallas-Bot/blob/main/README.md\1)",
        text,
    )
    text = re.sub(
        r"\]\(\.\./plugins/README\.md([^)]*)\)",
        r"](/plugins/index\1)",
        text,
    )
    text = re.sub(
        r"\]\(plugins/README\.md([^)]*)\)",
        r"](/plugins/index\1)",
        text,
    )
    text = re.sub(
        r"\]\(\.\./config/([^)#]+)\)",
        rf"](https://github.com/PallasBot/Pallas-Bot/tree/main/config/\1)",
        text,
    )
    text = re.sub(
        r"\]\(\.\./tools/([^)#]+)\)",
        rf"](https://github.com/PallasBot/Pallas-Bot/tree/main/tools/\1)",
        text,
    )
    text = re.sub(
        r"\]\(\.\./scripts/([^)#]+)\)",
        rf"](https://github.com/PallasBot/Pallas-Bot/tree/main/scripts/\1)",
        text,
    )
    text = re.sub(
        r"\]\(\.\./Dockerfile([^)]*)\)",
        r"](https://github.com/PallasBot/Pallas-Bot/blob/main/Dockerfile\1)",
        text,
    )
    text = re.sub(r"\]\(DockerDeployment\.md([^)]*)\)", r"](/deploy/docker\1)", text)
    text = re.sub(r"\]\(FAQ\.md([^)]*)\)", r"](/deploy/faq\1)", text)
    text = re.sub(r"\]\(Migration-v3\.md([^)]*)\)", r"](/about/migration\1)", text)
    text = re.sub(
        r"\]\(\.\./\.\./\.\./resource/([^)#]+)\)",
        rf"](https://github.com/PallasBot/Pallas-Bot/tree/main/resource/\1)",
        text,
    )
    text = re.sub(
        r"\]\(\.\./\.\./\.\./tools/([^)#]+)\)",
        rf"](https://github.com/PallasBot/Pallas-Bot/tree/main/tools/\1)",
        text,
    )
    text = re.sub(
        r"\]\(\.\./\.\./\.\./config/([^)#]+)\)",
        rf"](https://github.com/PallasBot/Pallas-Bot/tree/main/config/\1)",
        text,
    )
    text = re.sub(
        r"\]\(\.\./\.\./\.\./docker-compose\.yml\)",
        r"](https://github.com/PallasBot/Pallas-Bot/blob/main/docker-compose.yml)",
        text,
    )
    text = re.sub(
        r"\]\(\.\./\.\./\.\./scripts/([^)#]+)\)",
        rf"](https://github.com/PallasBot/Pallas-Bot/tree/main/scripts/\1)",
        text,
    )
    text = re.sub(r"\]\(guide/([a-z0-9.-]+)\.md([^)]*)\)", r"](/guide/\1\2)", text)
    text = re.sub(r"\]\(\.\./guide/([a-z0-9.-]+)\.md([^)]*)\)", r"](/guide/\1\2)", text)
    for guide_page in ("quickstart", "concepts", "welcome"):
        text = re.sub(
            rf"\]\({guide_page}\.md([^)]*)\)",
            rf"](/guide/{guide_page}\1)",
            text,
        )
    text = re.sub(r"\]\(\.\./user/README\.md([^)]*)\)", r"](/guide/usage-admin\1)", text)
    text = re.sub(r"\]\(user/README\.md([^)]*)\)", r"](/guide/usage-admin\1)", text)
    text = re.sub(
        r"\]\(\.\./develop/README\.md([^)]*)\)",
        r"](/develop/index\1)",
        text,
    )
    text = re.sub(
        r"\]\(\.\./architecture/bot_process_sharding\.md([^)]*)\)",
        r"](/architecture/bot-process-sharding\1)",
        text,
    )
    text = re.sub(
        r"\]\(\.\./architecture/([a-z0-9_-]+)\.md([^)]*)\)",
        r"](/architecture/\1\2)",
        text,
    )
    text = re.sub(
        r"\]\(\.\./common/community_stats\.md([^)]*)\)",
        r"](/common/community_stats\1)",
        text,
    )
    text = re.sub(
        r"\]\(\.\./\.\./skills/([^)#]+)\)",
        rf"](https://github.com/PallasBot/Pallas-Bot/blob/main/docs/skills/\1)",
        text,
    )
    text = re.sub(
        r"\]\(\.\./skills/([^)#]+)\)",
        rf"](https://github.com/PallasBot/Pallas-Bot/blob/main/docs/skills/\1)",
        text,
    )
    text = re.sub(r"\]\(4\.0-start\.md([^)]*)\)", r"](/guide/4.0-start\1)", text)
    text = re.sub(r"\]\(\.\./Config\.md([^)]*)\)", r"](/deploy/config\1)", text)
    text = re.sub(r"\]\(\.\./Deployment\.md([^)]*)\)", r"](/deploy/deployment\1)", text)
    text = re.sub(r"\]\(\.\./Migration-v3\.md([^)]*)\)", r"](/about/migration\1)", text)
    text = re.sub(r"\]\(develop/([a-z0-9_/-]+)\.md([^)]*)\)", r"](/develop/\1\2)", text)
    text = re.sub(r"\]\(\.\./develop/([a-z0-9_/-]+)\.md([^)]*)\)", r"](/develop/\1\2)", text)
    # 已带 maintainer/developer 前缀的链接
    text = re.sub(
        r"\]\((?:\.\./)*(maintainer/[a-z0-9_./-]+)\.md([^)]*)\)",
        r"](/\1\2)",
        text,
    )
    text = re.sub(
        r"\]\((?:\.\./)*(developer/[a-z0-9_./-]+)\.md([^)]*)\)",
        r"](/\1\2)",
        text,
    )
    # 去掉站内链接里的 .md 后缀
    text = re.sub(
        r"(\]\(/(?:deploy|plugins|architecture|common|about|guide|maintainer|developer|develop)"
        r"/[a-zA-Z0-9_./-]+)\.md\)",
        r"\1)",
        text,
    )
    return text


def rewrite_tree_relative_links(text: str, *, rel_src: str) -> str:
    """把 maintainer/developer 树内相对链接改成 VitePress 绝对路径。"""
    if rel_src.startswith("maintainer/"):
        text = re.sub(
            r"\]\((?:\.\./)?(install|deploy|operate|reference)/([a-z0-9_./-]+)\.md([^)]*)\)",
            r"](/maintainer/\1/\2\3)",
            text,
        )
        text = re.sub(r"\]\((?:\.\./)?quickstart\.md([^)]*)\)", r"](/maintainer/quickstart\1)", text)
    elif rel_src.startswith("developer/"):
        text = re.sub(
            r"\]\((?:\.\./)?(architecture|plugin-development|reference|author)/"
            r"([a-z0-9_./-]+)\.md([^)]*)\)",
            r"](/developer/\1/\2\3)",
            text,
        )
        text = re.sub(r"\]\((?:\.\./)?index\.md([^)]*)\)", r"](/developer/index\1)", text)
    return text


def sync(dest_root: Path) -> int:
    src_root = dest_root / "src"
    count = 0
    avatar_src = DOCS / "plugins" / "assets" / "brand-avatar.png"
    avatar_dst = src_root / "public" / "assets" / "brand-avatar.png"
    if avatar_src.is_file():
        avatar_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(avatar_src, avatar_dst)
        print("sync plugins/assets/brand-avatar.png -> src/public/assets/brand-avatar.png")
    for rel_src, rel_dst in FILE_MAP.items():
        source = DOCS / rel_src
        if not source.is_file():
            print(f"skip missing: {rel_src}")
            continue
        body = source.read_text(encoding="utf-8")
        body = rewrite_tree_relative_links(body, rel_src=rel_src)
        out = src_root / rel_dst
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(transform_for_vitepress(body), encoding="utf-8")
        count += 1
        print(f"sync {rel_src} -> src/{rel_dst}")
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync docs/ to Pallas-Bot-Docs VitePress src/")
    parser.add_argument(
        "--dest",
        type=Path,
        default=REPO_ROOT.parent / "Pallas-Bot-Docs",
        help="Pallas-Bot-Docs 仓库根目录",
    )
    args = parser.parse_args()
    if not args.dest.is_dir():
        raise SystemExit(f"dest not found: {args.dest}")
    n = sync(args.dest)
    print(f"done: {n} files")


if __name__ == "__main__":
    main()
