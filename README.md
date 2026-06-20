# Voice_call

- 作者：魏云龙 2024302121012；占曜宇 2024302061113
- 所属课程：武汉大学开源软件与技术课程 2026

一个基于 Python 的 TCP 双向语音通话项目。项目支持一端作为服务端监听，另一端作为客户端连接，连接建立后通过 PyAudio 采集和播放 16-bit PCM 音频数据。仓库根目录只保留运行入口和必要项目文件，详细说明统一放在 `docs/` 目录中，便于查看和维护。

## 项目简介

本项目的主要目标是实现一个可以在本机、局域网、Windows 与 WSL 环境中运行的简易语音通话工具。它不是完整的会议系统，也不包含 NAT 穿透、账号体系或房间管理，而是聚焦在最核心的点对点音频链路上：

- 服务端通过 TCP socket 等待客户端连接
- 客户端连接服务端 IP 和端口
- 双方分别启动麦克风采集线程和扬声器播放线程
- 音频数据按“长度前缀 + 数据负载”的格式发送
- 可选使用共享密码进行认证
- 可选基于密码派生 Fernet 密钥进行加密

## 功能特点

- 支持 `server` 和 `client` 两种运行模式
- 支持 Windows、Linux、WSL 等常见环境
- 支持本机回环和局域网点对点通话
- 支持列出音频设备并手动指定输入/输出设备
- 支持共享密码认证
- 支持可选的 Fernet 对称加密
- 支持实时显示通话时长、上传速率、下载速率和麦克风音量
- 提供 WSL 音频、socket 和回环测试脚本，方便排查环境问题

## 环境要求

- Python 3.10+
- 可用的麦克风和扬声器
- Python 依赖：
  - `pyaudio==0.2.14`
  - `cryptography==41.0.7`

Linux / WSL 下安装 `pyaudio` 前通常需要系统音频开发库：

```bash
sudo apt-get update
sudo apt-get install -y python3-dev portaudio19-dev
```

## 安装方法

Windows PowerShell：

```powershell
py -3 -m pip install -r .\requirements.txt
```

Linux / WSL：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

## 快速开始

先在一台机器上启动服务端：

```powershell
python voice_call.py --mode server --port 5000
```

再在另一台机器上启动客户端：

```powershell
python voice_call.py --mode client --host 192.168.1.100 --port 5000
```

如果只在本机测试，可以把客户端地址写成 `127.0.0.1`：

```powershell
python voice_call.py --mode client --host 127.0.0.1 --port 5000
```

## 加密通话

加密模式需要双方同时指定相同密码：

```powershell
python voice_call.py --mode server --port 5000 --encrypt --password test123
python voice_call.py --mode client --host 127.0.0.1 --port 5000 --encrypt --password test123
```

如果只写 `--encrypt` 而没有提供 `--password`，程序不会生成 Fernet 密钥，实际仍然是普通传输。因此安全模式下必须同时使用 `--encrypt` 和 `--password`。

## 音频设备

列出当前系统中的音频设备：

```powershell
python voice_call.py --list-devices
```

手动指定麦克风和扬声器：

```powershell
python voice_call.py --mode server --port 5000 --input-device 0 --output-device 2
```

如果出现没有声音、麦克风无输入、设备打开失败等问题，优先检查 `--list-devices` 的输出，并确认选中的设备支持对应的输入或输出通道。

## 常用参数

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--mode` | 必填 | `server` 表示服务端，`client` 表示客户端 |
| `--host` | `127.0.0.1` | 客户端连接的服务端地址 |
| `--port` | `5000` | TCP 端口 |
| `--password` | 无 | 共享密码，用于认证 |
| `--encrypt` | 关闭 | 启用 Fernet 加密，需要同时指定密码 |
| `--rate` | `48000` | 音频采样率 |
| `--channels` | `1` | 声道数 |
| `--chunk` | `1024` | 每次采集和发送的音频帧大小 |
| `--input-device` | 自动选择 | 手动指定输入设备编号 |
| `--output-device` | 自动选择 | 手动指定输出设备编号 |
| `--list-devices` | 关闭 | 只列出音频设备后退出 |

## 项目结构

```text
Voice_call/
├── docs/
│   ├── ARCHITECTURE.md        # 架构说明
│   ├── CHANGELOG.md           # 变更记录
│   ├── CODE_OF_CONDUCT.md     # 行为准则
│   ├── CONTRIBUTING.md        # 贡献说明
│   ├── DEVELOPMENT.md         # 开发说明
│   ├── EXPERIMENT_REPORT.md   # 实验报告
│   ├── SECURITY.md            # 安全说明
│   ├── TESTING.md             # 测试说明
│   └── USAGE.md               # 使用说明
├── tools/
│   ├── wsl_audio_probe.py
│   ├── wsl_loopback_call_test.py
│   └── wsl_subprocess_socket_probe.py
├── voice_call_app/
│   ├── audio.py               # 音频设备与流管理
│   ├── cli.py                 # 命令行参数
│   ├── config.py              # 配置数据类
│   ├── console.py             # 终端输出工具
│   ├── crypto.py              # 认证与加密
│   ├── engine.py              # 通话主流程
│   ├── stats.py               # 运行统计
│   └── windows.py             # Windows 终端兼容处理
├── voice_call.py              # 程序入口
├── requirements.txt
└── LICENSE
```

## 文档导航

- [使用说明](./docs/USAGE.md)：安装、启动、参数和常见问题
- [架构说明](./docs/ARCHITECTURE.md)：模块职责、运行流程和数据格式
- [测试说明](./docs/TESTING.md)：本机、跨系统、加密和异常场景测试
- [开发说明](./docs/DEVELOPMENT.md)：开发环境、代码规范和修改流程
- [实验报告](./docs/EXPERIMENT_REPORT.md)：项目背景、设计实现、测试结果和总结
- [贡献指南](./docs/CONTRIBUTING.md)：Issue、分支、提交和 Pull Request 规范
- [安全策略](./docs/SECURITY.md)：安全模型、局限和漏洞反馈方式
- [行为准则](./docs/CODE_OF_CONDUCT.md)：协作沟通的基本规则
- [变更记录](./docs/CHANGELOG.md)：项目主要改动记录

## 测试方式

编译检查：

```powershell
python -m compileall voice_call.py voice_call_app tools
```

本机回环测试：

```powershell
python voice_call.py --mode server --port 5000
python voice_call.py --mode client --host 127.0.0.1 --port 5000
```

加密模式测试：

```powershell
python voice_call.py --mode server --port 5000 --encrypt --password test123
python voice_call.py --mode client --host 127.0.0.1 --port 5000 --encrypt --password test123
```

## 当前限制

- 只支持一对一通话，不支持多人房间
- 不包含 NAT 穿透，跨公网使用需要自行配置网络
- 不提供账号体系和证书校验
- 音频编码固定为 16-bit PCM，未做压缩编码
- 命令行密码可能被系统进程列表看到，安全性要求较高的场景不建议直接使用
- WSL 音频依赖 WSLg / PulseAudio 环境，部分机器可能需要手动排查设备

## 许可证

本项目使用 MIT License，详见 [LICENSE](./LICENSE)。
