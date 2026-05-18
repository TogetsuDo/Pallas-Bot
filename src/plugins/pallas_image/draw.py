import asyncio
import time

import httpx
from nonebot import logger, on_command
from nonebot.adapters import Bot
from nonebot.adapters.onebot.v11 import (
    GroupMessageEvent,
    Message,
)
from nonebot.exception import FinishedException
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER

from src.common.cmd_perm import group_message_permission_for_command
from src.common.config import GroupConfig
from src.common.utils.http_msg import (
    PALLAS_VAGUE_REPLY,
    upstream_error_visible_to_user,
    user_failure_reply,
)

from .config import ImageApiBackend, image_gen_config
from .draw_usage_store import bump_pallas_draw_usage, pallas_draw_usage_today
from .image_api import (
    CffiRequestsError,
    bytes_from_image_reference,
    generations_payload,
    image_api_body_issue_label,
    image_edits_endpoint,
    image_gen_auth_headers_json,
    image_gen_endpoint,
    message_at_user,
    post_edits_with_transport,
    post_generations_with_transport,
    reply_from_image_api_json,
)
from .image_request_options import image_gen_request_attempts
from .runtime_state import image_gen_semaphore

PALLAS_DRAW_COOLDOWN_KEY = "pallas_draw_command"


def extract_image_urls_from_message(msg: Message) -> list[str]:
    urls: list[str] = []
    for seg in msg:
        if seg.type == "image":
            u = seg.data.get("url") or seg.data.get("file") or ""
            if isinstance(u, str) and u.strip():
                urls.append(u.strip())
    return urls


