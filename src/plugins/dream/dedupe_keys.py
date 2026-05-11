from __future__ import annotations

import hashlib


def dream_text_dedupe_key(text: str) -> str:
    return " ".join((text or "").strip().lower().split())


def dream_image_dedupe_key(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
