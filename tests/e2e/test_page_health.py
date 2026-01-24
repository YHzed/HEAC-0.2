"""
页面健康检查测试

测试所有 Streamlit 页面是否能正常加载,无错误
"""
import pytest
from playwright.sync_api import Page
from tests.utils.streamlit_helpers import (
    StreamlitHelpers,
    assert_no_errors,
    assert_title_contains
)


def test_home_page_loads(page: Page):
    """测试主页加载"""
    # 检查页面标题
    assert_title_contains(page, "HEAC")
    
    # 检查无错误
    assert_no_errors(page)
    
    # 检查关键元素存在
    helpers = StreamlitHelpers(page)
    
    # 检查主页应该有系统概览
    assert page.get_by_text("系统概览").is_visible()
    
    # 检查核心功能标题
    assert page.get_by_text("核心功能").is_visible()
    
    print("✓ 主页加载成功")


def test_all_pages_accessible(page: Page):
    """测试所有页面可访问"""
    helpers = StreamlitHelpers(page)
    
    # 定义所有应该可访问的页面
    pages_to_test = [
        "General ML Lab",
        "HEA Cermet Lab",
        "Process Agent",
        "GBFS Feature Selection",
        "Model Training",
        "Virtual Screening",
        "HEA Data Preprocessing",
        "Database Manager"
    ]
    
    for page_name in pages_to_test:
        print(f"测试页面: {page_name}")
        
        try:
            # 导航到页面
            helpers.navigate_to_page(page_name)
            
            # 等待页面加载
            helpers.wait_for_app_ready(timeout=15000)
            
            # 检查无错误
            assert_no_errors(page)
            
            print(f"  ✓ {page_name} 加载成功")
            
        except Exception as e:
            # 截图以便调试
            helpers.take_screenshot(f"error_{page_name.replace(' ', '_')}")
            raise AssertionError(f"页面 '{page_name}' 加载失败: {e}")


def test_sidebar_navigation(page: Page):
    """测试侧边栏导航功能"""
    # 检查侧边栏存在
    sidebar = page.locator('[data-testid="stSidebar"]')
    assert sidebar.is_visible(), "侧边栏未显示"
    
    # 检查至少有几个页面链接
    page_links = sidebar.locator('a')
    assert page_links.count() >= 5, "侧边栏页面链接数量不足"
    
    print(f"✓ 侧边栏包含 {page_links.count()} 个页面链接")


def test_no_console_errors(page: Page):
    """测试主页是否有 JavaScript 控制台错误"""
    console_errors = []
    
    def handle_console(msg):
        if msg.type == 'error':
            console_errors.append(msg.text)
    
    page.on('console', handle_console)
    
    # 重新加载页面以捕获控制台消息
    page.reload()
    page.wait_for_load_state('networkidle')
    
    # 允许一些已知的非关键错误
    filtered_errors = [
        err for err in console_errors 
        if 'favicon' not in err.lower()  # 忽略 favicon 错误
        and 'websocket' not in err.lower()  # 忽略 WebSocket 连接问题
    ]
    
    assert len(filtered_errors) == 0, \
        f"发现控制台错误: {filtered_errors}"
    
    print("✓ 无控制台错误")


@pytest.mark.slow
def test_performance_check(page: Page):
    """测试页面加载性能"""
    import time
    
    helpers = StreamlitHelpers(page)
    
    # 测试主页加载时间
    start_time = time.time()
    page.reload()
    page.wait_for_load_state('networkidle')
    load_time = time.time() - start_time
    
    # 主页应在 5 秒内加载完成
    assert load_time < 5.0, f"主页加载时间过长: {load_time:.2f}秒"
    
    print(f"✓ 主页加载时间: {load_time:.2f}秒")
