# 控制台只读 API 压测

## 快速运行

```bash
export PALLAS_CONSOLE_PASSWORD='你的口令'
# 或开发机：PALLAS_BENCH_DEV_TOKEN=1（自动 mint 会话 token）

THREADS=16 DURATION_SEC=30 bash tools/jmeter/run_console_load.sh
```

结果目录：`data/bot/jmeter/`（JMeter `.jtl` 或 httpx 回退的 `summary_http_*.txt`）。

## JMeter vs httpx 回退

- **apt `jmeter`（2.13）** 在 Java 17+ 上加载手写 JMX 会失败（`ScriptWrapper` / XStream）。
- `run_console_load.sh` 在 JMeter 失败或 `FORCE_HTTP_LOAD=1` 时自动改用 `http_console_load.py`（同等 4 个 GET 端点）。
- 若需原生 JMeter：解压 [Apache JMeter 5.6+](https://jmeter.apache.org/download_jmeter.cgi) 并设置 `JMETER_BIN=/path/to/jmeter`。

## 环境变量

| 变量 | 说明 |
| --- | --- |
| `HOST` / `PORT` | 默认 `127.0.0.1` / `8088`（与 WebUI dev 代理一致，按本机改） |
| `THREADS` | 并发（默认 20，见 `run_console_load.sh`） |
| `DURATION_SEC` | 持续时间（默认 60） |
| `PALLAS_CORPUS_USAGE_HTTP_TIMEOUT_SEC` | 语料 usage 远程超时（默认 3） |
| `PALLAS_CORPUS_USAGE_CACHE_SEC` | usage 进程内缓存 TTL（默认 120） |
