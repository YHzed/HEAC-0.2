"""
Streamlit 测试辅助函数

提供常用的 Streamlit 元素交互和断言工具
"""
from playwright.sync_api import Page, expect


class StreamlitHelpers:
    """Streamlit 测试辅助工具类"""
    
    def __init__(self, page: Page):
        self.page = page
    
    def wait_for_app_ready(self, timeout: int = 10000):
        """等待 Streamlit 应用完全加载"""
        # 等待 Streamlit 的状态指示器消失
        self.page.wait_for_selector(
            '[data-testid="stStatusWidget"]',
            state='hidden',
            timeout=timeout
        )
    
    def click_button(self, button_text: str):
        """点击包含指定文本的按钮"""
        button = self.page.get_by_role('button', name=button_text)
        button.click()
        self.wait_for_app_ready()
    
    def select_from_selectbox(self, label: str, value: str):
        """从下拉框中选择值"""
        # Streamlit selectbox 实现较复杂,需要特殊处理
        selectbox = self.page.locator(f'label:has-text("{label}")').locator('..')
        selectbox.click()
        self.page.get_by_text(value, exact=True).click()
        self.wait_for_app_ready()
    
    def upload_file(self, file_path: str):
        """上传文件"""
        file_input = self.page.locator('input[type="file"]')
        file_input.set_input_files(file_path)
        self.wait_for_app_ready()
    
    def get_metric_value(self, label: str) -> str:
        """获取 st.metric 的值"""
        metric = self.page.locator(
            f'[data-testid="stMetricLabel"]:has-text("{label}")'
        ).locator('..')
        value_element = metric.locator('[data-testid="stMetricValue"]')
        return value_element.inner_text()
    
    def check_error_exists(self) -> bool:
        """检查页面是否有错误消息"""
        errors = self.page.locator('[data-testid="stException"]')
        return errors.count() > 0
    
    def get_error_message(self) -> str:
        """获取错误消息文本"""
        error = self.page.locator('[data-testid="stException"]').first
        return error.inner_text() if error else ""
    
    def navigate_to_page(self, page_name: str):
        """通过侧边栏导航到指定页面"""
        # 点击侧边栏中的页面链接
        sidebar = self.page.locator('[data-testid="stSidebar"]')
        page_link = sidebar.get_by_text(page_name)
        page_link.click()
        self.wait_for_app_ready()
    
    def take_screenshot(self, name: str):
        """截取页面截图(保存到 tests/screenshots/)"""
        import os
        os.makedirs('tests/screenshots', exist_ok=True)
        self.page.screenshot(path=f'tests/screenshots/{name}.png')


def assert_no_errors(page: Page):
    """断言页面没有 Streamlit 错误"""
    helpers = StreamlitHelpers(page)
    assert not helpers.check_error_exists(), \
        f"页面出现错误: {helpers.get_error_message()}"


def assert_title_contains(page: Page, text: str):
    """断言页面标题包含指定文本"""
    title = page.locator('h1').first.inner_text()
    assert text in title, f"标题 '{title}' 不包含 '{text}'"


def wait_for_computation(page: Page, timeout: int = 30000):
    """等待长时间计算完成"""
    helpers = StreamlitHelpers(page)
    helpers.wait_for_app_ready(timeout=timeout)
