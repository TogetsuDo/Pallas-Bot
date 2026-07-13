# 进阶介绍

已经能 `uv run nb run`，群里 **牛牛帮助** 有回复，就可以按需往下查。不用从头读到尾。

## 想搞懂原理

| 文档 | 你会搞懂 |
| --- | --- |
| [理解架构](concepts.md) | 协议端、Pallas-Bot、库、控制台怎么串 |
| [配置存储](../developer/architecture/config-storage.md) | `pallas.toml` 和 `webui.json` 谁覆盖谁 |
| [运维入口](../maintainer/quickstart.md) / [开发](../developer/index.md) | 正式文档主线 |

## 要上 VPS / 生产

| 文档 | 你会搞懂 |
| --- | --- |
| [配置要点](../Config.md) | 生产环境检查项 |
| [标准部署](../Deployment.md) | systemd、备份 |
| [Docker](../DockerDeployment.md) | Compose、卷、镜像带哪些扩展 |

::: tip 数据库
默认用 **PostgreSQL**。表结构首次启动自动建；先准备好空库。  
从 3.x 升级的站可继续用 MongoDB。
:::

## 连 QQ、装插件、改配置

| 文档 | 你会搞懂 |
| --- | --- |
| [连接 QQ](connect-qq.md) | NapCat、WS、验收口令 |
| [安装插件](install-plugins.md) | core / 官方扩展 / local |
| [使用指南](../user/README.md) | 日常网页操作 |
| [网页控制台](web-console.md) | `/pallas/` 各面板 |

## 多只牛 / 高级玩法

| 文档 | 你会搞懂 |
| --- | --- |
| [多进程分片](../maintainer/deploy/sharded.md) | hub、worker、Redis |
| [站点定制](../maintainer/deploy/upgrade.md) | 更新时不弄丢自己的插件 |
| [AI 扩展](ai.md) | 怎么接 Pallas-Bot-AI |
| [语料联邦](../common/corpus/README.md) | 跨群接话库（多数站可跳过） |

## 出问题了

| 文档 | 你会搞懂 |
| --- | --- |
| [FAQ](../FAQ.md) | 口令忘了、没反应、升级 |
| [命令权限](../common/cmd_perm/README.md) | 谁能用某口令 |

## 要写代码

看 [写第一个插件](../developer/plugin-development/first-plugin.md) 和 [Developer](../developer/index.md)。
