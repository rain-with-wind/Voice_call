# 贡献指南

感谢你对本项目感兴趣！以下是参与贡献的方式。

## 如何贡献

### 报告问题

在 GitHub Issues 中提交 bug 报告或功能建议，请包含：

- 你的操作系统和 Python 版本
- 复现步骤
- 实际结果和期望结果

### 提交代码

1. Fork 本仓库
2. 创建功能分支：`git checkout -b feature/xxx`
3. 提交更改：`git commit -m "feat: 描述你的改动"`
4. 推送到分支：`git push origin feature/xxx`
5. 创建 Pull Request

### 提交信息格式

使用约定式提交：

- `feat:` 新功能
- `fix:` Bug 修复
- `docs:` 文档更新
- `refactor:` 代码重构
- `chore:` 杂项

## 开发规范

- 保持模块职责单一
- 新增依赖需在 `requirements.txt` 中声明版本号
- CLI 参数在 `cli.py` 中定义，配置字段在 `config.py` 中添加
- 运行 `python -m compileall voice_call.py voice_call_app` 确保无语法错误

## 测试

提交前请验证：

- [ ] 本机回环通话正常
- [ ] `--list-devices` 正常输出
- [ ] 加密模式正常
- [ ] Ctrl+C 正常退出

## 行为准则

请遵循以下基本原则：

- 尊重所有贡献者
- 建设性地提出意见
- 专注于对项目有益的内容
