# duel（牛牛决斗）

泰拉风味多幕决斗：事件包、干员/关键词 QTE、双牛八角笼、胜负惩罚。

## 用户命令

| 口令 | 场景 | 说明 |
| --- | --- | --- |
| 牛牛决斗 @对手 [N幕\|N回合] | 群内 | 对人或单牛 |
| 牛牛决斗 @牛A @牛B | 群内 | 双牛对决 |
| 八角笼牛 [N幕\|N回合] | 群内 | 随机两只在线牛牛 |
| 按幕面提示答干员名/关键词 | 群内 | QTE 抢答 |
| 决斗事件重载 | 群内 | 热更新事件包（群管） |

## 命令权限

| 命令 ID | 默认等级 |
| --- | --- |
| `duel.duel` | everyone |
| `duel.cage` | everyone |
| `duel.reload_events` | group_moderator |

## 配置

WebUI **插件 → duel** 或 [`config.py`](../../../src/plugins/duel/config.py)。事件包约定见 [`event_packs/README.md`](../../../src/plugins/duel/event_packs/README.md)。

资源同步：

```bash
uv run python scripts/fetch_arknights_duel_data.py
```

## 排障

| 现象 | 处理 |
| --- | --- |
| 无法开战 | 同群仅一场；检查 @ 与在线牛 |
| 乱入无头像 | 执行资源脚本补 `resource/arknights/avatars` |

## 实现

[`src/plugins/duel/`](../../../src/plugins/duel/)
