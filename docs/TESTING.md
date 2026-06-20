# 测试说明

本项目测试以手工端到端验证为主，重点确认程序能启动、设备能打开、网络能连接、音频能双向传输、加密模式能正常工作。

## 1. 测试环境

| 环境 | Python | 验证内容 |
| --- | --- | --- |
| Windows PowerShell | 3.10+ | 安装依赖、设备枚举、本机回环、局域网连接 |
| WSL Ubuntu | 3.10+ | 音频设备探测、本机回环、与 Windows 互通 |
| Linux | 3.10+ | 依赖安装、TCP 连接、音频输入输出 |

## 2. 静态检查

运行 Python 编译检查：

```powershell
python -m compileall voice_call.py voice_call_app tools
```

期望结果：

- 所有 Python 文件可以正常编译
- 无语法错误
- 无导入路径错误

## 3. 命令行检查

```powershell
python voice_call.py --help
```

期望结果：

- 能看到 `--mode`
- 能看到 `--host`
- 能看到 `--port`
- 能看到 `--password`
- 能看到 `--encrypt`
- 能看到音频参数和设备参数

## 4. 音频设备测试

```powershell
python voice_call.py --list-devices
```

检查项：

- 程序可以正常启动并退出
- 输出中有输入设备
- 输出中有输出设备
- 默认输入和默认输出符合当前系统设置

如果默认设备不符合预期，需要记录可用设备编号，并在后续通话中手动指定。

## 5. 本机回环测试

终端 1：

```powershell
python voice_call.py --mode server --port 5000
```

终端 2：

```powershell
python voice_call.py --mode client --host 127.0.0.1 --port 5000
```

通过标准：

- 服务端显示客户端已连接
- 客户端显示已连接到服务器
- 双方显示麦克风和扬声器已启动
- 上传和下载速率有变化
- 麦克风音量条随说话变化
- Ctrl+C 可以正常退出
- 退出时打印通话统计

## 6. 局域网测试

服务端：

```powershell
python voice_call.py --mode server --port 5000
```

客户端：

```powershell
python voice_call.py --mode client --host <服务端IP> --port 5000
```

检查项：

- 客户端能连接服务端
- 双方音频参数一致
- 网络传输速率稳定
- 防火墙没有阻断端口

## 7. 加密模式测试

服务端：

```powershell
python voice_call.py --mode server --port 5000 --encrypt --password test123
```

客户端：

```powershell
python voice_call.py --mode client --host 127.0.0.1 --port 5000 --encrypt --password test123
```

通过标准：

- 双方认证通过
- 双方显示端到端加密已启用
- 通话可以正常进行
- 退出流程正常

异常用例：

| 场景 | 期望结果 |
| --- | --- |
| 双方密码不同 | 认证失败并断开 |
| 一端启用加密另一端不启用 | 无法正常解密，通话失败 |
| 只写 `--encrypt` 不写密码 | 不创建 Fernet 密钥 |

## 8. 设备指定测试

先查看设备：

```powershell
python voice_call.py --list-devices
```

再指定设备：

```powershell
python voice_call.py --mode server --port 5000 --input-device 0 --output-device 2
```

通过标准：

- 输出中显示指定的输入设备名称
- 输出中显示指定的输出设备名称
- 通话时有声音输入和输出

## 9. WSL 排查测试

可使用 `tools/` 中的辅助脚本：

```bash
python tools/wsl_audio_probe.py
python tools/wsl_subprocess_socket_probe.py
python tools/wsl_loopback_call_test.py
```

这些脚本主要用于确认：

- WSL 是否能访问音频设备
- socket 是否能正常创建和连接
- 子进程启动是否正常
- 本机回环链路是否可用

## 10. 回归测试清单

每次修改代码后至少检查：

- [ ] `python -m compileall voice_call.py voice_call_app tools`
- [ ] `python voice_call.py --help`
- [ ] `python voice_call.py --list-devices`
- [ ] 本机回环通话
- [ ] 加密模式通话
- [ ] Ctrl+C 退出
- [ ] README 和相关文档同步更新

## 11. 已知现象

- WSL 下可能出现 ALSA/JACK 探测日志，不一定代表程序失败
- 强制断开时，另一端显示“对方已断开连接”属于正常表现
- 输出重定向到文件时，终端音量条可能不如交互终端清晰
- 网络较差时可能出现音频卡顿，因为当前项目未做抖动缓冲和音频压缩
