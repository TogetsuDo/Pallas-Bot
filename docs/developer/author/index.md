# Author

这一组页面面向三类开发者：

- 本体维护者
- 官方扩展作者
- 社区插件作者

它不是新的第三条文档主线，而是一个“以作者视角读 Developer 文档”的整理入口。

## 先读什么

1. [架构总览](../architecture/overview.md)
2. [Core 与扩展](../architecture/core-vs-extensions.md)
3. [Golden Plugin](../plugin-development/golden-plugin.md)
4. [配置与 WebUI](../plugin-development/config-and-webui.md)
5. [发布](../plugin-development/publishing.md)

## 为什么要有作者视角

同样是“开发 Pallas 生态”，三类作者面对的边界其实不同：

- 本体维护者关心平台边界、运行时结构和长期演进
- 官方扩展作者关心版本、治理、PyPI 和与主仓协作
- 社区插件作者关心稳定公开入口、接入成本和分发方式

如果不先分清你是哪类作者，就很容易读到一半发现自己在看不属于自己的规则。

## 三类作者分别该怎么理解 4.0

### 本体维护者

重点应放在：

- 内核与平台分层
- Core 与扩展边界
- 分片运行时
- 配置与治理统一入口

更具体地说，本体维护者首先要防止“把所有能力继续塞回主仓”。

### 官方扩展作者

重点应放在：

- 扩展与主仓的职责边界
- 元数据、治理、配置接入
- 版本号、README、PyPI 发布
- 与 WebUI 和 activation policy 的协同

官方扩展作者写的不是“临时插件”，而是站长会长期安装和升级的正式能力包。

### 社区插件作者

重点应放在：

- 只依赖现行公开入口
- 不碰内部 API
- README、metadata、目录结构规范
- 合适的索引与分发方式

社区插件作者最重要的不是“能跑起来”，而是“不要把主仓当前实现细节当长期契约”。

## 你要理解的边界

- Pallas 4.0 不再把所有能力都塞进本体
- core、official extension、community extension 职责不同
- WebUI 源码仓与主仓运行产物分离
- 单进程与分片场景下，插件激活策略不同
- `pallas.api.*`、Platform API、Internal API 不是一回事

## 开发者最常见的三种跑偏

### 作者身份没分清

比如明明在写社区插件，却一路按主仓内部协作模式去 import 和设计。

### 仓库边界没分清

比如把 WebUI 前端问题放在主仓运行产物里修，把扩展仓问题硬塞进主仓。

### 稳定边界没分清

比如把当前内部实现直接当成长期公开 API 使用。

## 建议阅读路径

### 如果你是本体维护者

建议顺序：

1. [架构总览](../architecture/overview.md)
2. [分片运行时](../architecture/shard-runtime.md)
3. [插件治理与分层](../architecture/plugin-governance.md)
4. [仓库结构](../reference/repo-layout.md)

### 如果你是官方扩展作者

建议顺序：

1. [Core 与扩展](../architecture/core-vs-extensions.md)
2. [Golden Plugin](../plugin-development/golden-plugin.md)
3. [元数据](../plugin-development/metadata.md)
4. [发布](../plugin-development/publishing.md)

### 如果你是社区插件作者

建议顺序：

1. [插件开发入门](../plugin-development/getting-started.md)
2. [配置与 WebUI](../plugin-development/config-and-webui.md)
3. [Platform API](../reference/platform-api.md)
4. [Internal API](../reference/internal-api.md)

## 相关阅读

- [Developer](../index.md)
- [仓库结构](../reference/repo-layout.md)
- [写作与风格约定](../reference/style-guide.md)
