from src.plugins.help.help_constants import HELP_STATUS_OFF, HELP_STATUS_ON, HELP_STATUS_PLACEHOLDER
from src.plugins.help.status_dots import parse_plugin_table_statuses, should_paint_help_status_dots


def test_parse_plugin_table_statuses() -> None:
    md = (
        "## 插件列表\n\n"
        "| 序号 | 名称 | 状态 | 简介 |\n"
        "|------|------|------|------|\n"
        f"| 1 | A | {HELP_STATUS_ON} | 说明 |\n"
        f"| 2 | B | {HELP_STATUS_OFF} | 说明2 |\n"
    )
    assert should_paint_help_status_dots(md)
    assert parse_plugin_table_statuses(md) == [True, False]
