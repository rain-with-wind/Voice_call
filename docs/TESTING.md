# Testing Notes

## English

## Verified Environments

- Windows PowerShell with `py -3`
- Windows Python version: `3.13.5`
- WSL Ubuntu with
  `/mnt/d/QQ/Downloads/Voice_call/Voice_call/.venv/bin/python3`
- WSL Python version: `3.12.3`

## Verified Scenarios

### Audio Probes

Windows PowerShell:

- PyAudio device enumeration: passed
- output stream open: passed
- input stream open: passed
- playback test tone: passed
- microphone read: passed

WSL:

- PyAudio device enumeration: passed
- output stream open: passed
- input stream open: passed
- playback test tone: passed
- microphone read: passed

### End-to-End Program Tests

- Windows local loopback: passed
- WSL local loopback: passed
- WSL server -> Windows client: passed
- Windows server -> WSL client: passed

## Important Test Observations

- WSL audio works through Pulse/WSLg in the current environment.
- WSL still emits ALSA/JACK probe noise to stderr.
- On Windows, redirected logs can show encoding artifacts in the volume bar.
- Forced process termination during tests naturally causes a peer disconnect or
  connection reset message at the end of the run.
- Current tests used the present defaults: `rate=48000`, `channels=1`,
  `chunk=1024`, unless old-script compatibility was being discussed.

## Old Script Compatibility

The refactored script can interoperate with the old single-file script when the
refactored side matches the old audio format:

```powershell
py -3 voice_call.py --mode client --host PEER_IP --port 5000 --rate 44100 --channels 2
```

or:

```powershell
py -3 voice_call.py --mode server --port 5000 --rate 44100 --channels 2
```

## 中文

## 已验证环境

- Windows PowerShell，使用 `py -3`
- Windows Python 版本：`3.13.5`
- WSL Ubuntu，使用
  `/mnt/d/QQ/Downloads/Voice_call/Voice_call/.venv/bin/python3`
- WSL Python 版本：`3.12.3`

## 已验证场景

### 音频探针

Windows PowerShell：

- PyAudio 设备枚举：通过
- 输出流打开：通过
- 输入流打开：通过
- 测试音播放：通过
- 麦克风读取：通过

WSL：

- PyAudio 设备枚举：通过
- 输出流打开：通过
- 输入流打开：通过
- 测试音播放：通过
- 麦克风读取：通过

### 端到端程序测试

- Windows 本机回环：通过
- WSL 本机回环：通过
- WSL 服务端 -> Windows 客户端：通过
- Windows 服务端 -> WSL 客户端：通过

## 重要测试现象

- 当前环境中，WSL 音频通过 Pulse/WSLg 可以正常工作。
- WSL 仍会把 ALSA/JACK 探测噪声打印到 stderr。
- 在 Windows 上，如果把输出重定向到日志，音量条可能出现编码乱码。
- 测试时如果强制结束进程，结尾出现 peer disconnected 或 connection reset
  属于正常现象。
- 除非特别讨论旧版兼容性，否则当前测试都使用现有默认值：`rate=48000`、
  `channels=1`、`chunk=1024`。

## 与旧版脚本的兼容性

重构版可以与旧版单文件脚本互通，但重构版必须匹配旧版音频格式：

```powershell
py -3 voice_call.py --mode client --host 对方IP --port 5000 --rate 44100 --channels 2
```

或者：

```powershell
py -3 voice_call.py --mode server --port 5000 --rate 44100 --channels 2
```
