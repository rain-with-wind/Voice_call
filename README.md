# Voice Call CLI

基于 WebSocket 音频引擎 + Flask 房间协调后端的语音通话工具，支持 Windows / WSL / Linux 环境。

## 功能特性

- 实时双工语音通话，通过 WebSocket 中继传输
- 公共房间的注册、发现、心跳保持和关闭
- 浏览器房间管理面板
- 只需 ngrok HTTP 一条隧道即可公网通话（无需 TCP 隧道）

## 项目结构

```
Voice_call/
├── deploy/
│   ├── public/
│   │   ├── run_backend_wsl.sh
│   │   ├── setup_backend_wsl.sh
│   │   └── smoke_test_backend.sh
│   └── wsl/
│       ├── run_client.sh
│       ├── run_server.sh
│       ├── setup_wsl.sh
│       └── smoke_test.sh
├── public_backend/
│   ├── app/
│   │   ├── routes/
│   │   │   ├── health.py
│   │   │   ├── rooms.py
│   │   │   └── voice.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── room_registry.py
│   │   └── __init__.py
│   ├── frontend/
│   │   ├── assets/
│   │   │   ├── app.js
│   │   │   └── styles.css
│   │   └── index.html
│   ├── run.py
│   └── wsgi.py
├── voice_call_cli/
│   ├── backend_client/
│   │   ├── api.py
│   │   └── __init__.py
│   ├── cli.py
│   ├── config.py
│   ├── console.py
│   ├── engine.py
│   ├── ws_engine.py
│   ├── public_commands.py
│   └── stats.py
├── voice_call.py
├── requirements.txt
├── requirements-backend.txt
└── README.md
```

## 环境准备

### Windows

语音 CLI：

```bash
cd d:\python\pythonproject\Voice_call
pip install -r requirements.txt
```

后端：

```bash
cd d:\python\pythonproject\Voice_call
pip install flask flask-sock
```

### WSL / Linux

系统依赖：

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip portaudio19-dev
```

语音 CLI：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

后端：

```bash
python3 -m venv .venv-backend
source .venv-backend/bin/activate
pip install -r requirements-backend.txt
```

## 本地使用

### 直接 TCP 模式（局域网直连）

服务端：

```bash
python voice_call.py --mode server --port 5000
```

客户端：

```bash
python voice_call.py --mode client --host 192.168.1.100 --port 5000
```

### 公共房间模式（通过后端中继）

启动后端：

**Windows：**

```bash
cd d:\python\pythonproject\Voice_call\public_backend
python run.py
```

**WSL / Linux：**

```bash
bash deploy/public/run_backend_wsl.sh
```

后端监听 `0.0.0.0:8100`，前端页面 `http://127.0.0.1:8100/`。

创建房间（服务端）：

```bash
python voice_call.py host-public \
  --backend-url http://127.0.0.1:8100 \
  --room-name 我的房间
```

加入房间（客户端）：

```bash
python voice_call.py join-public \
  --backend-url http://127.0.0.1:8100 \
  --room-code ABC123
```

查看在线房间：

```bash
python voice_call.py list-rooms --backend-url http://127.0.0.1:8100
```

## 公网部署

只需启动后端并通过 ngrok 暴露 HTTP 端口，语音数据通过 WebSocket 自动走同一隧道。

### 步骤 1：启动后端

**Windows：**

```bash
cd d:\python\pythonproject\Voice_call\public_backend
python run.py
```

### 步骤 2：启动 ngrok

```bash
ngrok http 8100
```

输出示例：

```
Forwarding: https://xxxx-xxx.ngrok-free.app -> http://localhost:8100
```

记下 `https://xxxx-xxx.ngrok-free.app` → **Backend URL**。

### 步骤 3：发起通话

服务端（创建房间）：

```bash
python voice_call.py host-public \
  --backend-url https://xxxx-xxx.ngrok-free.app \
  --room-name 测试房间
```

客户端（加入房间）：

```bash
python voice_call.py join-public \
  --backend-url https://xxxx-xxx.ngrok-free.app \
  --room-code <对方提供的房间码>
```

### 部署一览

```
终端 1：cd public_backend && python run.py      → Flask 后端 :8100
终端 2：ngrok http 8100                          → 公网 API + 语音中继（WebSocket）

服务端机器                          客户端机器
┌─────────────────┐                ┌─────────────────┐
│  Flask 后端      │                │                 │
│  + WS 中继       │                │                 │
│       ↓         │                │                 │
│  ngrok HTTP     │──── 互联网 ────│  voice_call.py  │
│  (单条隧道)     │                │  join-public    │
└─────────────────┘                └─────────────────┘
```

## 常见问题

**Q: Ctrl+C 无法退出通话？**

A: 已修复，按 Ctrl+C 可以正常退出。

**Q: 提示 `ConnectionRefusedError`？**

A: 确保后端已启动，检查 `http://127.0.0.1:8100/api/health` 是否返回正常。

**Q: 语音延迟或卡顿？**

A: ngrok 免费版带宽有限。局域网内使用直接 TCP 模式延迟更低。

## 许可证

本项目基于 [MIT License](./LICENSE) 发布。
