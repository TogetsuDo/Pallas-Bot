# 补丁说明（可选）

若必须修改主仓已跟踪文件，请在此记录 diff 与原因；长期应改为 `local/plugins/` 独立插件或向上游贡献。

## 建议做法

1. 导出补丁：`git diff HEAD -- bot.py src/common/... > local/patches/你的说明.patch`
2. 在 patch 同目录或本文件注明：改了什么、为何不能插件化、对应上游 issue/PR（如有）。
3. 主仓 tag 更新后：`git apply --check local/patches/xxx.patch`，再 `git apply` 或手工合并。

在线更新前请尽量把定制迁出 `src/plugins/`，避免与 Release tag 冲突；`src/common/*`、入口脚本等只能走 patch 或 PR。
