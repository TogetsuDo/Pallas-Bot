from packages.llm_chat import __plugin_meta__


def test_llm_chat_metadata_uses_sdk_declarations():
    perms = __plugin_meta__.extra.get("command_permissions") or []
    limits = __plugin_meta__.extra.get("command_limits") or []
    assert {row["id"] for row in perms} == {"llm_chat.chat", "llm_chat.clear"}
    assert limits[0]["id"] == "llm_chat.chat"
    assert limits[0]["cd_sec"] == 3
    assert __plugin_meta__.extra.get("reload_policy") == "metadata"
    assert __plugin_meta__.extra.get("ingress_route") == {"lane": "remote"}


def test_llm_chat_metadata_declares_llm_tools():
    tools = __plugin_meta__.extra.get("llm_tools") or []
    names = {row["name"] for row in tools}
    assert names == {"llm_chat.clear"}
    clear_tool = next(row for row in tools if row["name"] == "llm_chat.clear")
    assert clear_tool["command_id"] == "llm_chat.clear"
    assert clear_tool["command_template"] == "clear"
