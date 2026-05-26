"""帕拉斯 Bot 共享内核，按层划分子包。

- foundation：配置、路径、日志、数据库
- platform：分片、多 Bot、Redis 协调、联邦入口
- features：cmd_perm、语料、社区统计、控制面、消息净化
- console：WebUI 配置段与控制台 Web
- domain：游戏域共享
- shared：工具函数、适配器、服务探测
"""
