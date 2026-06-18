from packages.pb_core import __plugin_meta__
from pallas.core.commands import missing_command_declarations


def test_pb_core_metadata_declares_all_commands():
    command_ids = {
        "pb_core.status",
        "pb_core.console",
        "pb_core.plugins",
        "pb_core.update_check",
        "pb_core.restart",
    }
    assert missing_command_declarations(__plugin_meta__.extra, command_ids=command_ids) == []


def test_pb_core_help_name():
    assert __plugin_meta__.name == "牛牛核心"
