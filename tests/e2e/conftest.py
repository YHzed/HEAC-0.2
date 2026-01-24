"""
简化的 E2E 测试配置 - 使用已运行的 Streamlit 服务器

使用方法:
1. 先手动启动 Streamlit: streamlit run Home.py
2. 然后运行测试: pytest tests/e2e/
"""
import pytest
from playwright.sync_api import sync_playwright, Browser, Page, BrowserContext


# Streamlit 应用配置
STREAMLIT_URL = "http://localhost:8501"


@pytest.fixture(scope="session")
def browser():
    """
    创建 Playwright 浏览器实例(会话级别,所有测试共享)
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,  # 无头模式,适合 CI/CD
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def context(browser: Browser) -> BrowserContext:
    """
    为每个测试创建新的浏览器上下文(隔离 cookies/storage)
    """
    context = browser.new_context(
        viewport={'width': 1280, 'height': 720},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    )
    yield context
    context.close()


@pytest.fixture(scope="function")
def page(context: BrowserContext) -> Page:
    """
    为每个测试创建新页面并导航到 Streamlit 应用
    
    注意:此 fixture 要求 Streamlit 服务器已在 http://localhost:8501 运行
    如果服务器未运行,测试将失败
    """
    page = context.new_page()
    
    # 导航到应用
    try:
        page.goto(STREAMLIT_URL, timeout=10000)
        page.wait_for_load_state('networkidle', timeout=15000)
    except Exception as e:
        raise RuntimeError(
            f"无法连接到 Streamlit 服务器 ({STREAMLIT_URL})。"
            f"请先运行: streamlit run Home.py\n"
            f"错误: {e}"
        )
    
    yield page
    page.close()


def pytest_configure(config):
    """注册自定义标记"""
    config.addinivalue_line(
        "markers", "slow: 标记测试为慢速测试(需较长时间)"
    )
    config.addinivalue_line(
        "markers", "workflow: 标记为完整工作流测试"
    )

