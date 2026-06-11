# 架构说明

## 项目目标

将单文件 TCP 语音通话脚本重构为模块化结构，保持通话模型不变的同时提高可读性和可维护性。

## 运行时流程

1. 服务端进程打开 TCP 监听 socket
2. 客户端进程连接到该 socket
3. 如配置了密码，双方进行基于哈希的认证握手
4. 如同时指定 `--encrypt` 和 `--password`，服务端生成 salt 发给客户端，双方派生 Fernet 密钥
5. 双方各自打开音频输入流和输出流
6. 发送线程：录制麦克风 → 加密 → 4 字节长度前缀 + 数据 → 发送
7. 接收线程：接收 → 解密 → 播放
8. 状态线程：实时显示码率、时长、麦克风音量

## 模块职责

### `voice_call.py`
- 兼容性入口，调用 `voice_call_app.cli.main()`

### `voice_call_app/cli.py`
- 解析命令行参数
- 构建运行时配置
- 启动服务端或客户端模式

### `voice_call_app/config.py`
- 定义 `VoiceCallConfig` 数据类，所有运行时配置的单一来源

### `voice_call_app/console.py`
- ANSI 颜色和终端格式化工具

### `voice_call_app/windows.py`
- Windows 终端 UTF-8 编码设置

### `voice_call_app/crypto.py`
- 密码哈希与认证握手
- Fernet 密钥派生和加解密

### `voice_call_app/audio.py`
- PyAudio 生命周期管理
- 输入/输出流创建
- 音频设备枚举与自动选择
- 麦克风音量计算

### `voice_call_app/stats.py`
- 运行时计数器
- 音量条格式化

### `voice_call_app/engine.py`
- 核心运行时：socket 管理、认证、加密、音频线程协调
- 服务端/客户端主循环
- 实时状态栏渲染

## 数据封包格式

每个音频包结构：

```
[4 字节 网络字节序长度] [负载数据（可选加密）]
```

PCM 格式固定为 16-bit 有符号整数 (`paInt16`)。

## 安全模型

轻量级安全设计：

- 密码认证：双方通过 SHA-256 哈希验证共享密钥
- 加密：使用 PBKDF2 从密码派生 Fernet 密钥，结合服务端随机 salt
- 无密码时跳过认证和加密

适用于个人项目、教学演示和内部实验，不包含身份管理、证书校验或复杂密钥交换。
