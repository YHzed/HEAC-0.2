"""
批量应用Apex主题到所有pages的脚本
"""

import os
from pathlib import Path

# Apex主题导入代码片段
APEX_IMPORT = """
# 导入Apex主题
try:
    from ui.apex_theme import apply_apex_theme, create_apex_header, create_apex_badge, APEX_COLORS
    THEME_AVAILABLE = True
except ImportError:
    THEME_AVAILABLE = False
"""

APEX_APPLY = """
# 应用Apex主题
if THEME_AVAILABLE:
    apply_apex_theme()
"""

pages_dir = Path("d:/ML/HEAC 0.2/pages")

print("📄 需要更新的页面：\n")

for py_file in pages_dir.glob("*.py"):
    print(f"  - {py_file.name}")

print("\n✅ 已更新的页面：")
print("  - 6_Proxy_Models.py")  
print("  - 10_Database_Manager.py")

print("\n❌ 待更新的页面需要手动添加以下代码：")
print("\n1. 在导入部分添加：")
print(APEX_IMPORT)
print("\n2. 在st.set_page_config()之后添加：")
print(APEX_APPLY)
