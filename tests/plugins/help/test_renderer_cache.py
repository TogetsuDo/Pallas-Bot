from __future__ import annotations

from src.plugins.help import renderer


def test_save_image_to_cache_prunes_old_pngs(tmp_path, monkeypatch):
    monkeypatch.setattr(renderer, "plugin_data_dir", lambda _name: tmp_path)
    monkeypatch.setattr(renderer, "_help_image_cache_suffix", lambda: "fixed-a")
    monkeypatch.setattr(renderer, "_HELP_CACHE_FILES_PER_DIR_MAX", 2, raising=False)

    cache_dir = tmp_path / "42"
    cache_dir.mkdir(parents=True, exist_ok=True)
    old_a = cache_dir / "old-a.png"
    old_b = cache_dir / "old-b.png"
    old_a.write_bytes(b"old-a")
    old_b.write_bytes(b"old-b")

    renderer.save_image_to_cache(b"new", "markdown", "style", group_id=42)

    pngs = sorted(p.name for p in cache_dir.glob("*.png"))
    assert len(pngs) == 2
    assert "old-a.png" not in pngs
    assert "old-b.png" in pngs
