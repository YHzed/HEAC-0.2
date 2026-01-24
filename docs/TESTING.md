# HEAC 0.2 E2E 测试指南

## 🎯 测试框架概述

本项目使用 **Playwright** 进行端到端(E2E)测试,验证 Streamlit 应用的功能完整性。

---

## 🚀 快速开始

### 前置要求

- Python 3.10+
- Playwright 已安装: `pip install playwright pytest-playwright`
- Chromium 浏览器: `python -m playwright install chromium`

### 运行所有测试

```bash
# 确保在正确的环境中
conda activate heac-0.2

# 运行所有 E2E 测试
pytest tests/e2e/

# 运行特定测试文件
pytest tests/e2e/test_page_health.py

# 运行特定测试
pytest tests/e2e/test_page_health.py::test_home_page_loads
```

---

## 📁 测试结构

```
tests/
├── e2e/                    # E2E 测试
│   ├── conftest.py         # pytest 配置和 fixtures
│   ├── test_page_health.py # 页面健康检查
│   └── test_data_workflow.py # 数据处理工作流
├── utils/                  # 测试工具
│   └── streamlit_helpers.py # Streamlit 辅助函数
└── screenshots/            # 测试截图 (自动生成)
```

---

## 🧪 测试类别

### 1. 页面健康检查 (`test_page_health.py`)

验证所有页面能正常加载:
- ✅ 主页加载
- ✅ 所有页面可访问
- ✅ 侧边栏导航
- ✅ 无控制台错误
- ✅ 性能检查

### 2. 工作流测试 (`test_data_workflow.py`)

测试核心业务流程:
- 数据上传和处理
- 成分解析
- 特征计算

---

## 🔧 使用辅助工具

### StreamlitHelpers 类

```python
from tests.utils.streamlit_helpers import StreamlitHelpers

def test_example(page):
    helpers = StreamlitHelpers(page)
    
    # 等待应用加载
    helpers.wait_for_app_ready()
    
    # 点击按钮
    helpers.click_button("开始预测")
    
    # 导航到其他页面
    helpers.navigate_to_page("Model Training")
    
    # 截图
    helpers.take_screenshot("example_screenshot")
    
    # 检查是否有错误
    if helpers.check_error_exists():
        print(f"Error: {helpers.get_error_message()}")
```

---

## 📊 测试标记

使用 pytest 标记来组织和过滤测试:

```bash
# 只运行快速测试(排除slow标记)
pytest -m "not slow"

# 只运行工作流测试
pytest -m workflow

# 运行特定标记组合
pytest -m "e2e and not slow"
```

可用标记:
- `slow`: 慢速测试 (>10秒)
- `workflow`: 完整工作流测试
- `e2e`: 端到端测试

---

## 🐛 调试

### 查看浏览器界面

修改 `conftest.py` 中的 `headless` 参数:

```python
browser = p.chromium.launch(
    headless=False,  # 改为 False 可见浏览器
    slow_mo=500      # 减慢操作速度
)
```

### 截图调试

测试失败时会自动截图到 `tests/screenshots/`:

```python
helpers.take_screenshot("debug_screenshot")
```

### 查看详细日志

```bash
pytest -v -s tests/e2e/
```

---

## ⚙️ 配置

### Streamlit 服务器

测试自动管理 Streamlit 服务器:
- 如果已有服务器在 8501 端口运行,则使用现有服务器
- 否则启动新服务器并在测试结束后关闭

### pytest.ini

主要配置:
- 测试路径: `tests/`
- 日志级别: `INFO`
- 自定义标记: slow, workflow, e2e

---

## 📝 编写新测试

### 基本模板

```python
import pytest
from playwright.sync_api import Page
from tests.utils.streamlit_helpers import StreamlitHelpers, assert_no_errors

def test_new_feature(page: Page):
    """测试新功能"""
    helpers = StreamlitHelpers(page)
    
    # 1. 导航
    helpers.navigate_to_page("Page Name")
    
    # 2. 交互
    helpers.click_button("Button Text")
    
    # 3. 断言
    assert_no_errors(page)
    assert page.get_by_text("Expected Text").is_visible()
    
    print("✓ 测试通过")
```

### 最佳实践

1. **清晰的测试名称**: 使用描述性名称,如 `test_user_can_upload_csv_file`
2. **独立测试**: 每个测试应独立运行,不依赖其他测试
3. **适当的等待**: 使用 `wait_for_app_ready()` 而非固定 `sleep()`
4. **错误处理**: 测试失败时截图以便调试
5. **注释**: 复杂测试添加步骤注释

---

## 🚨 常见问题

### Q: 测试超时

**原因**: Streamlit 应用加载慢或卡住  
**解决**: 增加 timeout 参数或检查应用日志

### Q: 元素找不到

**原因**: Streamlit 渲染未完成或选择器错误  
**解决**: 使用 `wait_for_app_ready()` 并检查选择器

### Q: 服务器启动失败

**原因**: 端口被占用或依赖缺失  
**解决**: 检查端口 8501,确保依赖已安装

---

## 📈 持续集成

### GitHub Actions 示例

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install playwright pytest-playwright
          python -m playwright install chromium
      - name: Run E2E tests
        run: pytest tests/e2e/
```

---

## 📚 参考资源

- [Playwright 文档](https://playwright.dev/python/)
- [pytest 文档](https://docs.pytest.org/)
- [Streamlit 测试指南](https://docs.streamlit.io/library/advanced-features/testing)

---

*最后更新: 2026-01-23*
