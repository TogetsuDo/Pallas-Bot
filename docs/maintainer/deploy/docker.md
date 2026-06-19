# Docker 部署

这页帮你在 Docker 下把路径、端口、共享数据和外部可达地址都对齐。

Docker 场景的重点不是“把容器跑起来”，而是保证运行时路径、端口、共享数据和外部可达地址都一致。

## 哪些东西必须稳定

至少把这几层分开：

- 容器镜像与启动命令
- `config/` 与 `data/` 挂载
- WebUI 静态资源
- 协议端与反向 WS 目标地址
- 分片时 hub / worker 的端口与角色

::: warning
其中一层映射错了，表现通常就是“服务能起来，但功能不对”。
:::

## 推荐先读

- [DockerDeployment](../../DockerDeployment.md)
- [配置参考](../reference/config.md)
- [配置存储](../../architecture/settings-storage.md)

## 最先检查的四件事

### 1. `config/` 和 `data/` 是否真的持久化

Docker 部署最常见的问题不是代码，而是挂载不完整：

- `config/pallas.toml` 没挂进去
- `data/` 没持久化，导致 WebUI 保存、协议端数据、分片 registry 在容器重建后丢失

::: warning 4.0 下尤其注意
- `data/pallas_config/webui.json` 是运行时重要配置落盘
- 分片 registry、协议端数据、控制台运行数据都依赖 `data/`
:::

### 2. WebUI 资源是否与后端版本匹配

常见现象：

- 页面能打开，但样式或功能像旧版
- 后端接口已经变了，前端还在请求旧字段

这通常要回头检查：

- 容器里的静态资源是否已更新
- 是否把正确的 WebUI 产物同步到了主仓运行目录

### 3. 协议端看到的地址是否真能访问

容器内地址、宿主机地址、对外地址经常不是同一个。

::: warning
别默认把这些直接写进协议端或 callback 配置：

- `127.0.0.1`
- Compose 服务名
- 容器内网地址

要以“真正发起连接的一侧能否访问”为准。
:::

### 4. 分片端口是否全部对齐

用 hub + worker 时：

- hub 端口要明确
- 每个 worker 端口要明确
- 对外暴露与注册表分配要一致
- 协议端实例中的 `ws_url` 要对应正确 worker

## Docker 下的推荐理解方式

把容器视为部署壳，而不是配置来源。

也就是说：

- 主配置仍以 `config/pallas.toml` 为主
- WebUI 保存仍以 `data/pallas_config/webui.json` 为主
- Compose 负责注入少量角色相关环境变量和端口映射

::: warning
别把所有长期配置都散落到 Compose 环境变量里，否则后续维护和排障很难收口。
:::

## 单进程与分片的区别

### 单进程

重点检查：

- Bot 监听端口
- WebUI 资源
- 协议端连接地址
- `data/` 是否持久化

### 分片

在上面基础上，再增加：

- hub / worker 是否共用同一 `data/`
- worker 端口是否完整映射
- registry 与实际容器编排是否一致
- AI callback 是否仍回到 hub

## 最常见的三类故障

### 容器重建后配置丢失

通常说明：

- `data/` 没挂载
- 或挂到了错误位置

### 页面是旧的，但后端接口是新的

通常说明：

- 静态资源没更新
- 或主仓运行目录里的 WebUI 产物没有和当前前端版本同步

### 协议端或 AI 回调在本机能通，线上不通

通常说明：

- 配置里用了错误的宿主名或端口
- 容器外部调用方根本访问不到该地址

## Docker 部署时的最小自检

上线前至少确认：

- `config/pallas.toml` 已挂载
- `data/` 已挂载
- WebUI 资源已同步
- 控制台能正常读写配置
- 协议端能连到正确的 WS 地址
- 分片时 hub / worker / registry 三者一致

## 相关阅读

- [单进程部署](single-process.md)
- [分片部署](sharded.md)
- [WebUI](../install/webui.md)
- [协议端](../install/protocol.md)
