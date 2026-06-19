"""插件商店资源快照：README / icon / cover / avatar 定时拉取到本地 public 目录。"""

from __future__ import annotations

import asyncio
import json
import mimetypes
import re
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
from nonebot import logger

from pallas.core.foundation.paths import plugin_data_dir

_SNAPSHOT_FILENAME = "plugin_store_assets_snapshot.json"
_PUBLIC_PREFIX = "/pallas/store-assets"
_MAX_CONCURRENCY = 6
_HTTP_TIMEOUT = httpx.Timeout(30.0, connect=10.0)
_GITHUB_RAW_RE = re.compile(r"github\.com[/:]([^/]+)/([^/.]+?)(?:\.git)?(?:/|$)", re.IGNORECASE)


def snapshot_path() -> Path:
    return plugin_data_dir("pb_webui", create=True) / _SNAPSHOT_FILENAME


def load_snapshot() -> dict[str, Any]:
    path = snapshot_path()
    try:
        raw = path.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError):
        return {}
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        logger.warning("Pallas-Bot 控制台: 插件商店资源快照损坏，忽略 path={}", path)
        return {}
    return data if isinstance(data, dict) else {}


def save_snapshot(data: dict[str, Any]) -> None:
    path = snapshot_path()
    tmp = path.with_suffix(".json.tmp")
    try:
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)
    except OSError as exc:
        logger.warning("Pallas-Bot 控制台: 插件商店资源快照写盘失败 err={}", exc)


def _public_root() -> Path:
    return plugin_data_dir("pb_webui", create=True) / "public" / "store-assets"


def _asset_target_id(kind: str, row: dict[str, Any]) -> str:
    return str(row["package"] if kind == "official" else row["plugin_id"]).strip()


