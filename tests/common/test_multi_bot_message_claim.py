from pathlib import Path

import pytest

from src.common import multi_bot_message_claim as claim_mod


@pytest.fixture
def claim_plugin_data(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "pallas_image"
    monkeypatch.setattr(claim_mod, "plugin_data_dir", lambda name, create=True: root if name == "pallas_image" else tmp_path / name)
    return root


def test_only_one_bot_claims_same_message(claim_plugin_data: Path) -> None:
    gid, mid = 12345, 999
    assert claim_mod.try_claim_message_sync("pallas_image", gid, mid, 111) is True
    assert claim_mod.try_claim_message_sync("pallas_image", gid, mid, 222) is False
    assert claim_mod.try_claim_message_sync("pallas_image", gid, mid, 111) is True


def test_different_message_id_both_claim(claim_plugin_data: Path) -> None:
    gid = 12345
    assert claim_mod.try_claim_message_sync("pallas_image", gid, 1, 111) is True
    assert claim_mod.try_claim_message_sync("pallas_image", gid, 2, 222) is True
