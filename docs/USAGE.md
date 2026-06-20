# 使用说明

本文档记录项目的安装、启动、参数和常见问题。初次运行建议先完成“列出设备”和“本机回环”两个步骤，再做跨机器通话。

## 1. 准备环境

### Windows

```powershell
py -3 --version
py -3 -m pip install -r .\requirements.txt
```

如果安装 `pyaudio` 失败，可以先确认 Python 版本和 pip 是否正常，再重新安装依赖。

### Linux / WSL

```bash
sudo apt-get update
sudo apt-get install -y python3-dev portaudio19-dev

python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

WSL 下音频依赖 WSLg / PulseAudio。如果系统没有可用音频设备，程序无法打开麦克风或扬声器。

## 2. 查看音频设备

```powershell
python voice_call.py --list-devices
```

输出中需要重点看三点：

- 是否存在输入设备
- 是否存在输出设备
- 默认设备是不是当前真正使用的麦克风和扬声器

如果默认设备不正确，可以记录设备编号，然后用 `--input-device` 和 `--output-device` 手动指定。

## 3. 本机回环测试

先打开第一个终端，启动服务端：

```powershell
python voice_call.py --mode server --port 5000
```

再打开第二个终端，启动客户端：

```powershell
python voice_call.py --mode client --host 127.0.0.1 --port 5000
```

正常情况下，双方会显示连接成功，状态栏中的上传和下载速率会变化，麦克风音量条也会随说话变化。

## 4. 局域网通话

服务端：

```powershell
python voice_call.py --mode server --port 5000
```

客户端：

```powershell
python voice_call.py --mode client --host <服务端IP> --port 5000
```

服务端 IP 可以通过以下方式查看：

Windows：

```powershell
ipconfig
```

Linux / WSL：

```bash
ip addr
```

如果连接失败，优先检查服务端是否已经启动、防火墙是否放行端口、客户端填写的 IP 是否正确。

## 5. 加密通话

服务端：

```powershell
python voice_call.py --mode server --port 5000 --encrypt --password test123
```

客户端：

```powershell
python voice_call.py --mode client --host <服务端IP> --port 5000 --encrypt --password test123
```

双方的密码必须完全一致。加密开关也要一致，否则可能无法正常解密音频数据。

## 6. 手动指定设备

先列出设备：

```powershell
python voice_call.py --list-devices
```

然后按编号启动：

```powershell
python voice_call.py --mode server --port 5000 --input-device 0 --output-device 2
```

客户端也可以同样指定：

```powershell
python voice_call.py --mode client --host 127.0.0.1 --port 5000 --input-device 0 --output-device 2
```

## 7. 与旧版脚本互通

如果需要与旧版单文件脚本互通，需要匹配旧版默认音频参数：

```powershell
python voice_call.py --mode client --host <IP> --port 5000 --rate 44100 --channels 2
```

或者：

```powershell
python voice_call.py --mode server --port 5000 --rate 44100 --channels 2
```

## 8. 参数说明

| 参数 | 说明 |
| --- | --- |
| `--mode server` | 以服务端模式运行，等待连接 |
| `--mode client` | 以客户端模式运行，连接服务端 |
| `--host` | 客户端要连接的服务端地址 |
| `--port` | TCP 端口，默认 `5000` |
| `--password` | 共享密码 |
| `--encrypt` | 启用 Fernet 加密，需要密码 |
| `--rate` | 采样率，默认 `48000` |
| `--channels` | 声道数，默认 `1` |
| `--chunk` | 每个音频块的帧数，默认 `1024` |
| `--input-device` | 输入设备编号 |
| `--output-device` | 输出设备编号 |
| `--list-devices` | 列出音频设备后退出 |

## 9. 常见问题

### 无法导入 `pyaudio`

Linux / WSL 先安装系统依赖：

```bash
sudo apt-get install -y portaudio19-dev python3-dev
pip install pyaudio
```

Windows 下可以尝试升级 pip 后重新安装：

```powershell
py -3 -m pip install -U pip
py -3 -m pip install -r .\requirements.txt
```

### 能连接但没有声音

检查：

- 麦克风是否被系统禁用
- 程序是否选错输入设备
- 扬声器是否静音
- `--rate` 和 `--channels` 是否两端一致
- 状态栏上传和下载速率是否大于 0

### WSL 输出 ALSA/JACK 警告

WSL 下设备探测可能打印较多日志。只要音频设备能打开、上传下载速率正常，一般不影响通话。

### Connection refused

通常是以下原因：

- 服务端没有启动
- 端口填写错误
- 防火墙阻止连接
- 客户端填写的 IP 不正确

### 认证失败

检查双方 `--password` 是否完全一致，包括大小写和空格。

### 加密失败

确认双方都同时使用了 `--encrypt --password <密码>`。只启用一端加密会导致数据格式不一致。
