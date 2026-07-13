# 本体安装

把 `Pallas-Bot` 本体装上并跑起来。

## 依赖与基础步骤

- Python 3.12
- `uv`
- 数据库：**PostgreSQL**（4.0 默认），见 [配置参考](../reference/config.md)；3.x 升级可继续 MongoDB
- Redis：仅分片 / AI 等场景需要

想直接动手，看这几篇：

- [五分钟跑起来](../../guide/quickstart.md)
- [把玩法 / AI 也装上](../../guide/4.0-start.md)
- [本地开发环境](../../develop/environment.md)

## 4.0 本体的角色

本体负责这些事：

- 消息入口
- 插件加载
- 配置合并
- WebUI API
- 分片协调
- AI callback 落地

::: tip
4.0 之后，很多玩法不再内置在本体里，而是拆成了官方插件。本体跑起来后，还想要决斗、MAA 这类能力，去看 [安装官方插件](official-extensions.md)。
:::
