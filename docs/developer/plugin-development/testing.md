# 测试

插件测试的目标不是“把所有路径都跑一遍”，而是证明你新增或修改的行为在 4.0 体系里仍然成立。

## 至少覆盖哪些内容

- 行为测试
- 元数据测试
- 配置与权限测试
- 分片相关能力测试（如果有）

## 最少思路

### 行为测试

验证命令、触发条件和主要输出是否符合预期。

### 元数据测试

验证 `command_permissions`、`menu_data`、`command_limits` 等声明是否完整、ID 是否一致。

### 配置测试

验证配置默认值、开关和关键参数是否会影响行为。

### 分片相关测试

如果插件涉及：

- 同群独占
- 跨 worker 协调
- hosted activity
- AI callback

那至少要补一类分片下的行为验证。

## 目录约定

插件测试通常放在：

```text
tests/plugins/<plugin_name>/
```

如果是平台或跨插件行为，也可能落在：

- `tests/common/`
- `tests/platform/`

## 什么时候不够

只测“函数能调用”通常不够。对 4.0 插件来说，更重要的是：

- 权限是否接对
- metadata 是否能被平台理解
- 配置和热重载语义是否一致

## 相关阅读

- [贡献与提交流程](../../develop/workflow.md)
- [本地开发环境](../../develop/environment.md)
- [Golden Plugin](golden-plugin.md)
- 仓库内 `tests/plugins/*`
