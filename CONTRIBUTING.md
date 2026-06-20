# 贡献指南

欢迎对本项目提出问题、建议或代码改进。为了让沟通和维护更顺畅，提交前请先阅读下面的说明。

## 可以贡献什么

- 修复运行错误
- 改进音频设备选择
- 改进 Windows / WSL / Linux 兼容性
- 补充测试用例或测试脚本
- 完善使用说明和排查文档
- 改进认证、加密或错误处理
- 提出更好的项目结构建议

## 报告问题

提交 Issue 时建议包含：

- 操作系统和版本
- Python 版本
- 运行命令
- 完整错误信息
- 复现步骤
- 期望结果和实际结果

如果问题与音频设备有关，请附上：

```powershell
python voice_call.py --list-devices
```

的输出内容。

## 提交代码

建议流程：

1. Fork 仓库
2. 创建分支
3. 修改代码和文档
4. 本地完成测试
5. 提交 Pull Request

示例：

```bash
git checkout -b fix/audio-device-selection
git add .
git commit -m "fix: improve audio device selection"
git push origin fix/audio-device-selection
```

## 提交信息

建议使用以下格式：

| 类型 | 说明 |
| --- | --- |
| `feat:` | 新功能 |
| `fix:` | Bug 修复 |
| `docs:` | 文档修改 |
| `refactor:` | 重构 |
| `test:` | 测试相关 |
| `chore:` | 构建、依赖、杂项 |

示例：

```text
docs: update usage guide
fix: handle invalid pcm packet length
feat: add manual output device option
```

## 开发要求

- 保持模块职责清楚
- 不把无关修改混在一个 PR 里
- 新增依赖需要更新 `requirements.txt`
- 新增 CLI 参数需要更新 README 和使用说明
- 修改安全相关逻辑需要更新 `SECURITY.md`
- 修改通信或音频逻辑后需要做本机回环测试

## 提交前检查

```powershell
python -m compileall voice_call.py voice_call_app tools
python voice_call.py --help
python voice_call.py --list-devices
```

建议再手工验证：

- [ ] 本机回环通话
- [ ] 加密模式通话
- [ ] Ctrl+C 正常退出
- [ ] 文档与实际参数一致

## Pull Request 说明

PR 描述中建议写清楚：

- 修改了什么
- 为什么修改
- 如何测试
- 是否影响已有命令
- 是否需要更新文档

## 行为准则

交流时请保持尊重、清晰和建设性。遇到不同意见时优先围绕问题本身讨论，不进行人身攻击或无意义争论。
