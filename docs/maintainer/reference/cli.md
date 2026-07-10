# CLI 参考

这页记录维护者日常最常用的命令入口，不展开内部实现细节。

## 最常用的命令

### 官方扩展

```bash
uv run pallas ext install pallas-plugin-duel
uv run pallas ext uninstall pallas-plugin-duel
```

适合：

- 安装官方扩展
- 卸载官方扩展
- 配合重启让新状态生效

### 同步依赖

```bash
uv run pallas sync
```

适合：

- 拉齐环境
- 更新依赖
- 部署前后做一次统一同步

### AI Runtime 安装

```bash
uv run pallas ai path
uv run pallas ai setup
uv run pallas ai setup --check-only
```

需同级目录 **Pallas-Bot-AI**，或设置 `PALLAS_AI_ROOT`。验收见 [安装验收 Checklist](../install/ga-install-checklist.md)。

### 启停与部署脚本

这两个脚本你仍会频繁用到：

- `./scripts/run_unified_bot.sh`
- `./scripts/run_sharded_bot.sh`

单进程、分片、测试 worker 这几类场景里，它们仍是最稳定的运维入口。

## 什么时候优先用 CLI

- 服务器上没有打开 WebUI
- 需要脚本化操作
- 想明确控制安装、同步、启停过程

## 什么时候优先用 WebUI

- 想直接通过插件商店安装扩展
- 想改运行中配置
- 想看运行态和聚合状态

## 相关阅读

- [安装官方扩展](../install/official-extensions.md)
- [分片部署](../deploy/sharded.md)
- [单进程部署](../deploy/single-process.md)
