from __future__ import annotations

from pathlib import Path

from nonebot import get_driver, logger

_hook_installed = False


def _lexicon_file_readable(path: str) -> bool:
    return Path(path).is_file()


def install_message_scrub_startup_log() -> None:
    global _hook_installed
    if _hook_installed:
        return
    try:
        driver = get_driver()
    except ValueError:
        return
    _hook_installed = True

    @driver.on_startup
    async def _message_scrub_log_config_on_startup() -> None:
        from .api_chain import build_review_providers
        from .config import get_message_scrub_config

        cfg = get_message_scrub_config()

        local_bits: list[str] = []
        if cfg.inbound_filter_substrings:
            local_bits.append("env_substrings")
        if cfg.scrub_lexicon_path:
            if _lexicon_file_readable(cfg.scrub_lexicon_path):
                local_bits.append("lexicon_file")
            else:
                local_bits.append("lexicon_path_invalid")
                logger.warning("message_scrub lexicon path not readable: {}", cfg.scrub_lexicon_path)
        if cfg.scrub_lexicon_extra:
            local_bits.append("extra_substrings")

        if cfg.scrub_baidu_api_key and not cfg.scrub_baidu_secret_key:
            logger.warning(
                "message_scrub Baidu censor disabled: PALLAS_SCRUB_BAIDU_API_KEY set but SECRET missing",
            )
        if cfg.scrub_baidu_secret_key and not cfg.scrub_baidu_api_key:
            logger.warning(
                "message_scrub Baidu censor disabled: PALLAS_SCRUB_BAIDU_SECRET_KEY set but API_KEY missing",
            )

        providers = build_review_providers()
        chain_ids = [p.id for p in providers]

        if cfg.scrub_review_providers_key_present:
            chain_mode = "explicit"
            if not (cfg.scrub_review_providers or "").strip():
                chain_desc = "none"
            else:
                chain_desc = ",".join(chain_ids) if chain_ids else "none_active_check_env"
        else:
            chain_mode = "auto"
            chain_desc = ",".join(chain_ids) if chain_ids else "none"

        local_on = bool(local_bits)
        intercept_on = local_on or bool(chain_ids)

        local_human = "+".join(local_bits) if local_bits else "none"
        api_fail_open = cfg.inbound_filter_api_fail_open

        logger.info(
            "message_scrub startup inbound_filter={} local_sources={} remote_mode={} "
            "remote_providers={} api_fail_open={} api_timeout_sec={}",
            "enabled" if intercept_on else "disabled_no_local_no_remote",
            local_human,
            chain_mode,
            chain_desc,
            api_fail_open,
            cfg.inbound_filter_api_timeout_sec,
        )
