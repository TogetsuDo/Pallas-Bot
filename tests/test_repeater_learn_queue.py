import asyncio

import pytest

from src.plugins.repeater.learn_queue import learn_concurrency, learn_queue_max_size


def test_learn_defaults_reasonable():
    from src.plugins.repeater.config import Config
    from src.plugins.repeater.learn_runtime_config import RepeaterLearnRuntimeConfig

    assert Config.model_fields["learn_concurrency"].default == 8
    assert RepeaterLearnRuntimeConfig().learn_concurrency == 8
    assert learn_queue_max_size() >= 64


@pytest.mark.asyncio
async def test_learn_sem_limits_parallel(monkeypatch):
    from src.plugins.repeater import learn_queue as lq

    monkeypatch.setattr(lq, "learn_concurrency", lambda: 2)
    lq.clear_repeater_learn_runtime_state()
    sem = lq.learn_sem()
    await sem.acquire()
    await sem.acquire()
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(sem.acquire(), timeout=0.05)
    sem.release()
    sem.release()
