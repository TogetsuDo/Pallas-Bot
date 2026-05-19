import pytest

from src.plugins.maa.store import MaaStore, NotifyTarget
from src.plugins.maa.tasks import MaaTaskSpec


@pytest.mark.asyncio
async def test_get_task_flow(beanie_fixture) -> None:
    store = MaaStore()
    user = "12345"
    device = "42cfa6e9dfa147d8a7c1d9a6d658b06d"

    await store.touch_seen(user, device, ttl=3600)
    err = await store.bind_device(12345, user, device, ttl=3600)
    assert err is None

    notify = NotifyTarget(bot_id=10001, user_id=12345)
    ids, err2 = await store.enqueue(
        12345,
        [MaaTaskSpec("LinkStart")],
        notify,
        attach_screenshot=False,
    )
    assert err2 is None
    assert len(ids) == 1

    tasks = await store.pending_tasks_for(user, device)
    assert len(tasks) == 1
    assert tasks[0]["type"] == "LinkStart"

    unverified = await store.pending_tasks_for(user, "00000000-0000-0000-0000-000000000099")
    assert unverified == []


@pytest.mark.asyncio
async def test_bind_requires_seen() -> None:
    store = MaaStore()
    err = await store.bind_device(99, "99", "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", ttl=3600)
    assert err is not None
