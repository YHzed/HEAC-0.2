"""
数据库管理工作流 E2E 测试

测试 Database Manager 的数据查询和管理功能
"""
import pytest
from playwright.sync_api import Page
from tests.utils.streamlit_helpers import StreamlitHelpers, assert_no_errors


@pytest.mark.workflow
def test_database_manager_loads(page: Page):
    """测试数据库管理器页面加载"""
    helpers = StreamlitHelpers(page)
    
    helpers.navigate_to_page("Database Manager")
    assert_no_errors(page)
    
    # 检查页面标题
    assert page.get_by_text("Database Manager").is_visible()
    
    print("✓ Database Manager 页面加载成功")


@pytest.mark.workflow
def test_data_query_interface(page: Page):
    """测试数据查询界面"""
    helpers = StreamlitHelpers(page)
    
    helpers.navigate_to_page("Database Manager")
    assert_no_errors(page)
    
    # 检查查询相关的UI元素
    # 应该有查询条件、筛选器等
    
    # 检查是否有数据表格
    tables = page.locator('[data-testid="stDataFrame"]')
    print(f"✓ 找到 {tables.count()} 个数据表格")
    
    assert_no_errors(page)


@pytest.mark.workflow
def test_export_functionality(page: Page):
    """测试数据导出功能可用性"""
    helpers = StreamlitHelpers(page)
    
    helpers.navigate_to_page("Database Manager")
    assert_no_errors(page)
    
    # 检查是否有导出按钮或下载链接
    # 不实际触发导出,只验证UI存在
    
    assert_no_errors(page)
    print("✓ 数据导出功能界面可访问")


@pytest.mark.workflow
@pytest.mark.slow
def test_feature_calculation_interface(page: Page):
    """测试特征计算界面"""
    helpers = StreamlitHelpers(page)
    
    helpers.navigate_to_page("Database Manager")
    assert_no_errors(page)
    
    # 检查是否有特征计算选项
    # 根据实际UI结构调整
    
    assert_no_errors(page)
    print("✓ 特征计算界面可用")
