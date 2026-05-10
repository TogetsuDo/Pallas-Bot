from __future__ import annotations

DREAM_CAPTURE_BLOCK_SUBSTRINGS: tuple[str, ...] = ("不可以",)


def dream_capture_blocked_by_substrings(plain_text: str, raw_message: str) -> bool:
    p = plain_text or ""
    r = raw_message or ""
    return any(s in p or s in r for s in DREAM_CAPTURE_BLOCK_SUBSTRINGS)
