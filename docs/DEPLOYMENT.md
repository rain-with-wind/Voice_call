# 部署说明

本文档面向 WSL、本地 Linux 虚拟机，以及后续公网部署场景。

## 1. WSL / Linux 本地部署

### 系统依赖

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip portaudio19-dev
```

### 语音 CLI 环境

```bash
cd /mnt/d/QQ/Downloads/Voice_call/Voice_call_cli
bash deploy/wsl/setup_wsl.sh
```

### 公网协调后端环境

```bash
cd /mnt/d/QQ/Downloads/Voice_call/Voice_call_cli
bash deploy/public/setup_backend_wsl.sh
```

### 启动后端

```bash
bash deploy/public/run_backend_wsl.sh
```

默认访问地址：

- 前端首页：`http://127.0.0.1:8100/`
- 健康检查：`http://127.0.0.1:8100/api/health`

## 2. 语音通话启动方式

### 直接 TCP 模式

服务端：

```bash
python3 voice_call.py --mode server --port 5000
```

客户端：

```bash
python3 voice_call.py --mode client --host 192.168.43.62 --port 5000
```

### 基于后端的房间模式

服务端注册房间：

```bash
python3 voice_call.py host-public \
  --backend-url http://127.0.0.1:8100 \
  --room-name demo-room \
  --public-host 127.0.0.1 \
  --port 5000
```

客户端按房间码加入：

```bash
python3 voice_call.py join-public \
  --backend-url http://127.0.0.1:8100 \
  --room-code ABC123
```

## 3. 公网部署建议

如果需要让外部客户通过域名访问后端，可按以下方式部署：

1. 将 `public_backend` 运行在 Linux 服务器或云主机上
2. 使用 `gunicorn public_backend.wsgi:app` 作为生产 WSGI 服务
3. 使用 `nginx` 做反向代理
4. 为后端域名配置 DNS 解析
5. 为语音服务开放实际 TCP 端口，例如 `5000`
6. 确保客户端能访问房主机器的 `public_host:public_port`

可参考：

- `deploy/public/backend.service`
- `deploy/public/nginx.conf`

## 4. 验证步骤

### Python 语法验证

```bash
python3 -m compileall voice_call.py voice_call_cli public_backend
```

### 后端冒烟测试

```bash
bash deploy/public/smoke_test_backend.sh
```

### 语音链路测试

在一端启动：

```bash
python3 voice_call.py --mode server --port 5000
```

另一端连接：

```bash
python3 voice_call.py --mode client --host 192.168.43.62 --port 5000
```

## 5. 当前限制

- 浏览器前端只负责房间控制与语音通话可视化，不直接承载浏览器内音视频通话
- 真实语音流量仍走 TCP 音频通道
- 跨 NAT、弱网适配和浏览器原生通话能力仍有限
- 如需进一步升级，推荐下一阶段引入 WebRTC
