# 插件开发入门

第一次写 Pallas 4.0 插件？这页就是你的入口。

你要做的：

- 先做出一个最小可运行插件
- 再把它接进帮助、权限、配置、测试与文档
- 从一开始就按 4.0 的结构和治理方式写，别沿用旧 `src.*` 时代的散装写法

## 先理解你在写哪类插件

Pallas 里常见的插件来源有三类：

| 类型 | 放哪 | 适合什么 |
| --- | --- | --- |
| 站点私有插件 | `local/plugins/` | 本地定制、试验功能、未准备上游化 |
| 内置 / core 插件 | `packages/` | 主仓内置能力 |
| 官方或社区扩展 | 独立仓库 | 独立发布、独立安装、独立版本 |

只是想先写功能验证的话，优先从 `local/plugins/` 开始。

## 一个最小插件至少要接什么

按 4.0 标准，“算完成”的插件不只是能响应命令。至少补齐：

- 插件入口与元数据
- 命令权限
- 帮助文案
- 配置接法
- 最小测试
- README

## 推荐学习顺序

1. [Golden Plugin](golden-plugin.md)
2. [配置与 WebUI](config-and-webui.md)
3. [pallas.api Cookbook](pallas-api-cookbook.md)
4. [测试](testing.md)
5. [元数据](metadata.md)

想要一个从零跟做的例子，先按 [Golden Plugin](golden-plugin.md) 和 [配置与 WebUI](config-and-webui.md) 这条主线继续补。

## 当前插件开发的几个硬边界

### 不再使用旧 `src.*` 作为社区入口

现在的推荐 API 入口是 `pallas.api.*`。

### 不要把所有逻辑塞进 `__init__.py`

入口文件负责声明与注册，不负责承载全部实现。

### 不要把权限写死在帮助文案里

权限应通过 `command_permissions` 和运行时治理系统表达。

### 不要跳过测试和 README

::: tip 站点私有插件也别省
哪怕是站点私有插件，也至少保留最小文档和最小验证。
:::

## 你现在可以怎么开始

要立刻动手，最稳的顺序是：

1. 先按 [Golden Plugin](golden-plugin.md) 定目录
2. 在 `config.py` 接热重载配置
3. 在 `__init__.py` 声明 metadata 和命令权限
4. 在 `handlers.py` 写口令逻辑
5. 补一个最小测试和 README

## 相关阅读

- [Golden Plugin](golden-plugin.md)
- [配置与 WebUI](config-and-webui.md)
