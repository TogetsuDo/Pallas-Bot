from packages.llm_chat.chat_message import user_reply_for_submit_failure
from packages.llm_chat.replies import LLM_CHAT_BUSY_REPLY, LLM_CHAT_FAILED_REPLY


def test_user_reply_for_submit_failure():
    assert user_reply_for_submit_failure("busy") == LLM_CHAT_BUSY_REPLY
    assert user_reply_for_submit_failure("request_failed") == LLM_CHAT_FAILED_REPLY
    assert user_reply_for_submit_failure("cooldown") is None
