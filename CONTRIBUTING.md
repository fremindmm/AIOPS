# 贡献指南

感谢你对 AIOPS 项目的关注！我们欢迎任何形式的贡献。

## 🎯 我们需要什么样的贡献

### 代码贡献
- **新功能开发**: 查看 [Issues](https://github.com/yourusername/aiops/issues) 中标记为 `enhancement` 的需求
- **Bug 修复**: 查看标记为 `bug` 的问题
- **性能优化**: 提升系统性能和响应速度
- **测试用例**: 增加单元测试和集成测试覆盖率

### 非代码贡献
- **文档完善**: 改进 README、API 文档、使用教程
- **问题反馈**: 报告 bug 或提出改进建议
- **案例分享**: 分享你的使用场景和最佳实践
- **翻译工作**: 帮助项目国际化

## 🚀 快速开始

### 1. 环境准备

```bash
# Fork 并克隆项目
git clone https://github.com/YOUR_USERNAME/aiops.git
cd aiops

# 添加上游仓库
git remote add upstream https://github.com/ORIGINAL_OWNER/aiops.git

# 创建开发环境
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 开发依赖
```

### 2. 开发流程

```bash
# 同步上游代码
git fetch upstream
git checkout main
git merge upstream/main

# 创建特性分支
git checkout -b feature/your-feature-name

# 进行开发...
# 运行测试
python -m pytest tests/

# 提交代码
git add .
git commit -m "feat: add amazing feature"
git push origin feature/your-feature-name
```

### 3. 提交规范

我们使用语义化提交信息：

- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式化，不影响功能
- `refactor`: 代码重构
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

示例：
```
feat: 添加 Prometheus 监控集成
fix: 修复内存泄漏问题
docs: 更新 API 文档
```

## 📋 代码规范

### Python 代码规范

```python
# 使用 PEP 8 规范
# 使用 Black 格式化代码
black your_file.py

# 使用 Type Hints
def analyze_alert(alert: Alert) -> RootCause:
    """分析告警并返回根因"""
    pass

# 编写清晰的文档字符串
def make_decision(self, alert: Alert) -> Decision:
    """
    基于告警做出决策

    Args:
        alert: 告警对象

    Returns:
        Decision: 包含操作建议的决策对象
    """
    pass
```

### 测试要求

```python
# 测试文件命名: test_*.py
# 测试函数命名: test_*

def test_causality_engine():
    """测试因果分析引擎"""
    engine = CausalityEngine()
    alert = Alert(...)
    result = engine.analyze(alert)
    assert result.confidence > 0.8
```

## 🏗️ 项目结构

```
aiops/
├── engine/              # 核心引擎
│   ├── causality.py    # 因果分析
│   ├── decision.py     # 决策引擎
│   └── knowledge.py    # 知识库
├── services/           # 服务层
│   └── mock_data.py   # 模拟数据服务
├── templates/         # 前端模板
├── static/           # 静态资源
├── tests/            # 测试用例
├── docs/             # 文档
└── app.py           # 主应用

```

## 🔍 Pull Request 流程

1. **确保代码质量**
   - 通过所有测试用例
   - 代码符合规范
   - 添加必要的测试
   - 更新相关文档

2. **PR 描述模板**
   ```markdown
   ## 变更说明
   简要描述这个 PR 的目的

   ## 变更类型
   - [ ] Bug 修复
   - [ ] 新功能
   - [ ] 性能优化
   - [ ] 文档更新

   ## 测试情况
   - [ ] 单元测试通过
   - [ ] 集成测试通过
   - [ ] 手动测试通过

   ## 相关 Issue
   Fixes #123
   ```

3. **代码审查**
   - 至少需要一位维护者的审查
   - 解决所有评论和建议
   - 确保 CI/CD 检查通过

## 🎖️ 贡献者行为准则

### 我们的承诺
- 营造开放、友好的社区氛围
- 尊重不同观点和经验
- 优雅地接受建设性批评
- 关注社区最佳利益

### 不可接受的行为
- 使用不当言语或图像
- 人身攻击或政治攻击
- 公开或私下骚扰
- 未经许可发布他人信息

## 💡 需要帮助？

- **技术问题**: 在 [Discussions](https://github.com/yourusername/aiops/discussions) 提问
- **Bug 报告**: 在 [Issues](https://github.com/yourusername/aiops/issues) 提交
- **功能建议**: 创建 [Feature Request](https://github.com/yourusername/aiops/issues/new?template=feature_request.md)

## 🌟 成为核心贡献者

持续贡献高质量代码的开发者将被邀请成为项目的核心贡献者，获得：
- 直接提交权限
- 参与项目规划
- 优先技术支持
- 贡献者证书

---

再次感谢你的贡献！让我们一起打造最好用的智能运维平台！ 🚀