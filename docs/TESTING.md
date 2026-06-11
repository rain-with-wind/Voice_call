# 测试说明

## 测试环境

| 平台 | Python 版本 | 状态 |
|------|-------------|------|
| Windows PowerShell | 3.13.5 | 通过 |
| WSL Ubuntu | 3.12.3 | 通过 |
| Linux | 3.10+ | 通过 |

## 音频设备测试

```powershell
# 列出所有设备
python voice_call.py --list-devices
```

检查项：
- 输入设备（麦克风）存在且通道数 > 0
- 输出设备（扬声器）存在且通道数 > 0

## 端到端通话测试

### 本机回环

终端 1：
```powershell
python voice_call.py --mode server --port 5000
```

终端 2：
```powershell
python voice_call.py --mode client --host 127.0.0.1 --port 5000
```

验证：
- 双方显示 `[连接]` 成功
- `上传` 和 `下载` 速率 > 0
- 麦克风音量条随说话变化
- Ctrl+C 正常退出

### 跨机器

服务端：
```powershell
python voice_call.py --mode server --port 5000
```

客户端：
```powershell
python voice_call.py --mode client --host <服务端IP> --port 5000
```

### 加密模式

双方都加 `--encrypt --password test123`，验证能正常通话。

## 兼容性测试

如需与旧版单文件脚本互通，匹配参数：

```powershell
python voice_call.py --mode client --host <IP> --port 5000 --rate 44100 --channels 2
```

## 已知现象

- WSL 音频初始化时会打印 ALSA/JACK 探测日志（stderr），不影响通话
- 强制结束进程时出现 "对方已断开连接" 属正常
- Windows 上将输出重定向到文件时，音量条可能显示异常字符
