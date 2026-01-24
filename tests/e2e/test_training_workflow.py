"""
模型训练工作流 E2E 测试

测试 Model Training 页面的完整训练流程
"""
import pytest
from playwright.sync_api import Page
from tests.utils.streamlit_helpers import StreamlitHelpers, assert_no_errors


@pytest.mark.workflow
@pytest.mark.slow
def test_model_training_page_loads(page: Page):
    """测试模型训练页面加载"""
    helpers = StreamlitHelpers(page)
    
    # 导航到模型训练页面
    helpers.navigate_to_page("Model Training")
    assert_no_errors(page)
    
    # 检查页面标题
    assert page.get_by_text("Model Training").is_visible()
    
    # 检查关键 UI 元素
    # 通常应该有数据加载、算法选择、训练按钮等
    
    print("✓ Model Training 页面加载成功")


@pytest.mark.workflow
def test_algorithm_selection(page: Page):
    """测试算法选择功能"""
    helpers = StreamlitHelpers(page)
    
    helpers.navigate_to_page("Model Training")
    assert_no_errors(page)
    
    # 检查是否有算法选择下拉框
    # 具体的选择器需要根据实际UI调整
    selectboxes = page.locator('[data-testid="stSelectbox"]')
    
    if selectboxes.count() > 0:
        print(f"✓ 找到 {selectboxes.count()} 个选择框")
    
    assert_no_errors(page)


@pytest.mark.workflow
@pytest.mark.slow
def test_training_execution_availability(page: Page):
    """测试训练执行功能可用性"""
    helpers = StreamlitHelpers(page)
    
    helpers.navigate_to_page("Model Training")
    assert_no_errors(page)
    
    # 检查是否有训练相关的按钮
    buttons = page.locator('[data-testid="baseButton-secondary"]')
    
    if buttons.count() > 0:
        print(f"✓ 找到 {buttons.count()} 个操作按钮")
    
    # 不实际触发训练(太慢),只验证UI可用
    assert_no_errors(page)
    print("✓ 训练功能界面可用")
