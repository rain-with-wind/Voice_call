# Voice Call Refactored

## English

`Voice Call Refactored` is a cleaned-up multi-file version of a direct TCP
voice call script.

It keeps the original model:

- one side runs as a TCP server
- the other side connects as a TCP client
- audio is captured and played with PyAudio
- an optional shared password enables authentication
- optional Fernet encryption can be enabled when a password is provided

This repository is designed to be easier to read, maintain, test, and publish
than the original single-file script.

## Features

- Direct TCP duplex voice call
- Optional password-based authentication
- Optional symmetric encryption using `cryptography`
- Modular package layout
- Windows console UTF-8 helper
- Practical WSL troubleshooting probes

## Tested Status

The current code has been tested in the following environments:

- Windows PowerShell with `py -3` on Python `3.13.5`
- WSL Ubuntu with
  `/mnt/d/QQ/Downloads/Voice_call/Voice_call/.venv/bin/python3` on Python
  `3.12.3`
- Windows local loopback: server and client both work
- WSL local loopback: server and client both work
- Cross-system:
  - WSL server -> Windows client: works
  - Windows server -> WSL client: works

Observed behavior during testing:

- audio input and output both opened successfully on Windows
- audio input and output both opened successfully in WSL through Pulse/WSLg
- WSL still prints a large amount of ALSA/JACK noise during device probing, but
  the call itself works

## Compatibility With the Old Single-File Script

The current refactored version can talk to the old single-file script, but you
must match the old audio defaults.

Old script defaults:

- `--rate 44100`
- `--channels 2`
- `--chunk 1024`

The refactored version defaults to `48000` and `1` channel, so when talking to
the old script you should start the refactored side with:

```powershell
py -3 voice_call.py --mode client --host PEER_IP --port 5000 --rate 44100 --channels 2
```

or:

```powershell
py -3 voice_call.py --mode server --port 5000 --rate 44100 --channels 2
```

If password or encryption is enabled, both sides must use the same
`--password` and the same `--encrypt` setting.

Note that in the current code, encryption is derived from the shared password.
Using `--encrypt` without `--password` does not create a Fernet key.

## Requirements

- Python 3.10+
- `pyaudio`
- `cryptography`
- A working microphone and speaker output

On Linux you often need system audio development packages before installing
`pyaudio`, for example:

```bash
sudo apt-get update
sudo apt-get install -y python3-dev portaudio19-dev
```

## Installation

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

## Quick Start

Windows PowerShell server:

```powershell
py -3 voice_call.py --mode server --port 5000
```

Windows PowerShell client:

```powershell
py -3 voice_call.py --mode client --host 192.168.1.100 --port 5000
```

WSL server using the existing project venv:

```bash
cd /mnt/d/QQ/Downloads/Voice_call/Voice_call_refactored
/mnt/d/QQ/Downloads/Voice_call/Voice_call/.venv/bin/python3 voice_call.py --mode server --port 5000
```

WSL client using the existing project venv:

```bash
cd /mnt/d/QQ/Downloads/Voice_call/Voice_call_refactored
/mnt/d/QQ/Downloads/Voice_call/Voice_call/.venv/bin/python3 voice_call.py --mode client --host 192.168.1.100 --port 5000
```

Secure call example:

```powershell
py -3 voice_call.py --mode server --port 5000 --encrypt --password mypassword
py -3 voice_call.py --mode client --host 192.168.1.100 --port 5000 --encrypt --password mypassword
```

## Project Layout

```text
Voice_call_refactored/
|- docs/
|  |- ARCHITECTURE.md
|  |- DEVELOPMENT.md
|  |- TESTING.md
|  `- USAGE.md
|- tools/
|- voice_call_app/
|- requirements.txt
`- voice_call.py
```

## Documentation

- Architecture overview: [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)
- Usage guide: [docs/USAGE.md](./docs/USAGE.md)
- Development notes: [docs/DEVELOPMENT.md](./docs/DEVELOPMENT.md)
- Testing notes: [docs/TESTING.md](./docs/TESTING.md)

## Limitations

- This is a raw TCP audio tool, not a WebRTC system.
- NAT traversal is not built in.
- WSL audio depends on the host WSLg / Pulse setup.
- There is no room or multi-party call system.
- The server bind address is fixed in code to `0.0.0.0`.
- Audio format is fixed to 16-bit PCM. Only rate, channels, and chunk are
  configurable from the CLI.
- There is no CLI flag for manual input/output device selection.

## License

This project is released under the MIT License.

---

## 中文

`Voice Call Refactored` 是一个把“单文件 TCP 语音通话脚本”拆成多文件后的整理版本。

它保留了原始工作方式：

- 一端作为 TCP 服务端监听
- 另一端作为 TCP 客户端连接
- 使用 PyAudio 采集和播放音频
- 可选共享密码认证
- 只有在提供密码时才真正启用基于密码派生的 Fernet 加密

