from src.common.platform.bot_runtime.plugin_loader import _prioritize_scheduler_modules


def test_prioritize_scheduler_modules_puts_apscheduler_first():
    paths = ["my_pack", "nonebot_plugin_apscheduler", "other"]
    assert _prioritize_scheduler_modules(paths) == [
        "nonebot_plugin_apscheduler",
        "my_pack",
        "other",
    ]
