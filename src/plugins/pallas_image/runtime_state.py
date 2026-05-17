import asyncio

from .config import image_gen_config

image_gen_semaphore = asyncio.Semaphore(image_gen_config.max_concurrency)
_semaphore_limit = image_gen_config.max_concurrency


def sync_image_gen_semaphore(max_concurrency: int) -> None:
    global image_gen_semaphore, _semaphore_limit
    limit = max(1, min(int(max_concurrency), 32))
    if limit == _semaphore_limit:
        return
    image_gen_semaphore = asyncio.Semaphore(limit)
    _semaphore_limit = limit