这个仓库的目标是比原始单文件版本更容易阅读、维护、测试和开源发布。

## 功能

- 直接基于 TCP 的双向语音通话
- 可选的基于密码认证
- 使用 `cryptography` 的可选对称加密
- 更清晰的模块化结构
- Windows 终端 UTF-8 兼容处理
- 面向 WSL 的排查脚本

## 已测试状态

当前代码已经在以下环境中完成验证：

- Windows PowerShell，使用 `py -3`，Python 版本为 `3.13.5`
- WSL Ubuntu，使用
  `/mnt/d/QQ/Downloads/Voice_call/Voice_call/.venv/bin/python3`，Python 版本为
  `3.12.3`
- Windows 本机回环：服务端和客户端都可运行
- WSL 本机回环：服务端和客户端都可运行
- 跨系统互通：
  - WSL 服务端 -> Windows 客户端：可用
  - Windows 服务端 -> WSL 客户端：可用

测试时观察到的现象：

- Windows 端可以正常打开输入和输出设备
- WSL 端通过 Pulse/WSLg 也可以正常打开输入和输出设备
- WSL 在探测音频设备时仍会打印大量 ALSA/JACK 噪声日志，但不影响实际通话

## 与旧版单文件脚本的兼容性

当前重构版可以和旧版单文件脚本互通，但必须把音频参数对齐到旧版默认值。

旧版默认参数为：

- `--rate 44100`
- `--channels 2`
- `--chunk 1024`

而当前重构版默认是 `48000` 采样率和 `1` 声道，所以当你要和旧版互通时，重构版必须这样启动：

```powershell
py -3 voice_call.py --mode client --host 对方IP --port 5000 --rate 44100 --channels 2
```

或者：

```powershell
py -3 voice_call.py --mode server --port 5000 --rate 44100 --channels 2
```

如果启用了密码或加密，则双方的 `--password` 和 `--encrypt` 必须完全一致。

需要特别注意，当前代码里的加密密钥是从共享密码派生出来的，所以单独传
`--encrypt` 而不传 `--password`，不会真正建立 Fernet 密钥。

## 依赖要求

- Python 3.10 及以上
- `pyaudio`
- `cryptography`
- 可用的麦克风和扬声器输出

在 Linux 上安装 `pyaudio` 前通常需要先安装系统级音频开发包，例如：

```bash
sudo apt-get update
sudo apt-get install -y python3-dev portaudio19-dev
```

## 安装

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

## 快速开始

Windows PowerShell 服务端：

```powershell
py -3 voice_call.py --mode server --port 5000
```

Windows PowerShell 客户端：

```powershell
py -3 voice_call.py --mode client --host 192.168.1.100 --port 5000
```

WSL 服务端，使用现有项目虚拟环境：

```bash
cd /mnt/d/QQ/Downloads/Voice_call/Voice_call_refactored
/mnt/d/QQ/Downloads/Voice_call/Voice_call/.venv/bin/python3 voice_call.py --mode server --port 5000
```

WSL 客户端，使用现有项目虚拟环境：

```bash
cd /mnt/d/QQ/Downloads/Voice_call/Voice_call_refactored
/mnt/d/QQ/Downloads/Voice_call/Voice_call/.venv/bin/python3 voice_call.py --mode client --host 192.168.1.100 --port 5000
```

加密通话示例：

```powershell
py -3 voice_call.py --mode server --port 5000 --encrypt --password mypassword
py -3 voice_call.py --mode client --host 192.168.1.100 --port 5000 --encrypt --password mypassword
```

## 项目结构

```text
Voice_call_refactored/
|- docs/
|  |- ARCHITECTURE.md
|  |- DEVELOPMENT.md
|  |- TESTING.md
|  `- USAGE.md
|- tools/
|- voice_call_app/
|- requirements.txt
`- voice_call.py
```

## 文档

- 架构说明：[docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)
- 使用说明：[docs/USAGE.md](./docs/USAGE.md)
- 开发说明：[docs/DEVELOPMENT.md](./docs/DEVELOPMENT.md)
- 测试说明：[docs/TESTING.md](./docs/TESTING.md)

## 当前限制

- 这是一个原始 TCP 音频工具，不是 WebRTC 系统
- 没有内建 NAT 穿透
- WSL 音频依赖宿主机的 WSLg / Pulse 配置
- 没有房间系统，也不支持多人通话
- 服务端绑定地址在代码里固定为 `0.0.0.0`
- 音频格式固定为 16-bit PCM，CLI 只能调 `rate`、`channels` 和 `chunk`
- 当前没有用于手动选择输入/输出设备的 CLI 参数

## 许可证

本项目使用 MIT License。
