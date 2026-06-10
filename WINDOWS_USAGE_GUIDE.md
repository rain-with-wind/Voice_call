# Windows 使用指南

## 适用范围

这份文档只针对 Windows 终端用法。

不涉及：

- WSL
- Linux
- Bash

命令默认在 PowerShell 中执行。

项目目录请替换成你自己的实际路径，例如：

```text
C:\path\to\Voice_call_cli_new_architecture
```

下面统一用这个占位路径：

```text
C:\path\to\Voice_call_cli_new_architecture
```

## 这套东西怎么用

一次通话只需要一台机器当房主。

角色分成两种：

1. 房主
   - 启动本地后端
   - 用 `ngrok` 暴露后端
   - 发起通话
2. 加入者
   - 根据通话码加入通话

注意：

- 双方都可以部署这套代码
- 但一次通话里只需要一边开后端
- 双方最终都通过命令行说话

## 一次性准备

### 1. 准备语音 CLI 环境

在两台机器上都执行：

```powershell
cd C:\path\to\Voice_call_cli_new_architecture
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -r .\requirements.txt
```

### 2. 准备后端环境

只在可能当房主的机器上执行：

```powershell
cd C:\path\to\Voice_call_cli_new_architecture
py -3 -m venv .venv-backend
.\.venv-backend\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -r .\requirements-backend.txt
```

### 3. 配置 ngrok

只在房主机器上执行：

```powershell
ngrok config add-authtoken YOUR_NGROK_TOKEN
```

如果 `ngrok` 不在 PATH，就改成完整路径：

```powershell
& "C:\path\to\ngrok.exe" config add-authtoken YOUR_NGROK_TOKEN
```

## 房主操作

房主需要保持 3 个 PowerShell 窗口一直开着：

1. 后端窗口
2. ngrok 窗口
3. 发起通话窗口

### 方法一：逐行输入

#### 窗口 1：启动后端

```powershell
python .\public_backend\run.py
```

这个窗口不要关闭。

#### 窗口 2：启动 ngrok

```powershell
ngrok http 8100
```

运行后会显示一个公网地址，例如：

```text
https://xxxx.ngrok-free.app
```

记住这个地址，后面都要用。

这个窗口也不要关闭。

#### 窗口 3：发起通话

```powershell
python .\voice_call.py host-public --backend-url https://paltry-shaded-relive.ngrok-free.dev --room-name demo-call
```

运行后终端会打印一个通话码，例如：

```text
ABC123
```

把下面两项发给对方：

- 后端地址
- 通话码

这个窗口也不要关闭。

### 方法二：一条式命令

#### 窗口 1

```powershell
cd C:\path\to\Voice_call_cli_new_architecture; .\.venv-backend\Scripts\Activate.ps1; python .\public_backend\run.py
```

#### 窗口 2

```powershell
ngrok http 8100
```

#### 窗口 3

```powershell
cd C:\path\to\Voice_call_cli_new_architecture; .\.venv\Scripts\Activate.ps1; python .\voice_call.py start-call --backend-url https://xxxx.ngrok-free.app --call-name demo-call
```

## 加入者操作

加入者只需要一个 PowerShell 窗口。

### 方法一：逐行输入

```powershell
cd C:\path\to\Voice_call_cli_new_architecture
.\.venv\Scripts\Activate.ps1
python .\voice_call.py join-call --backend-url https://xxxx.ngrok-free.app --call-code ABC123
```

### 方法二：一条式命令

```powershell
cd C:\path\to\Voice_call_cli_new_architecture; .\.venv\Scripts\Activate.ps1; python .\voice_call.py join-call --backend-url https://xxxx.ngrok-free.app --call-code ABC123
```

## 常用辅助命令

### 检查后端状态

```powershell
cd C:\path\to\Voice_call_cli_new_architecture
.\.venv\Scripts\Activate.ps1
python .\voice_call.py backend-health --backend-url https://xxxx.ngrok-free.app
```

### 查看当前通话列表

```powershell
cd C:\path\to\Voice_call_cli_new_architecture
.\.venv\Scripts\Activate.ps1
python .\voice_call.py list-calls --backend-url https://xxxx.ngrok-free.app
```

### 查看本机设备信息

```powershell
cd C:\path\to\Voice_call_cli_new_architecture
.\.venv\Scripts\Activate.ps1
python .\voice_call.py device-info --json
```

## 最小流程

### 房主最小流程

先做一次环境准备：

```powershell
cd C:\path\to\Voice_call_cli_new_architecture
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -r .\requirements.txt
```

```powershell
cd C:\path\to\Voice_call_cli_new_architecture
py -3 -m venv .venv-backend
.\.venv-backend\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -r .\requirements-backend.txt
```

然后开 3 个窗口分别运行：

```powershell
cd C:\path\to\Voice_call_cli_new_architecture; .\.venv-backend\Scripts\Activate.ps1; python .\public_backend\run.py
```

```powershell
ngrok http 8100
```

```powershell
cd C:\path\to\Voice_call_cli_new_architecture; .\.venv\Scripts\Activate.ps1; python .\voice_call.py start-call --backend-url https://xxxx.ngrok-free.app --call-name demo-call
```

### 加入者最小流程

先做一次环境准备：

```powershell
cd C:\path\to\Voice_call_cli_new_architecture
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -r .\requirements.txt
```

然后加入：

```powershell
cd C:\path\to\Voice_call_cli_new_architecture; .\.venv\Scripts\Activate.ps1; python .\voice_call.py join-call --backend-url https://xxxx.ngrok-free.app --call-code ABC123
```

## 注意事项

- 一次通话里只需要一个后端
- 房主必须一直保持后端、`ngrok`、`start-call` 三个进程都在运行
- 加入者只需要保持 `join-call` 进程运行
- 如果 `ngrok` 重启，公网地址可能变化，双方都要改成新的后端地址
- `--call-name` 只是这次通话的显示名称
- 真正加入时依赖的是 `--call-code`

## 常见问题

### 1. 后端已经启动，但对方加入失败

检查：

- `ngrok` 是否还在运行
- 后端地址是否是当前最新地址
- 通话码是否正确
- 房主的 `start-call` 进程是否还在

### 2. 提示 `ngrok` 找不到

检查：

```powershell
Get-Command ngrok -ErrorAction SilentlyContinue
```

如果没有结果，就用完整路径：

```powershell
& "C:\path\to\ngrok.exe" http 8100
```

### 3. 提示执行脚本被系统拦截

先在当前 PowerShell 窗口执行：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
```

然后再执行：

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. 提示音频相关错误

重新安装 CLI 依赖：

```powershell
cd C:\path\to\Voice_call_cli_new_architecture
.\.venv\Scripts\Activate.ps1
python -m pip install -r .\requirements.txt
```

同时确认麦克风和扬声器在系统里工作正常。

### 5. 提示后端依赖缺失

重新安装后端依赖：

```powershell
cd C:\path\to\Voice_call_cli_new_architecture
.\.venv-backend\Scripts\Activate.ps1
python -m pip install -r .\requirements-backend.txt
```
