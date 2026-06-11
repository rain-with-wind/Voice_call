# Usage Guide

## English

## 1. Install Dependencies

Windows PowerShell:

```powershell
py -3 -m pip install -r .\requirements.txt
```

WSL or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

## 2. Start the Server Side

Windows PowerShell:

```powershell
py -3 voice_call.py --mode server --port 5000
```

WSL with the existing project venv:

```bash
cd /mnt/d/QQ/Downloads/Voice_call/Voice_call_refactored
/mnt/d/QQ/Downloads/Voice_call/Voice_call/.venv/bin/python3 voice_call.py --mode server --port 5000
```

Optional secure mode:

```powershell
py -3 voice_call.py --mode server --port 5000 --encrypt --password mypassword
```

## 3. Start the Client Side

Windows PowerShell:

```powershell
py -3 voice_call.py --mode client --host 192.168.1.100 --port 5000
```

WSL with the existing project venv:

```bash
cd /mnt/d/QQ/Downloads/Voice_call/Voice_call_refactored
/mnt/d/QQ/Downloads/Voice_call/Voice_call/.venv/bin/python3 voice_call.py --mode client --host 192.168.1.100 --port 5000
```

Optional secure mode:

```powershell
py -3 voice_call.py --mode client --host 192.168.1.100 --port 5000 --encrypt --password mypassword
```

## 4. Useful Flags

- `--port`: TCP port number
- `--host`: server address in client mode
- `--password`: shared password
- `--encrypt`: request Fernet encryption derived from the shared password
- `--rate`: sample rate, default `48000`
- `--channels`: channel count, default `1`
- `--chunk`: audio chunk size, default `1024`

Current behavior notes:

- `--password` is optional
- if `--password` is omitted, authentication is skipped
- `--encrypt` is intended to be used together with `--password`
- the server bind address is fixed in code to `0.0.0.0`

## 5. Talking to the Old Single-File Script

When the peer uses the old single-file script, start the refactored side with:

```powershell
py -3 voice_call.py --mode client --host PEER_IP --port 5000 --rate 44100 --channels 2
```

or:

```powershell
py -3 voice_call.py --mode server --port 5000 --rate 44100 --channels 2
```

This is required because the old script defaults to `44100Hz`, `2` channels,
and `1024` chunk size.

## 6. Cross-System Notes

Validated combinations:

- Windows PowerShell server <-> Windows PowerShell client
- WSL server <-> WSL client
- WSL server <-> Windows PowerShell client
- Windows PowerShell server <-> WSL client

## 7. Common Problems

### Cannot import `pyaudio`

Install the project requirements again, and on Linux install the system audio
development packages first.

### Cannot import `cryptography`

Run:

```powershell
py -3 -m pip install -r .\requirements.txt
```

### WSL prints ALSA or JACK warnings

That is common under WSL. If the call still shows:

- `output_device=pulse`
- `input_device=pulse`
- active `UP` and `DOWN` traffic

then the call path is usually working.

### Connection refused

Check:

- the server is running
- the port is correct
- the firewall allows the connection
- the host IP address is reachable

---

## 中文

## 1. 安装依赖

Windows PowerShell：

```powershell
py -3 -m pip install -r .\requirements.txt
```

WSL 或 Linux：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

## 2. 启动服务端

Windows PowerShell：

```powershell
py -3 voice_call.py --mode server --port 5000
```

WSL，使用现有项目虚拟环境：

```bash
cd /mnt/d/QQ/Downloads/Voice_call/Voice_call_refactored
/mnt/d/QQ/Downloads/Voice_call/Voice_call/.venv/bin/python3 voice_call.py --mode server --port 5000
```

可选加密模式：

```powershell
py -3 voice_call.py --mode server --port 5000 --encrypt --password mypassword
```

## 3. 启动客户端

Windows PowerShell：

```powershell
py -3 voice_call.py --mode client --host 192.168.1.100 --port 5000
```

WSL，使用现有项目虚拟环境：

```bash
cd /mnt/d/QQ/Downloads/Voice_call/Voice_call_refactored
/mnt/d/QQ/Downloads/Voice_call/Voice_call/.venv/bin/python3 voice_call.py --mode client --host 192.168.1.100 --port 5000
```

可选加密模式：

```powershell
py -3 voice_call.py --mode client --host 192.168.1.100 --port 5000 --encrypt --password mypassword
```

## 4. 常用参数

- `--port`：TCP 端口
- `--host`：客户端模式下的服务端地址
- `--password`：共享密码
- `--encrypt`：请求启用基于共享密码派生的 Fernet 加密
- `--rate`：采样率，默认 `48000`
- `--channels`：声道数，默认 `1`
- `--chunk`：音频分块大小，默认 `1024`

当前行为说明：

- `--password` 是可选的
- 如果不传 `--password`，则会跳过认证
- `--encrypt` 设计上应当和 `--password` 一起使用
- 服务端绑定地址在代码里固定为 `0.0.0.0`

## 5. 与旧版单文件互通

如果对方使用旧版单文件脚本，重构版必须这样启动：

```powershell
py -3 voice_call.py --mode client --host 对方IP --port 5000 --rate 44100 --channels 2
```

或者：

```powershell
py -3 voice_call.py --mode server --port 5000 --rate 44100 --channels 2
```

这是因为旧版默认就是 `44100Hz`、`2` 声道、`1024` chunk。

## 6. 跨系统说明

当前已经验证过以下组合：

- Windows PowerShell 服务端 <-> Windows PowerShell 客户端
- WSL 服务端 <-> WSL 客户端
- WSL 服务端 <-> Windows PowerShell 客户端
- Windows PowerShell 服务端 <-> WSL 客户端

## 7. 常见问题

### 无法导入 `pyaudio`

重新安装项目依赖；在 Linux 上还需要先装系统级音频开发包。

### 无法导入 `cryptography`

执行：

```powershell
py -3 -m pip install -r .\requirements.txt
```

### WSL 打印大量 ALSA 或 JACK 警告

这在 WSL 里很常见。如果通话过程中仍能看到：

- `output_device=pulse`
- `input_device=pulse`
- `UP` 和 `DOWN` 数据持续变化

通常说明实际通话链路是正常的。

### Connection refused

请检查：

- 服务端是否已经启动
- 端口是否正确
- 防火墙是否允许连接
- 主机 IP 是否可达
