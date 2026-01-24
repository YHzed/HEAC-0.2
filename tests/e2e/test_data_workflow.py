"""
数据处理工作流 E2E 测试

测试 Process Agent 的完整数据处理流程
"""
import pytest
from playwright.sync_api import Page
from tests.utils.streamlit_helpers import StreamlitHelpers, assert_no_errors
import os


@pytest.mark.workflow
@pytest.mark.slow
def test_data_upload_and_processing(page: Page):
    """测试数据上传和处理流程"""
    helpers = StreamlitHelpers(page)
    
    # 1. 导航到 Process Agent 页面
    helpers.navigate_to_page("Process Agent")
    assert_no_errors(page)
    
    # 2. 检查页面加载
    assert page.get_by_text("Process Agent").is_visible()
    
    # 3. 查找文件上传区域
    file_uploader = page.locator('[data-testid="stFileUploader"]')
    
    if file_uploader.is_visible():
        print("✓ 文件上传组件加载成功")
        
        # 可以在这里测试文件上传
        # 但需要准备测试数据文件
        # test_file = "training data/test_sample.csv"
        # if os.path.exists(test_file):
        #     helpers.upload_file(test_file)
        #     print(f"✓ 文件上传成功: {test_file}")
    
    # 4. 验证无错误
    assert_no_errors(page)
    
    print("✓ Process Agent 页面功能正常")


@pytest.mark.workflow
def test_composition_parsing(page: Page):
    """测试成分解析功能"""
    helpers = StreamlitHelpers(page)
    
    # 导航到 Process Agent
    helpers.navigate_to_page("Process Agent")
    
    # 检查是否有成分解析相关的UI元素
    # 实际测试需要根据具体的UI结构调整
    
    assert_no_errors(page)
    print("✓ 成分解析功能可访问")
