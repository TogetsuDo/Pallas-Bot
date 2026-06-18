from packages.pb_protocol import __plugin_meta__, manager
from packages.pb_protocol.startup import manager as startup_manager


def test_pb_protocol_metadata():
    assert __plugin_meta__.name == "协议端管理"
    assert __plugin_meta__.extra.get("help_audience") == "maintainer"
    assert __plugin_meta__.extra.get("reload_policy") == "metadata"


def test_pb_protocol_manager_reexported():
    assert manager is startup_manager
