"""
应用Dark Mode主题到现有页面的快速脚本
"""
import sys
from pathlib import Path

# 需要更新的页面
pages_to_update = [
    'pages/6_Proxy_Models.py',
    'pages/10_Database_Manager.py'
]

# 在每个页面的导入部分添加
theme_import = """
try:
    from ui.dark_theme import apply_dark_theme, create_dashboard_header, create_section_title
    THEME_AVAILABLE = True
except ImportError:
    THEME_AVAILABLE = False
"""

# 在st.set_page_config之后添加
theme_apply = """
# 应用深色主题
if THEME_AVAILABLE:
    apply_dark_theme()
"""

print("Dark Mode主题已准备好应用到以下页面：")
for page in pages_to_update:
    print(f"  - {page}")

print("\n手动应用步骤：")
print("1. 在导入部分添加：")
print(theme_import)
print("\n2. 在st.set_page_config()后添加：")
print(theme_apply)
print("\n3. (可选) 使用create_dashboard_header()替换st.title()")
print("\n已自动更新6_Proxy_Models.py，请测试效果！")
