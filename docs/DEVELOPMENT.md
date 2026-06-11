# Development Notes

## English

## Refactoring Goals

This refactor focuses on readability and maintainability rather than feature
expansion.

Main goals:

- separate responsibilities by file
- reduce the size of the main runtime class
- make security, audio, and CLI parsing easier to inspect
- make the project easier to document and publish

## Suggested Local Checks

Windows PowerShell:

```powershell
py -3 -m compileall .\voice_call.py .\voice_call_app .\tools
```

WSL:

```bash
cd /mnt/d/QQ/Downloads/Voice_call/Voice_call_refactored
/mnt/d/QQ/Downloads/Voice_call/Voice_call/.venv/bin/python3 -m compileall voice_call.py voice_call_app tools
```

## Recommended Manual Checks

- verify `voice_call.py --help`
- verify audio input and output can both be opened
- verify local loopback server/client
- verify cross-system Windows <-> WSL behavior when relevant
- verify old-script compatibility with `--rate 44100 --channels 2`

## Notes About Windows and WSL

- On Windows, the project has been validated with `py -3`.
- On WSL, the current validated path is
  `/mnt/d/QQ/Downloads/Voice_call/Voice_call/.venv/bin/python3`.
- WSL audio may print ALSA/JACK noise during probing; this does not
  automatically mean the call failed.
- Python 3.10+ is currently required by the present codebase.

## Future Improvements

- add automated tests for packet framing and authentication
- add structured logging instead of print-heavy runtime output
- add device listing and explicit device selection
- make volume bar output more encoding-safe for redirected Windows logs
- add a compatibility preset for the old single-file script
- optionally package the tool with `pyproject.toml`

---

## 中文

## 重构目标

这次重构主要关注可读性和可维护性，而不是扩展新功能。

主要目标：

- 按职责拆分文件
- 缩小主运行时类的体积
- 让安全、音频和命令行解析逻辑更容易检查
- 让项目更容易写文档和开源发布

## 建议的本地检查

Windows PowerShell：

```powershell
py -3 -m compileall .\voice_call.py .\voice_call_app .\tools
```

WSL：

```bash
cd /mnt/d/QQ/Downloads/Voice_call/Voice_call_refactored
/mnt/d/QQ/Downloads/Voice_call/Voice_call/.venv/bin/python3 -m compileall voice_call.py voice_call_app tools
```

## 建议的手工验证

- 验证 `voice_call.py --help`
- 验证音频输入和输出都能打开
- 验证本机回环 server/client
- 在需要时验证 Windows <-> WSL 跨系统行为
- 使用 `--rate 44100 --channels 2` 验证与旧版单文件的兼容性

## 关于 Windows 和 WSL 的说明

- Windows 端目前已经用 `py -3` 验证过。
- WSL 端当前已经验证可用的路径是
  `/mnt/d/QQ/Downloads/Voice_call/Voice_call/.venv/bin/python3`。
- WSL 探测音频设备时会打印大量 ALSA/JACK 噪声，这不自动等于通话失败。

## 后续可改进项

- 为封包和认证补自动化测试
- 用结构化日志替代大量 `print`
- 增加设备列表和显式设备选择
- 让音量条在 Windows 重定向日志时更安全地处理编码
- 增加面向旧版单文件的兼容预设
- 视需要增加 `pyproject.toml` 打包配置
- 如果需要支持 Python 3.9，需要单独调整类型标注和 dataclass 用法
