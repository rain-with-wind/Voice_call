# 开发指南

## 项目结构

```
Voice_call/
├── docs/                  # 文档
│   ├── ARCHITECTURE.md    # 架构说明
│   ├── USAGE.md           # 使用指南
│   ├── DEVELOPMENT.md     # 开发指南（本文件）
│   └── TESTING.md         # 测试说明
├── voice_call_app/        # 核心代码
│   ├── __init__.py
│   ├── cli.py             # 命令行解析
│   ├── config.py          # 配置数据类
│   ├── console.py         # 终端颜色工具
│   ├── windows.py         # Windows UTF-8 设置
│   ├── crypto.py          # 认证与加密
│   ├── audio.py           # 音频设备管理
│   ├── stats.py           # 运行时统计
│   └── engine.py          # 核心引擎
├── voice_call.py          # 入口文件
├── requirements.txt       # Python 依赖
├── LICENSE                # MIT 许可证
└── README.md
```

## 环境设置

```bash
# 克隆仓库
git clone <repo-url>
cd Voice_call

# 安装依赖
pip install -r requirements.txt
```

## 代码检查

```powershell
# 编译检查所有 Python 文件
python -m compileall voice_call.py voice_call_app
```

## 手工验证清单

- [ ] `python voice_call.py --help` 正常输出
- [ ] `python voice_call.py --list-devices` 列出设备
- [ ] 本机回环：两个终端分别启动 server / client 能通话
- [ ] 跨机器：Windows ↔ WSL 或 Windows ↔ Linux
- [ ] 加密模式：`--encrypt --password test` 双方互通

## 添加新功能

1. 在对应的模块中添加代码
2. 如需新依赖，更新 `requirements.txt`
3. 如需新 CLI 参数，在 `cli.py` 中添加并在 `config.py` 中添加对应字段
4. 更新相关文档
5. 运行 `python -m compileall voice_call.py voice_call_app` 确保无语法错误

## 依赖说明

| 包 | 版本 | 用途 |
|----|------|------|
| `pyaudio` | 0.2.14 | 音频采集与播放（PortAudio 绑定） |
| `cryptography` | 41.0.7 | Fernet 加密与 PBKDF2 密钥派生 |

仅使用 Python 标准库和以上两个第三方包。
