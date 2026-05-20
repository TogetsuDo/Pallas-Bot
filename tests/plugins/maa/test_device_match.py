from src.plugins.maa.store import DeviceRecord, match_device_ref

DEV_A = "42cfa6e9dfa147d8a7c1d9a6d658b06d"
DEV_B = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"


def sample_devices() -> dict[str, DeviceRecord]:
    return {
        DEV_A: DeviceRecord(device=DEV_A, verified=True, alias="家里"),
        DEV_B: DeviceRecord(device=DEV_B, verified=True, alias=""),
    }


def test_match_full_id() -> None:
    did, err = match_device_ref(DEV_A, sample_devices())
    assert err is None
    assert did == DEV_A


def test_match_alias() -> None:
    did, err = match_device_ref("家里", sample_devices())
    assert err is None
    assert did == DEV_A


def test_match_prefix() -> None:
    did, err = match_device_ref("42cfa6e9", sample_devices())
    assert err is None
    assert did == DEV_A


def test_match_ambiguous_prefix() -> None:
    devices = {
        "42cfa6e9dfa147d8a7c1d9a6d658b06d": DeviceRecord(device="42cfa6e9dfa147d8a7c1d9a6d658b06d", verified=True),
        "42cfa6e9aaaaaaaaaaaaaaaaaaaaaaaaaa": DeviceRecord(device="42cfa6e9aaaaaaaaaaaaaaaaaaaaaaaaaa", verified=True),
    }
    _, err = match_device_ref("42cfa6e9", devices)
    assert err is not None
