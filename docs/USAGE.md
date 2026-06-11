# 使用指南

## 环境要求

- Python 3.10+
- 可用的麦克风和扬声器
- Windows / WSL / Linux

## 安装

**Windows (PowerShell)：**

```powershell
pip install -r requirements.txt
```

**Linux / WSL：**

```bash
# 先安装系统音频库
sudo apt-get update
sudo apt-get install -y python3-dev portaudio19-dev

# 安装 Python 依赖
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 启动服务端

```powershell
python voice_call.py --mode server --port 5000
```

带密码和加密：

```powershell
python voice_call.py --mode server --port 5000 --encrypt --password 你的密码
```

## 启动客户端

```powershell
python voice_call.py --mode client --host 192.168.1.100 --port 5000
```

## 列出音频设备

```powershell
python voice_call.py --list-devices
```

输出示例：

```
[音频] 共 4 个设备 (默认输入: 麦克风 (Realtek), 默认输出: 扬声器 (Realtek)):
  [0] 麦克风 (Realtek)  [输入×2] ← 默认输入
  [1] Stereo Mix (Realtek)  [输入×2]
  [2] 扬声器 (Realtek)  [输出×2] ← 默认输出
  [3] 线路输入 (Realtek)  [输入×2]
```

## 手动指定音频设备

```powershell
# 使用设备 0 作为麦克风，设备 2 作为扬声器
python voice_call.py --mode server --port 5000 --input-device 0 --output-device 2
```

## 全部参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--mode` | 必选 | `server` (服务端) 或 `client` (客户端) |
| `--host` | `127.0.0.1` | 客户端模式下的服务端地址 |
| `--port` | `5000` | TCP 端口号 |
| `--password` | 无 | 共享密码 |
| `--encrypt` | 否 | 启用 Fernet 端到端加密 |
| `--rate` | `48000` | 音频采样率 (Hz) |
| `--channels` | `1` | 音频声道数 |
| `--chunk` | `1024` | 音频帧大小 |
| `--input-device` | 自动 | 手动指定输入设备编号 |
| `--output-device` | 自动 | 手动指定输出设备编号 |
| `--list-devices` | — | 列出所有音频设备后退出 |

## 跨系统互通

已验证的组合：

- Windows ↔ Windows
- Windows ↔ WSL
- WSL ↔ Linux

## 常见问题

### 无法导入 `pyaudio`

在 Linux 上先装系统音频库，再装 Python 包：

```bash
sudo apt-get install -y portaudio19-dev python3-dev
pip install pyaudio
```

### 麦克风持续静音

使用 `--list-devices` 查看可用设备，然后用 `--input-device` 手动指定正确的麦克风。常见问题是选到了 Stereo Mix 或线路输入。

### WSL 打印 ALSA/JACK 警告

WSL 下的正常现象，只要通话中 `上传` 和 `下载` 有流量就说明链路正常。

### Connection refused

检查：服务端已启动、端口正确、防火墙允许连接、IP 地址可达。
