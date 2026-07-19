# dream（牛牛做梦）

做梦期间推送梦话：跨群漂流、历史梦、画画归档图、复读已学句；醉酒时更密且可联动夺舍。

## 用户命令

| 口令 | 场景 | 说明 |
| --- | --- | --- |
| 牛牛做梦 | 群内 | 进入做梦约 5～15 分钟 |
| 牛牛醒梦 / 牛牛别做梦 | 群内 | 结束做梦 |
| 牛牛醒一醒 | 群内 | 醒酒时亦会醒梦（见 drink） |

## 命令权限

| 命令 ID | 默认等级 |
| --- | --- |
| `dream.ban_cleanup` | staff |

（与复读共用「不可以」清理梦库，权限见 repeater / 帮助详情。）

## 配置

[`config.py`](../../../src/plugins/dream/config.py)：`dream_worker_sleep_*`、`dream_drift_queue_tick_probability`、`dream_message_retention_days` 等。入站过滤见 [message_scrub](../../common/message_scrub/README.md)。

## 排障

| 现象 | 处理 |
| --- | --- |
| 无梦话 | 确认已做梦、冷却未挡；他群无做梦则无漂流 |
| 梦库过大 | 运维可调用 `library_cleanup.delete_expired_dream_messages` |

## 实现

[`src/plugins/dream/`](../../../src/plugins/dream/)
