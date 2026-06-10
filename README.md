# Voice Call CLI

基于 WebSocket 音频引擎 + Flask 房间协调后端的语音通话工具，支持 Windows / WSL / Linux。

## 可用命令

| 命令 | 说明 |
|------|------|
| `host-public` | 创建房间，等待对方加入（服务端） |
| `join-public` | 通过房间码加入房间（客户端） |
| `list-rooms` | 查看在线房间列表 |
| `backend-health` | 检查后端是否正常 |
| `device-info` | 查看本机设备信息 |
| `--mode server/client` | 局域网 TCP 直连（旧版模式） |

## 环境准备

### Windows

```bash
cd d:\python\pythonproject\Voice_call
pip install -r requirements.txt
pip install flask flask-sock
```

### WSL / Linux

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip portaudio19-dev

# 语音 CLI
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 后端
python3 -m venv .venv-backend && source .venv-backend/bin/activate
pip install -r requirements-backend.txt
```

## 本地使用

### 1. 启动后端

**Windows：**

```bash
cd d:\python\pythonproject\Voice_call\public_backend
python run.py
```

**WSL / Linux：**

```bash
bash deploy/public/run_backend_wsl.sh
```

后端监听 `http://127.0.0.1:8100`，浏览器打开可见房间管理页面。

### 2. 发起通话

服务端创建房间：

```bash
python voice_call.py host-public --backend-url http://127.0.0.1:8100 --room-name 我的房间
```

客户端加入房间：

```bash
python voice_call.py join-public --backend-url http://127.0.0.1:8100 --room-code <房间码>
```

查看在线房间：

```bash
python voice_call.py list-rooms --backend-url http://127.0.0.1:8100
```

## 公网部署（ngrok）

只需一条 ngrok HTTP 隧道，语音通过 WebSocket 自动走同一通道。

### 步骤 1：启动后端

```bash
cd d:\python\pythonproject\Voice_call\public_backend
python run.py
```

### 步骤 2：启动 ngrok

```bash
ngrok http 8100
```

记下输出的地址 `https://xxxx-xxx.ngrok-free.app`。

### 步骤 3：通话

服务端：

```bash
python voice_call.py host-public --backend-url https://xxxx-xxx.ngrok-free.app --room-name 测试房间
```

客户端：

```bash
python voice_call.py join-public --backend-url https://xxxx-xxx.ngrok-free.app --room-code <房间码>
```

### 部署一览

```
终端 1：cd public_backend && python run.py
终端 2：ngrok http 8100

服务端                             客户端
┌──────────────┐                   ┌──────────────┐
│ Flask + WS   │                   │              │
│     ↓        │                   │              │
│ ngrok HTTP   │─── 互联网 ───────→│ join-public  │
└──────────────┘                   └──────────────┘
```

## 注意事项

- 保持后端和 ngrok 终端持续运行
- ngrok 免费版重启后 URL 会变化，需重新告知对方
- 局域网内推荐用 `--mode server/client` TCP 直连，延迟更低

## 许可证

MIT License
