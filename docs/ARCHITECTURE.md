# Architecture

## English

## Goal

This project refactors a monolithic direct TCP voice-call script into smaller,
focused modules without changing the basic call model.

## Runtime Flow

1. The server process opens a listening TCP socket.
2. The client process connects to that socket.
3. If a password is configured, both sides perform a hash-based
   authentication handshake.
4. If both `--encrypt` and `--password` are used, the server generates a salt,
   sends it to the client, and both sides derive the same Fernet key.
5. Each side opens one audio input stream and one audio output stream.
6. One worker thread records microphone audio and sends framed binary packets.
7. One worker thread receives framed binary packets and plays them back.
8. A status thread displays bitrate, duration, and microphone activity.

## Module Responsibilities

### `voice_call.py`

- Thin compatibility entrypoint
- Calls `voice_call_app.cli.main()`

### `voice_call_app/cli.py`

- Parses command-line arguments
- Builds runtime configuration
- Starts server or client mode

### `voice_call_app/config.py`

- Defines the typed configuration object used by the runtime

### `voice_call_app/console.py`

- Centralizes ANSI color helpers and banners

### `voice_call_app/windows.py`

- Applies Windows console UTF-8 tuning when possible

### `voice_call_app/crypto.py`

- Handles password hashing
- Performs the authentication handshake
- Manages Fernet key derivation and encryption/decryption

### `voice_call_app/audio.py`

- Owns the PyAudio lifecycle
- Starts input/output streams
- Chooses practical default devices automatically
- Computes microphone activity level

### `voice_call_app/stats.py`

- Stores counters and formats the volume bar shown in the terminal

### `voice_call_app/engine.py`

- Coordinates sockets, authentication, encryption, audio, and worker threads
- Contains the main server/client runtime behavior

## Data Framing

Each outbound audio payload is sent as:

1. a 4-byte network-order unsigned length prefix
2. the raw PCM frame bytes, optionally encrypted

This keeps stream parsing deterministic for both sides.

The PCM format used by the current code is fixed to 16-bit signed audio
(`paInt16`).

## Security Model

Security is intentionally lightweight:

- password authentication proves both sides know the shared secret
- encryption uses a Fernet key derived from the password and a server-issued
  salt
- if no password is provided, authentication is skipped and no Fernet key is
  derived

This is useful for hobby, teaching, and internal experiments, but it is not a
complete secure calling stack with identity management or advanced key
exchange.

---

## 中文

## 目标

这个项目把原本单文件的 TCP 语音通话脚本拆成更小、更明确的模块，同时尽量不改变原始通话模型。

## 运行流程

1. 服务端进程先打开一个监听中的 TCP socket。
2. 客户端进程连接到这个 socket。
3. 如果配置了密码，双方会进行一次基于哈希的认证握手。
4. 只有在同时使用 `--encrypt` 和 `--password` 时，服务端才会生成 salt 发给客户端，双方据此派生出同一个 Fernet 密钥。
5. 双方各自打开一个音频输入流和一个音频输出流。
6. 一个工作线程负责录制麦克风并发送二进制音频包。
7. 一个工作线程负责接收二进制音频包并播放。
8. 一个状态线程负责显示码率、通话时长和麦克风活动。

## 模块职责

### `voice_call.py`

- 兼容性入口文件
- 调用 `voice_call_app.cli.main()`

### `voice_call_app/cli.py`

- 解析命令行参数
- 构建运行时配置
- 启动服务端或客户端模式

### `voice_call_app/config.py`

- 定义运行时使用的配置对象

### `voice_call_app/console.py`

- 统一 ANSI 颜色和横幅输出

### `voice_call_app/windows.py`

- 在可能的情况下处理 Windows 终端 UTF-8 设置

### `voice_call_app/crypto.py`

- 处理密码哈希
- 执行认证握手
- 管理 Fernet 密钥派生与加解密

### `voice_call_app/audio.py`

- 管理 PyAudio 生命周期
- 启动输入/输出音频流
- 自动选择较实用的默认音频设备
- 计算麦克风活动音量

### `voice_call_app/stats.py`

- 保存统计计数器
- 格式化终端里显示的音量条

### `voice_call_app/engine.py`

- 负责协调 socket、认证、加密、音频和工作线程
- 包含服务端/客户端的主要运行逻辑

## 数据封包格式

每个发送出去的音频负载由两部分组成：

1. 4 字节网络字节序无符号长度前缀
2. 原始 PCM 音频帧数据，可选加密

这样可以让双方的流解析更稳定、更直接。

当前代码使用的 PCM 格式固定为 16-bit 有符号音频，也就是 `paInt16`。

## 安全模型

这个项目的安全机制是轻量级的：

- 密码认证用于确认双方知道同一个共享密钥
- 加密使用基于密码和服务端 salt 派生出来的 Fernet 密钥
- 如果没有提供密码，则会跳过认证，也不会派生 Fernet 密钥

它适合个人项目、教学演示和内部实验，但不是一个完整的安全通话系统，不包含身份管理、证书校验或更复杂的密钥交换机制。