def _safe_name(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip("-") or "asset"


def _parse_repo(repository_url: str | None) -> tuple[str, str] | None:
    raw = (repository_url or "").strip()
    match = _GITHUB_RAW_RE.search(raw)
    if not match:
        return None
    owner = match.group(1).strip()
    repo = match.group(2).strip()
    if not owner or not repo:
        return None
    return owner, repo


def _guess_suffix(url: str, content_type: str = "") -> str:
    path = urlparse(url).path
    suffix = Path(path).suffix.lower()
    if suffix:
        return suffix
    guessed = mimetypes.guess_extension((content_type or "").split(";", 1)[0].strip()) or ""
    if guessed == ".jpe":
        return ".jpg"
    return guessed or ".bin"


def _readme_public_rel(kind: str, target_id: str) -> str:
    return f"public/store-assets/readme/{kind}-{_safe_name(target_id)}.md"


def _asset_public_rel(kind: str, asset_type: str, target_id: str, suffix: str) -> str:
    clean_suffix = suffix if suffix.startswith(".") else f".{suffix}"
    return f"public/store-assets/{asset_type}/{kind}-{_safe_name(target_id)}{clean_suffix}"


def _public_url_from_rel(relative_path: str) -> str:
    rel = relative_path.replace("\\", "/").strip("/")
    if rel.startswith("public/store-assets/"):
        return f"{_PUBLIC_PREFIX}/{rel[len('public/store-assets/'):]}"
    return f"{_PUBLIC_PREFIX}/{Path(rel).name}"


def _resolve_path(relative_path: str) -> Path:
    rel = Path(relative_path)
    if rel.parts and rel.parts[0] == "public":
        return plugin_data_dir("pb_webui", create=True) / rel
    return _public_root() / rel


def _snapshot_entry(snapshot: dict[str, Any], kind: str, target_id: str) -> dict[str, Any]:
    bucket = snapshot.setdefault(kind, {})
    entry = bucket.setdefault(target_id, {})
    if not isinstance(entry, dict):
        entry = {}
        bucket[target_id] = entry
    return entry


def apply_asset_snapshot_to_rows(kind: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    snapshot = load_snapshot()
    bucket = snapshot.get(kind) or {}
    out: list[dict[str, Any]] = []
    for row in rows:
        copied = dict(row)
        target_id = _asset_target_id(kind, copied)
        entry = bucket.get(target_id)
        if isinstance(entry, dict):
            assets = entry.get("assets") or {}
            if isinstance(assets, dict):
                for asset_type in ("icon", "cover", "avatar"):
                    asset = assets.get(asset_type)
                    if isinstance(asset, dict):
                        public_url = str(asset.get("public_url") or "").strip()
                        if public_url:
                            copied[asset_type] = public_url
        out.append(copied)
    return out


def get_cached_readme_markdown(kind: str, target_id: str) -> str | None:
    snapshot = load_snapshot()
    entry = ((snapshot.get(kind) or {}).get(target_id) or {})
    if not isinstance(entry, dict):
        return None
    readme = entry.get("readme") or {}
    if not isinstance(readme, dict):
        return None
    relative_path = str(readme.get("relative_path") or "").strip()
    if not relative_path:
        return None
    path = _resolve_path(relative_path)
    try:
        text = path.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError):
        return None
    return text or None


async def collect_store_asset_targets() -> dict[str, list[dict[str, Any]]]:
    from pallas.console.webui.community_plugin_index import load_community_plugin_index_safe
    from pallas.core.platform.bot_runtime.plugin_matrix import (
        EXTRA_PLUGIN_PACKAGES,
        official_extension_repo_url,
        official_extension_visuals,
    )

    official: list[dict[str, Any]] = []
    for package in sorted(set(EXTRA_PLUGIN_PACKAGES.values())):
        repo_url = official_extension_repo_url(package)
        visuals = official_extension_visuals(package)
        official.append({
            "id": package,
            "repository_url": repo_url,
            "assets": {
                "icon": visuals.get("icon"),
                "cover": visuals.get("cover"),
                "avatar": visuals.get("avatar"),
            },
            "readme_url": _github_readme_url(repo_url),
        })

    index = await load_community_plugin_index_safe()
    community: list[dict[str, Any]] = []
    for row in index.get("plugins") or []:
        if not isinstance(row, dict) or not row.get("plugin_id"):
            continue
        community.append({
            "id": str(row["plugin_id"]).strip(),
            "repository_url": row.get("repository_url"),
            "assets": {
                "icon": row.get("icon"),
                "cover": row.get("cover"),
                "avatar": row.get("avatar"),
            },
            "readme_url": _github_readme_url(row.get("repository_url")),
        })
    return {"official": official, "community": community}


def _github_readme_url(repository_url: str | None) -> str | None:
    parsed = _parse_repo(repository_url)
    if not parsed:
        return None
    owner, repo = parsed
    return f"https://raw.githubusercontent.com/{owner}/{repo}/refs/heads/main/README.md"


async def _download_binary(url: str) -> tuple[bytes, str]:
    async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.content, str(resp.headers.get("content-type") or "")


async def _download_text(url: str) -> str:
    async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.text


def _write_bytes(relative_path: str, content: bytes) -> None:
    path = _resolve_path(relative_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(content)
    tmp.replace(path)


def _write_text(relative_path: str, content: str) -> None:
    path = _resolve_path(relative_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def _normalize_existing_asset(asset: dict[str, Any] | None, *, fallback_url: str | None = None) -> dict[str, Any] | None:
    if not isinstance(asset, dict):
        return None
    source_url = str(asset.get("source_url") or fallback_url or "").strip()
    public_url = str(asset.get("public_url") or "").strip()
    relative_path = str(asset.get("relative_path") or "").strip()
    if not public_url and not relative_path and not source_url:
        return None
    return {
        "source_url": source_url or None,
        "public_url": public_url or None,
        "relative_path": relative_path or None,
        "updated_at": asset.get("updated_at"),
        "error": asset.get("error"),
    }


async def _refresh_one(kind: str, target: dict[str, Any], previous: dict[str, Any]) -> dict[str, Any]:
    target_id = str(target["id"]).strip()
    entry: dict[str, Any] = {
        "repository_url": str(target.get("repository_url") or "").strip() or None,
        "assets": {},
        "readme": None,
    }
    prev_assets = previous.get("assets") if isinstance(previous.get("assets"), dict) else {}
    for asset_type, source_url in (target.get("assets") or {}).items():
        if asset_type not in ("icon", "cover", "avatar"):
            continue
        raw_url = str(source_url or "").trim() if hasattr(str(source_url or ""), "trim") else str(source_url or "").strip()
        prev_asset = _normalize_existing_asset(prev_assets.get(asset_type), fallback_url=raw_url)
        if not raw_url:
            if prev_asset:
                entry["assets"][asset_type] = prev_asset
            continue
        if raw_url.startswith("/pallas/"):
            entry["assets"][asset_type] = {
                "source_url": raw_url,
                "public_url": raw_url,
                "relative_path": None,
                "updated_at": time.time(),
                "error": None,
            }
            continue
        try:
            content, content_type = await _download_binary(raw_url)
            rel = _asset_public_rel(kind, asset_type, target_id, _guess_suffix(raw_url, content_type))
            _write_bytes(rel, content)
            entry["assets"][asset_type] = {
                "source_url": raw_url,
                "public_url": _public_url_from_rel(rel),
                "relative_path": rel,
                "updated_at": time.time(),
                "error": None,
            }
        except Exception as exc:  # noqa: BLE001
            if prev_asset:
                prev_asset["error"] = str(exc)
                entry["assets"][asset_type] = prev_asset
            else:
                entry["assets"][asset_type] = {
                    "source_url": raw_url,
                    "public_url": None,
                    "relative_path": None,
                    "updated_at": None,
                    "error": str(exc),
                }

    readme_url = str(target.get("readme_url") or "").strip()
    prev_readme = previous.get("readme") if isinstance(previous.get("readme"), dict) else None
    if readme_url:
        try:
            markdown = await _download_text(readme_url)
            rel = _readme_public_rel(kind, target_id)
            _write_text(rel, markdown)
            entry["readme"] = {
                "source_url": readme_url,
                "public_url": _public_url_from_rel(rel),
                "relative_path": rel,
                "updated_at": time.time(),
                "error": None,
            }
        except Exception as exc:  # noqa: BLE001
            if prev_readme:
                entry["readme"] = {
                    **prev_readme,
                    "error": str(exc),
                }
            else:
                entry["readme"] = {
                    "source_url": readme_url,
                    "public_url": None,
                    "relative_path": None,
                    "updated_at": None,
                    "error": str(exc),
                }
    elif prev_readme:
        entry["readme"] = prev_readme
    return target_id, entry


async def refresh_store_asset_snapshot() -> dict[str, Any]:
    previous = load_snapshot()
    targets = await collect_store_asset_targets()
    snapshot: dict[str, Any] = {"checked_at": time.time(), "official": {}, "community": {}}
    sem = asyncio.Semaphore(_MAX_CONCURRENCY)

    async def _run(kind: str, target: dict[str, Any]):
        async with sem:
            prev = (((previous.get(kind) or {}) if isinstance(previous.get(kind), dict) else {}).get(target["id"]) or {})
            if not isinstance(prev, dict):
                prev = {}
            return await _refresh_one(kind, target, prev)

    for kind in ("official", "community"):
        items = [t for t in targets.get(kind, []) if isinstance(t, dict) and t.get("id")]
        results = await asyncio.gather(*[_run(kind, item) for item in items])
        snapshot[kind] = {target_id: entry for target_id, entry in results}

    save_snapshot(snapshot)
    return snapshot


def run_async(awaitable):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(awaitable)
    raise RuntimeError("run_async cannot be used inside a running event loop")
