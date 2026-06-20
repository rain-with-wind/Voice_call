# 开发说明

本文档记录项目的开发环境、目录结构、修改流程和代码约定，方便后续维护。

## 1. 目录结构

```text
Voice_call/
├── docs/                  # 项目文档、报告、协作说明和安全说明
├── tools/                 # 环境排查和测试脚本
├── voice_call_app/        # 核心代码包
├── voice_call.py          # 入口文件
├── requirements.txt       # 依赖声明
├── README.md              # 主说明文档
└── LICENSE                # MIT 许可证
```

## 2. 开发环境

建议使用 Python 3.10 及以上版本。

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

Windows PowerShell：

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -r requirements.txt
```

## 3. 模块修改原则

项目按职责拆分模块，修改时尽量保持边界清楚：

| 模块 | 修改内容 |
| --- | --- |
| `cli.py` | 新增或修改命令行参数 |
| `config.py` | 新增运行时配置字段 |
| `audio.py` | 音频设备、采集、播放相关逻辑 |
| `crypto.py` | 认证、密钥派生、加密解密 |
| `engine.py` | socket、线程、通话流程 |
| `stats.py` | 统计数据和显示格式 |
| `console.py` | 终端颜色和输出样式 |
| `windows.py` | Windows 控制台兼容处理 |

如果新增 CLI 参数，一般需要同时修改：

1. `voice_call_app/cli.py`
2. `voice_call_app/config.py`
3. `README.md`
4. `docs/USAGE.md`
5. `docs/TESTING.md`

## 4. 代码风格

- 函数和变量使用清晰的英文命名
- 用户可见输出可以使用中文
- 一个模块只处理一类职责
- 尽量避免在多个地方重复同一段逻辑
- 资源释放要放在 `finally` 或统一清理函数中
- socket 接收固定长度数据时使用 `_recv_exact` 这类封装，不直接假设一次 `recv` 能收完整包

## 5. 运行检查

提交前建议至少执行：

```powershell
python -m compileall voice_call.py voice_call_app tools
python voice_call.py --help
python voice_call.py --list-devices
```

如果修改了通信、音频或加密逻辑，还需要做本机回环和加密模式测试。

## 6. 常见修改示例

### 新增命令行参数

1. 在 `cli.py` 中添加 `parser.add_argument`
2. 在 `VoiceCallConfig` 中添加字段
3. 创建配置对象时传入参数
4. 在需要的模块中读取 `self.config.<字段>`
5. 更新文档和测试清单

### 修改音频默认参数

1. 修改 `VoiceCallConfig` 中的默认值
2. 检查 README 和 USAGE 中的默认值
3. 做本机回环测试
4. 如果涉及旧版兼容，说明兼容参数

### 修改加密流程

1. 优先修改 `crypto.py`
2. 保持 `engine.py` 中调用接口尽量稳定
3. 测试普通模式、密码认证模式、加密模式和错误密码场景
4. 更新 `docs/SECURITY.md`

## 7. 依赖管理

当前第三方依赖只有：

| 包 | 版本 | 用途 |
| --- | --- | --- |
| `pyaudio` | `0.2.14` | 音频采集和播放 |
| `cryptography` | `41.0.7` | Fernet 加密和 PBKDF2 密钥派生 |

新增依赖时要考虑：

- 是否确实必要
- 是否有稳定维护
- 是否需要额外系统库
- 是否会增加安装难度
- 是否需要更新安全说明

## 8. 文档维护

代码行为变化后要同步检查：

- 主 README 是否仍准确
- 使用说明中的命令是否可用
- 测试说明是否覆盖新功能
- 安全说明是否需要更新
- 实验报告中的项目结构和功能描述是否过时

## 9. 分支和提交

建议分支命名：

- `feature/audio-device-selection`
- `fix/encryption-handshake`
- `docs/update-usage`
- `refactor/split-engine`

建议提交信息：

- `feat: add manual audio device selection`
- `fix: handle invalid pcm frame length`
- `docs: update testing guide`
- `refactor: split crypto helpers`

## 10. 后续改进方向

- 增加自动化单元测试
- 增加日志文件
- 支持配置文件
- 支持音频压缩编码
- 支持自动重连
- 增加更友好的图形界面
