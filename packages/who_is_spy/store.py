from __future__ import annotations

import json
import shutil
from pathlib import Path

from nonebot import logger

from pallas.core.foundation.paths import plugin_data_dir, resource_dir

DEFAULT_WORD_FILE = resource_dir("who_is_spy") / "undercover_words.json"
DATA_DIR = plugin_data_dir("who_is_spy")
WORD_FILE = DATA_DIR / "undercover_words.json"
RECENT_WORDS_FILE = DATA_DIR / "recent_word_pairs.json"

_PLUGIN = "who_is_spy"
_RECENT_KEY = "recent_word_pairs"

WORD_BANK: list[tuple[str, str]] = []


def ensure_word_file() -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not WORD_FILE.exists() and DEFAULT_WORD_FILE.is_file():
        shutil.copyfile(DEFAULT_WORD_FILE, WORD_FILE)
        logger.info("who_is_spy: seeded word bank from {} to {}", DEFAULT_WORD_FILE, WORD_FILE)
    return WORD_FILE


def read_word_pairs(path: Path | str) -> list[tuple[str, str]]:
    target = Path(path)
    if not target.is_file():
        return []
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("who_is_spy: load word bank failed path={} err={}", target, exc)
        return []

    pairs: list[tuple[str, str]] = []
    for item in data:
        if isinstance(item, (list, tuple)) and len(item) == 2:
            civilian, undercover = str(item[0]).strip(), str(item[1]).strip()
            if civilian and undercover:
                pairs.append((civilian, undercover))
    return pairs


def merge_word_pairs(*sources: list[tuple[str, str]]) -> list[tuple[str, str]]:
    seen: set[tuple[str, str]] = set()
    merged: list[tuple[str, str]] = []
    for source in sources:
        for pair in source:
            if pair in seen:
                continue
            seen.add(pair)
            merged.append(pair)
    return merged


def sync_word_file() -> int:
    """合并 data 词库与内置 resource。"""
    ensure_word_file()
    data_pairs = read_word_pairs(WORD_FILE)
    resource_pairs = read_word_pairs(DEFAULT_WORD_FILE) if DEFAULT_WORD_FILE.is_file() else []
    merged = merge_word_pairs(data_pairs, resource_pairs)
    if len(merged) > len(data_pairs):
        payload = [[a, b] for a, b in merged]
        WORD_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        logger.info(
            "who_is_spy: merged word bank {} -> {} pairs (resource had {} new)",
            len(data_pairs),
            len(merged),
            len(merged) - len(data_pairs),
        )
    return len(merged)


def load_words_from_json(path: Path | str | None = None) -> int:
    target = Path(path) if path else ensure_word_file()
    pairs = read_word_pairs(target)
    WORD_BANK[:] = pairs
    return len(pairs)


def word_pair_key(a: str, b: str) -> tuple[str, str]:
    return tuple(sorted((a, b)))


def _normalize_recent_blob(raw: object) -> dict[str, list[list[str]]]:
    if not isinstance(raw, dict):
        return {}
    out: dict[str, list[list[str]]] = {}
    for group_id, entries in raw.items():
        if not isinstance(entries, list):
            continue
        pairs = [[str(item[0]), str(item[1])] for item in entries if isinstance(item, (list, tuple)) and len(item) == 2]
        out[str(group_id)] = pairs
    return out


def _read_recent_blob() -> dict[str, list[list[str]]]:
    from pallas.core.storage.deploy_store import read_deploy_plugin_blob

    raw = read_deploy_plugin_blob(_PLUGIN).get(_RECENT_KEY)
    if raw is None:
        return _migrate_legacy_recent_blob()
    return _normalize_recent_blob(raw)


def _read_legacy_recent_blob() -> dict[str, list[list[str]]]:
    if not RECENT_WORDS_FILE.is_file():
        return {}
    try:
        raw = json.loads(RECENT_WORDS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return _normalize_recent_blob(raw)


def _migrate_legacy_recent_blob() -> dict[str, list[list[str]]]:
    blob = _read_legacy_recent_blob()
    if not blob and not RECENT_WORDS_FILE.is_file():
        return {}
    from pallas.core.storage.deploy_store import read_deploy_plugin_blob, write_deploy_plugin_blob

    storage = read_deploy_plugin_blob(_PLUGIN)
    storage[_RECENT_KEY] = blob
    write_deploy_plugin_blob(_PLUGIN, storage)
    if RECENT_WORDS_FILE.is_file():
        backup = RECENT_WORDS_FILE.with_suffix(RECENT_WORDS_FILE.suffix + ".migrated")
        if not backup.exists():
            RECENT_WORDS_FILE.replace(backup)
    return blob


def _save_recent_blob(blob: dict[str, list[list[str]]]) -> None:
    from pallas.core.storage.deploy_store import read_deploy_plugin_blob, write_deploy_plugin_blob

    storage = read_deploy_plugin_blob(_PLUGIN)
    storage[_RECENT_KEY] = blob
    write_deploy_plugin_blob(_PLUGIN, storage)


def load_recent_word_keys(group_id: int, *, limit: int) -> set[tuple[str, str]]:
    if limit <= 0:
        return set()
    entries = _read_recent_blob().get(str(group_id), [])
    keys: set[tuple[str, str]] = set()
    for item in entries[-limit:]:
        if len(item) == 2:
            keys.add(word_pair_key(item[0], item[1]))
    return keys


def record_recent_word_pair(group_id: int, a: str, b: str, *, keep: int) -> None:
    if keep <= 0:
        return
    blob = _read_recent_blob()
    key = str(group_id)
    entries = blob.get(key, [])
    pair = [a, b]
    if entries and entries[-1] == pair:
        return
    entries.append(pair)
    blob[key] = entries[-keep:]
    _save_recent_blob(blob)


def init_store() -> None:
    sync_word_file()
    loaded = load_words_from_json(WORD_FILE)
    if loaded:
        logger.info("who_is_spy: loaded {} word pairs from {}", loaded, WORD_FILE)
