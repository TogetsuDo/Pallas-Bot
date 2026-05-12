import random
from pathlib import Path

from src.common.paths import resource_dir

voice_set = {
    "任命助理",
    "交谈1",
    "交谈2",
    "交谈3",
    "晋升后交谈1",
    "晋升后交谈2",
    "信赖提升后交谈1",
    "信赖提升后交谈2",
    "信赖提升后交谈3",
    "闲置",
    "干员报到",
    "精英化晋升1",
    "精英化晋升2",
    "编入队伍",
    "任命队长",
    "戳一下",
    "信赖触摸",
    "问候",
}

voices_source = resource_dir("voices")
_extra_dir = voices_source / "extra"


def _load_extra_voices() -> set[str]:
    """从 extra 目录加载侧载语音集合。"""
    extra_set = set()
    if _extra_dir.exists():
        for f in _extra_dir.iterdir():
            if f.suffix == ".wav" and f.stem in voice_set:
                extra_set.add(f.stem)
    return extra_set


def get_voice_filepath(operator, voice_name) -> Path | None:
    if voice_name not in voice_set:
        return None
    f = voices_source / operator / f"{voice_name}.wav"
    if f.exists():
        return f
    # 查找 extra 目录中的侧载语音
    extra_f = _extra_dir / f"{voice_name}.wav"
    return extra_f if extra_f.exists() else None


def get_random_voice(operator, ranges) -> Path | None:
    extra_set = _load_extra_voices()
    # 合并 ranges 和 extra 中的可用语音
    available = [r for r in ranges if r in voice_set]
    if extra_set:
        available.extend([r for r in ranges if r in extra_set])
    if not available:
        return None
    key = random.choice(available)
    return get_voice_filepath(operator, key)