def dedupe_urls(urls: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def image_backends_with_endpoint(
    backends: list[ImageApiBackend],
    endpoint_fn,
) -> list[ImageApiBackend]:
    return [b for b in backends if endpoint_fn(b)]


def log_image_backend_unusable(
    bot_id: int,
    op: str,
    backend_label: str,
    group_id: int,
    body_text: str,
    *,
    has_more: bool,
) -> None:
    issue = image_api_body_issue_label(body_text) or "image_send_failed"
    snippet = body_text[:200]
    if has_more:
        logger.info(
            f"bot [{bot_id}] pallas_image {op} backend={backend_label} unusable "
            f"in group [{group_id}] issue={issue} body={snippet!r}, trying next",
        )
    else:
        logger.warning(
            f"bot [{bot_id}] pallas_image {op} backend={backend_label} unusable "
            f"in group [{group_id}] issue={issue} body={snippet!r}",
        )


_MAX_PALLAS_DRAW_USER_LOCKS = 8192
pallas_draw_user_locks: dict[tuple[int, int], asyncio.Lock] = {}


def get_pallas_draw_user_lock(group_id: int, user_id: int) -> asyncio.Lock:
    key = (group_id, user_id)
    if len(pallas_draw_user_locks) > _MAX_PALLAS_DRAW_USER_LOCKS:
        for k in list(pallas_draw_user_locks.keys()):
            if len(pallas_draw_user_locks) <= _MAX_PALLAS_DRAW_USER_LOCKS:
                break
            lock = pallas_draw_user_locks.get(k)
            if lock is not None and not lock.locked():
                del pallas_draw_user_locks[k]
    if key not in pallas_draw_user_locks:
        pallas_draw_user_locks[key] = asyncio.Lock()
    return pallas_draw_user_locks[key]


def draw_group_allowed(group_id: int) -> bool:
    wl = image_gen_config.draw_group_whitelist
    return not wl or group_id in wl


def draw_should_count_usage(group_id: int, user_id: int) -> bool:
    cfg = image_gen_config
    if cfg.draw_per_user_limit <= 0:
        return False
    if group_id in cfg.draw_unlimited_group_ids_set:
        return False
    if user_id in cfg.draw_unlimited_user_ids_set:
        return False
    return True


async def acquire_pallas_draw_group_cooldown(group_id: int) -> bool:
    seconds = image_gen_config.draw_command_cooldown
    if seconds <= 0:
        return True
    gconf = GroupConfig(group_id, cooldown=seconds)
    if not await gconf.is_cooldown(PALLAS_DRAW_COOLDOWN_KEY):
        return False
    await gconf.refresh_cooldown(PALLAS_DRAW_COOLDOWN_KEY)
    return True


pallas_draw = on_command(
    "牛牛画画",
    priority=image_gen_config.min_priority,
    block=True,
    permission=group_message_permission_for_command("pallas_image.draw"),
)


@pallas_draw.handle()
async def pallas_draw_handle(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):  # noqa: B008
    group_id = event.group_id
    user_id = event.user_id

    if not draw_group_allowed(group_id):
        return

    if not await acquire_pallas_draw_group_cooldown(group_id):
        return

    backends = image_gen_config.api_backends()
    if not backends or not any((b.model or "").strip() for b in backends):
        await pallas_draw.finish(
            message_at_user(
                user_id,
                "牛牛画画未配置：请设置 pallas_image 的 base_url、api_key、model，或配置 api_backends",
            )
        )

    usage_key = (group_id, user_id)
    count_usage = draw_should_count_usage(group_id, user_id)
    if await SUPERUSER(bot, event):
        count_usage = False
    limit_n = image_gen_config.draw_per_user_limit
    if count_usage and pallas_draw_usage_today(usage_key) >= limit_n:
        await pallas_draw.finish(message_at_user(user_id, f"你在本群今日的画画次数已达上限（{limit_n}）。"))

    text = args.extract_plain_text().strip()
    ref_urls = dedupe_urls(
        extract_image_urls_from_message(args)
        + (extract_image_urls_from_message(event.reply.message) if event.reply else [])
    )
    if not text and not ref_urls:
        await pallas_draw.finish(
            message_at_user(
                user_id,
                "请说明想画什么，例如：牛牛画画 一只穿斗篷的羊。\n"
                "也可附带一张或多张参考图"
                "或回复一条带图的消息后再发「牛牛画画」 做图生图。",
            )
        )

    await pallas_draw.send("欢呼吧！")
    asyncio.create_task(
        run_pallas_draw_queued(
            pallas_draw,
            int(event.self_id),
            usage_key,
            count_usage,
            user_id,
            text,
            ref_urls,
        ),
        name=f"pallas_draw:{group_id}:{user_id}",
    )


async def run_pallas_draw_queued(
    matcher,
    bot_id: int,
    usage_key: tuple[int, int],
    count_usage: bool,
    user_id: int,
    text: str,
    ref_urls: list[str],
) -> None:
    group_id, _ = usage_key
    try:
        async with get_pallas_draw_user_lock(group_id, user_id):
            limit_n = image_gen_config.draw_per_user_limit
            if count_usage and pallas_draw_usage_today(usage_key) >= limit_n:
                await matcher.send(message_at_user(user_id, f"你在本群今日的画画次数已达上限（{limit_n}）。"))
                return
            await pallas_draw_execute(matcher, bot_id, usage_key, count_usage, user_id, text, ref_urls)
    except FinishedException:
        raise
    except Exception as e:
        logger.exception(f"bot [{bot_id}] pallas_image queued draw failed in group [{group_id}]: {e}")


async def pallas_draw_execute(
    matcher,
    bot_id: int,
    usage_key: tuple[int, int],
    count_usage: bool,
    user_id: int,
    text: str,
    ref_urls: list[str],
) -> None:
    cfg = image_gen_config
    group_id = usage_key[0]
    backends = cfg.api_backends()
    default_prompt = (cfg.default_edit_prompt or "生成图像").strip()
    if cfg.merge_reference_urls_into_prompt:
        gen_prompt = " ".join([p for p in [text, *ref_urls] if p])
    elif text.strip():
        gen_prompt = text.strip()
    elif ref_urls:
        gen_prompt = default_prompt
    else:
        gen_prompt = default_prompt

    httpx_timeout = httpx.Timeout(cfg.request_timeout)
    async with image_gen_semaphore:
        try:
            async with httpx.AsyncClient(timeout=httpx_timeout, trust_env=True) as http_client:
                if ref_urls and cfg.use_edits_for_reference_images:
                    blobs: list[bytes] = []
                    for u in ref_urls:
                        b = await bytes_from_image_reference(http_client, u)
                        if b:
                            blobs.append(b)
                    if blobs:
                        edit_prompt = text.strip() or default_prompt
                        if len(ref_urls) > len(blobs):
                            logger.warning(
                                f"bot [{bot_id}] pallas_image ref download partial in group [{group_id}]: "
                                f"requested {len(ref_urls)} refs, got {len(blobs)} blobs",
                            )
                        last_body = ""
                        edit_param_attempts = image_gen_request_attempts(with_ref_urls=False)
                        edit_backends = image_backends_with_endpoint(backends, image_edits_endpoint)
                        for idx, backend in enumerate(edit_backends):
                            has_more_backend = idx < len(edit_backends) - 1
                            edits_ep = image_edits_endpoint(backend)
                            skip_backend = False
                            for opt_idx, req_opts in enumerate(edit_param_attempts):
                                has_more_opts = opt_idx < len(edit_param_attempts) - 1
                                still_retrying = has_more_backend or has_more_opts
                                if opt_idx > 0:
                                    logger.info(
                                        f"bot [{bot_id}] pallas_image edits retry params "
                                        f"({req_opts.log_label()}) backend={backend.label} "
                                        f"group=[{group_id}]",
                                    )
                                logger.info(
                                    f"bot [{bot_id}] pallas_image edits request in group [{group_id}] "
                                    f"backend={backend.label} params=({req_opts.log_label()}) "
                                    f"url={edits_ep} images={len(blobs)}",
                                )
                                req_started = time.perf_counter()
                                try:
                                    status, body_text = await post_edits_with_transport(
                                        blobs,
                                        edit_prompt,
                                        backend,
                                        options=req_opts,
                                    )
                                except (
                                    FinishedException,
                                    httpx.TimeoutException,
                                    httpx.ConnectError,
                                    httpx.HTTPError,
                                    CffiRequestsError,
                                    RuntimeError,
                                ) as e:
                                    if still_retrying:
                                        logger.info(
                                            f"bot [{bot_id}] pallas_image edits transport error "
                                            f"backend={backend.label} group=[{group_id}]: {e}, trying next",
                                        )
                                    else:
                                        logger.warning(
                                            f"bot [{bot_id}] pallas_image edits transport error "
                                            f"backend={backend.label} group=[{group_id}]: {e}",
                                        )
                                    break
                                last_body = body_text
                                logger.info(
                                    f"bot [{bot_id}] pallas_image edits response in group [{group_id}]: "
                                    f"backend={backend.label} status={status} "
                                    f"elapsed_ms={(time.perf_counter() - req_started) * 1000:.0f} "
                                    f"body_len={len(body_text)} url={edits_ep}",
                                )
                                if status == 200:
                                    if await reply_from_image_api_json(
                                        matcher,
                                        http_client,
                                        body_text,
                                        at_user_id=user_id,
                                        persist_draw=(usage_key[0], usage_key[1]),
                                        finish_on_error=not still_retrying,
                                    ):
                                        bump_pallas_draw_usage(usage_key, count_usage)
                                        return
                                    issue = image_api_body_issue_label(body_text) or "image_send_failed"
                                    log_image_backend_unusable(
                                        bot_id,
                                        "edits",
                                        backend.label,
                                        group_id,
                                        body_text,
                                        has_more=still_retrying,
                                    )
                                    if issue == "upstream_error":
                                        if upstream_error_visible_to_user(body_text):
                                            await matcher.finish(
                                                message_at_user(user_id, user_failure_reply(body_text))
                                            )
                                            return
                                        skip_backend = True
                                        break
                                    if has_more_opts:
                                        continue
                                    break
                                if still_retrying:
                                    logger.info(
                                        f"bot [{bot_id}] pallas_image edits backend={backend.label} "
                                        f"status={status} in group [{group_id}], trying next",
                                    )
                                else:
                                    logger.warning(
                                        f"bot [{bot_id}] pallas_image edits failed in group [{group_id}]: "
                                        f"backend={backend.label} status={status} body={body_text[:500]}",
                                    )
                                break
                            if skip_backend:
                                continue
                        logger.warning(
                            f"bot [{bot_id}] pallas_image edits exhausted in group [{group_id}], "
                            f"fallback to generations",
                        )

                payload_model = backends[0].model if backends else cfg.model
                last_body = ""
                gen_param_attempts = image_gen_request_attempts(with_ref_urls=bool(ref_urls))
                gen_backends = image_backends_with_endpoint(backends, image_gen_endpoint)
                for idx, backend in enumerate(gen_backends):
                    has_more_backend = idx < len(gen_backends) - 1
                    gen_ep = image_gen_endpoint(backend)
                    auth_json_headers = image_gen_auth_headers_json(backend)
                    skip_backend = False
                    for opt_idx, req_opts in enumerate(gen_param_attempts):
                        has_more_opts = opt_idx < len(gen_param_attempts) - 1
                        still_retrying = has_more_backend or has_more_opts
                        if opt_idx > 0:
                            logger.info(
                                f"bot [{bot_id}] pallas_image generations retry params "
                                f"({req_opts.log_label()}) backend={backend.label} "
                                f"group=[{group_id}]",
                            )
                        payload = generations_payload(
                            gen_prompt,
                            ref_urls,
                            model=backend.model or payload_model,
                            options=req_opts,
                        )
                        logger.info(
                            f"bot [{bot_id}] pallas_image generations request in group [{group_id}] "
                            f"backend={backend.label} params=({req_opts.log_label()}) url={gen_ep}",
                        )
                        request_started = time.perf_counter()
                        try:
                            status, body_text = await post_generations_with_transport(
                                gen_ep,
                                auth_json_headers,
                                payload,
                            )
                        except (
                            FinishedException,
                            httpx.TimeoutException,
                            httpx.ConnectError,
                            httpx.HTTPError,
                            CffiRequestsError,
                            RuntimeError,
                        ) as e:
                            if still_retrying:
                                logger.info(
                                    f"bot [{bot_id}] pallas_image generations transport error "
                                    f"backend={backend.label} group=[{group_id}]: {e}, trying next",
                                )
                            else:
                                logger.warning(
                                    f"bot [{bot_id}] pallas_image generations transport error "
                                    f"backend={backend.label} group=[{group_id}]: {e}",
                                )
                            break
                        last_body = body_text
                        logger.info(
                            f"bot [{bot_id}] pallas_image generations response in group [{group_id}]: "
                            f"backend={backend.label} status={status} "
                            f"elapsed_ms={(time.perf_counter() - request_started) * 1000:.0f} "
                            f"body_len={len(body_text)} url={gen_ep}",
                        )
                        if status == 200:
                            if await reply_from_image_api_json(
                                matcher,
                                http_client,
                                body_text,
                                at_user_id=user_id,
                                persist_draw=(usage_key[0], usage_key[1]),
                                finish_on_error=not still_retrying,
                            ):
                                bump_pallas_draw_usage(usage_key, count_usage)
                                return
                            issue = image_api_body_issue_label(body_text) or "image_send_failed"
                            log_image_backend_unusable(
                                bot_id,
                                "generations",
                                backend.label,
                                group_id,
                                body_text,
                                has_more=still_retrying,
                            )
                            if issue == "upstream_error":
                                if upstream_error_visible_to_user(body_text):
                                    await matcher.finish(message_at_user(user_id, user_failure_reply(body_text)))
                                    return
                                skip_backend = True
                                break
                            if has_more_opts:
                                continue
                            break
                        if still_retrying:
                            logger.info(
                                f"bot [{bot_id}] pallas_image generations backend={backend.label} "
                                f"status={status} in group [{group_id}], trying next",
                            )
                        else:
                            logger.warning(
                                f"bot [{bot_id}] pallas_image generations failed in group [{group_id}]: "
                                f"backend={backend.label} status={status} body={body_text[:500]}",
                            )
                        break
                    if skip_backend:
                        continue
                logger.error(
                    f"bot [{bot_id}] pallas_image generations exhausted backends in group [{group_id}]",
                )
                await matcher.finish(message_at_user(user_id, user_failure_reply(last_body)))
        except FinishedException:
            raise
        except httpx.TimeoutException:
            logger.error(f"bot [{bot_id}] pallas_image api timeout in group [{group_id}] after {cfg.request_timeout}s")
            await matcher.finish(PALLAS_VAGUE_REPLY)
        except httpx.ConnectError as e:
            logger.error(f"bot [{bot_id}] pallas_image api connect error in group [{group_id}]: {e}")
            await matcher.finish(PALLAS_VAGUE_REPLY)
        except CffiRequestsError as e:
            logger.error(f"bot [{bot_id}] pallas_image curl_cffi error in group [{group_id}]: {e}")
            await matcher.finish(PALLAS_VAGUE_REPLY)
        except RuntimeError as e:
            logger.error(f"bot [{bot_id}] pallas_image transport runtime error in group [{group_id}]: {e}")
            await matcher.finish(PALLAS_VAGUE_REPLY)
        except httpx.HTTPError as e:
            logger.error(f"bot [{bot_id}] pallas_image httpx error in group [{group_id}]: {e}")
            await matcher.finish(PALLAS_VAGUE_REPLY)
        except Exception as e:
            logger.exception(f"bot [{bot_id}] pallas_image api exception in group [{group_id}]: {e}")
            await matcher.finish(PALLAS_VAGUE_REPLY)
