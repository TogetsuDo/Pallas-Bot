from nonebot.adapters.onebot.v11 import Adapter as OneBotV11Adapter

from src.common.shared.adapters.onebot_v11_custom_events import ProfileLikeNotifyEvent, register_onebot_v11_custom_events


def test_profile_like_notify_event_parses_napcat_payload() -> None:
    payload = {
        "time": 1779553477,
        "self_id": 3976691212,
        "post_type": "notice",
        "notice_type": "notify",
        "sub_type": "profile_like",
        "operator_id": 3791098674,
        "operator_nick": "tester",
        "times": 10,
    }
    event = ProfileLikeNotifyEvent.model_validate(payload)
    assert event.operator_id == 3791098674
    assert event.user_id == 3791098674
    assert event.group_id == 0
    assert event.get_user_id() == "3791098674"


def test_register_onebot_v11_custom_events() -> None:
    register_onebot_v11_custom_events()
    models = OneBotV11Adapter.get_event_model(
        {
            "post_type": "notice",
            "notice_type": "notify",
            "sub_type": "profile_like",
        }
    )
    assert ProfileLikeNotifyEvent in models
