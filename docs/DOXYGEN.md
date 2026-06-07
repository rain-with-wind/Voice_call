# Doxygen 注释规范说明

本项目的 Python 代码注释按 Doxygen 风格整理，便于课程作业检查、后续维护，以及未来生成统一文档。

## 约定格式

模块头部：

```python
"""@file engine.py
@brief Audio transport engine for direct duplex voice calls over TCP.
"""
```

函数或方法：

```python
def connect_to_server(server_host):
    """@brief Connect to an already running voice call server.

    @param server_host Hostname or IP address of the remote server.
    @return None
    """
```

## 已采用的标签

- `@file`：说明文件名
- `@brief`：一句话概述职责
- `@param`：描述输入参数
- `@return`：描述返回值
- `@exception`：描述可能抛出的异常

## 编写建议

- `@brief` 保持简洁，聚焦“这个对象负责什么”
- `@param` 优先描述语义，而不是重复变量名
- 返回值是布尔值时，明确 `True` / `False` 的含义
- 私有函数如果承担关键逻辑，也建议补充 Doxygen 风格说明
- 用户可见行为变更除了写代码注释，也应同步更新 `README.md` 与 `docs/`

## 当前覆盖范围

目前已重点覆盖以下核心模块：

- `voice_call.py`
- `voice_call_cli/cli.py`
- `voice_call_cli/engine.py`
- `voice_call_cli/public_commands.py`
- `voice_call_cli/backend_client/api.py`
- `public_backend/app/__init__.py`
- `public_backend/app/routes/rooms.py`
- `public_backend/app/room_registry.py`

这部分已经足够支持课程检查和后续继续扩展。
