import asyncio

import pytest

from src.plugins.repeater.learn_queue import learn_concurrency, learn_queue_max_size


def test_learn_defaults_reasonable():
    assert learn_concurrency() >= 1
    assert learn_queue_max_size() >= 64


@pytest.mark.asyncio
async def test_learn_sem_limits_parallel(monkeypatch):
    monkeypatch.setenv("PALLAS_REPEATER_LEARN_CONCURRENCY", "2")
    from src.plugins.repeater import learn_queue as lq
    from src.plugins.repeater.learn_runtime_config import clear_repeater_learn_runtime_config_cache

    clear_repeater_learn_runtime_config_cache()
    lq.clear_repeater_learn_runtime_state()
    sem = lq.learn_sem()
    await sem.acquire()
    await sem.acquire()
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(sem.acquire(), timeout=0.05)
    sem.release()
    sem.release()
