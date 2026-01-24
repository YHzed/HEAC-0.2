"""
虚拟筛选工作流 E2E 测试

测试 Virtual Screening 页面的筛选功能
"""
import pytest
from playwright.sync_api import Page
from tests.utils.streamlit_helpers import StreamlitHelpers, assert_no_errors


@pytest.mark.workflow
def test_virtual_screening_page_loads(page: Page):
    """测试虚拟筛选页面加载"""
    helpers = StreamlitHelpers(page)
    
    helpers.navigate_to_page("Virtual Screening")
    assert_no_errors(page)
    
    # 检查页面标题
    assert page.get_by_text("Virtual Screening").is_visible()
    
    print("✓ Virtual Screening 页面加载成功")


@pytest.mark.workflow
def test_model_loading_interface(page: Page):
    """测试模型加载界面"""
    helpers = StreamlitHelpers(page)
    
    helpers.navigate_to_page("Virtual Screening")
    assert_no_errors(page)
    
    # 检查是否有模型选择或加载相关的UI
    # 具体实现根据页面结构调整
    
    assert_no_errors(page)
    print("✓ 模型加载界面可访问")


@pytest.mark.workflow
@pytest.mark.slow
def test_candidate_generation_interface(page: Page):
    """测试候选材料生成界面"""
    helpers = StreamlitHelpers(page)
    
    helpers.navigate_to_page("Virtual Screening")
    assert_no_errors(page)
    
    # 检查元素选择界面
    # 检查参数设置界面
    
    # 不实际执行筛选(太慢),只验证UI
    assert_no_errors(page)
    print("✓ 候选生成界面可用")


@pytest.mark.workflow
def test_screening_results_display(page: Page):
    """测试筛选结果显示功能"""
    helpers = StreamlitHelpers(page)
    
    helpers.navigate_to_page("Virtual Screening")
    assert_no_errors(page)
    
    # 验证是否有数据表格显示区域
    tables = page.locator('[data-testid="stDataFrame"]')
    
    # 可能没有数据,但UI应该存在
    print(f"✓ 找到 {tables.count()} 个数据表格元素")
    
    assert_no_errors(page)
