from types import SimpleNamespace

from src.common.features.cmd_perm.help_menu import (
    help_say_phrase,
    help_scene_text,
    is_user_help_menu_item,
    is_user_help_plugin,
    iter_user_help_menu,
)


def test_help_say_strips_scene_paren() -> None:
    item = {"trigger_condition": "设置群欢迎（群内）", "trigger_scene": "群内"}
    assert help_say_phrase(item) == "设置群欢迎"


def test_help_scene_explicit() -> None:
    item = {"trigger_method": "on_message", "trigger_scene": "私聊"}
    assert help_scene_text(item) == "私聊"


def test_maintainer_filtered_from_user_menu() -> None:
    menu = [
        {"func": "用户功能", "trigger_condition": "牛牛帮助"},
        {"func": "HTTP", "help_audience": "maintainer", "trigger_condition": "/api"},
    ]
    assert len(list(iter_user_help_menu(menu))) == 1
    assert is_user_help_menu_item(menu[1]) is False


def test_maintainer_plugin_extra_excluded_from_user_help() -> None:
    user_plugin = SimpleNamespace(metadata=SimpleNamespace(extra={"help_audience": "user"}))
    maintainer_plugin = SimpleNamespace(metadata=SimpleNamespace(extra={"help_audience": "maintainer"}))
    assert is_user_help_plugin(user_plugin) is True
    assert is_user_help_plugin(maintainer_plugin) is False
    assert is_user_help_plugin(SimpleNamespace(metadata=None)) is True
