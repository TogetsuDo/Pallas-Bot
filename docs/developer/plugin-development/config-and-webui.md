# 配置与 WebUI

Pallas 4.0 下，插件配置不再是“随便加个环境变量再读出来”。

记住三个基本事实：

- 主配置以 `config/pallas.toml` 为基础
- WebUI 统一落盘到 `data/pallas_config/webui.json`
- 运行时最终读取的是合并后的配置，而不是你随手读到的某个单文件

## 先记住配置优先级

当前合并顺序是：

1. `config/pallas.toml`
2. 遗留 `.env`
3. `data/pallas_config/webui.json`

最终以 WebUI 落盘为最高优先级覆盖。

所以：

- 不要再为主配置随意新增根目录 `.env` 键
- 不要假设改了 `pallas.toml` 就一定是运行中的最终值
- 不要在插件里私自维护另一套并行配置来源

## 插件开发里最常见的两种配置接法

### 1. 插件页配置

这是最常见也最推荐的方式。

典型做法：

1. 在 `config.py` 定义 Pydantic 模型
2. 使用 `install_hot_reload_config`
3. 在业务代码中通过 `get_config()` 读取当前值

这样做的好处是：

- WebUI 能自动生成表单
- 保存后可立即热重载
- 配置来源与主仓治理方式一致

### 2. 通用配置段

如果你的配置本质上不是“某个单插件页面”，而是横切能力或全局能力的一部分，就该接到通用配置段，别自造一个独立存储点。

典型例子包括：

- 命令权限
- service gateways
- message scrub
- ingress fanout

## 插件代码应该怎么写

推荐结构：

```python
from pydantic import BaseModel, Field

from pallas.api.config import install_hot_reload_config


class Config(BaseModel, extra="ignore"):
    enable: bool = Field(default=True, description="是否启用。")


plugin_webui = install_hot_reload_config(Config, config_module=__name__)
get_config = plugin_webui.get
```

业务代码里统一这样读：

```python
cfg = get_config()
if not cfg.enable:
    ...
```

::: warning 别长期复用旧快照
不要在模块导入时就 `cfg = get_config()` 然后长期复用这个旧快照。那会让 WebUI 保存后的热重载失效。
:::

## 什么时候需要热重载

如果一个配置项是面向运行中站点维护者调整的，默认就该考虑热重载。

例如：

- 开关项
- 命令文案
- 阈值
- 策略选择

如果改动的是 Python 代码本身、复杂启动流程或深层元数据结构，就别假装它是纯热重载问题。

## 与 WebUI 的边界

分清两件事：

- WebUI 前端页面在 `Pallas-Bot-WebUI`
- WebUI 后端配置、API、热重载逻辑在主仓

所以：

- 表单展示、前端交互、页面布局：去前端仓
- 配置模型、保存逻辑、运行时生效：改主仓

## 插件接配置前的判断题

新增一个配置项前，先问：

1. 这是主配置、插件配置，还是横切通用配置
2. 站长是否需要通过 WebUI 修改
3. 修改后是否应该立即生效
4. 这个值是否真的应该属于该插件，而不是平台共性

很多后续配置混乱，都是因为一开始没做这层判断。

## 当前推荐入口

- 现行开发文档先看这里和 [配置存储](../architecture/config-storage.md)
- 旧的 `docs/common/webui/README.md` 仍保留大量细节，现在更适合作为底层参考

## 相关阅读

- [配置存储](../architecture/config-storage.md)
- [Golden Plugin](golden-plugin.md)
- [WebUI 配置底层说明](../../common/webui/README.md)
