"""
批量为所有pages添加Apex主题的脚本
"""
import re
from pathlib import Path

# Pages目录
pages_dir = Path("d:/ML/HEAC 0.2/pages")

# Apex主题导入代码
APEX_IMPORT = """# 导入Apex主题
try:
    from ui.apex_theme import apply_apex_theme
    THEME_AVAILABLE = True
except ImportError:
    THEME_AVAILABLE = False

"""

# Apex主题应用代码
APEX_APPLY = """
# 应用Apex主题
if THEME_AVAILABLE:
    apply_apex_theme()
"""

# 已更新的文件
updated_files = ["6_Proxy_Models.py", "10_Database_Manager.py"]

# 需要更新的文件
files_to_update = [
    "1_General_ML_Lab.py",
    "2_HEA_Cermet_Lab.py", 
    "3_Cermet_Library.py",
    "4_Literature_Lab.py",
    "5_Process_Agent.py",
    "6_GBFS_Feature_Selection.py",
    "7_Model_Training.py",
    "8_Virtual_Screening.py",
    "9_HEA_Data_Preprocessing.py"
]

def add_apex_theme(file_path):
    """为Python文件添加Apex主题"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已经有apex_theme导入
        if 'apex_theme' in content or 'apply_apex_theme' in content:
            print(f"  ⏭️  {file_path.name} - 已包含主题代码，跳过")
            return False
        
        # 找到import部分的结束位置
        # 通常在最后一个import或from语句之后
        import_pattern = r'((?:^(?:import|from)\s+.+$\n?)+)'
        match = re.search(import_pattern, content, re.MULTILINE)
        
        if match:
            # 在import部分之后插入Apex导入
            insert_pos = match.end()
            content = content[:insert_pos] + "\n" + APEX_IMPORT + content[insert_pos:]
        else:
            # 如果找不到import，在文件开头插入
            content = APEX_IMPORT + "\n" + content
        
        # 找到st.set_page_config之后插入apply_apex_theme
        config_pattern = r'(st\.set_page_config\([^)]+\))'
        match = re.search(config_pattern, content, re.DOTALL)
        
        if match:
            insert_pos = match.end()
            content = content[:insert_pos] + APEX_APPLY + content[insert_pos:]
        else:
            print(f"  ⚠️  {file_path.name} - 未找到st.set_page_config，请手动添加")
            return False
        
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"  ✅ {file_path.name} - 已成功添加主题")
        return True
        
    except Exception as e:
        print(f"  ❌ {file_path.name} - 错误: {e}")
        return False

print("🎨 开始批量更新Apex主题到所有页面...\n")

success_count = 0
skip_count = 0
fail_count = 0

for filename in files_to_update:
    file_path = pages_dir / filename
    if file_path.exists():
        result = add_apex_theme(file_path)
        if result:
            success_count += 1
        elif 'apex_theme' in open(file_path, 'r', encoding='utf-8').read():
            skip_count += 1
        else:
            fail_count += 1
    else:
        print(f"  ⚠️  {filename} - 文件不存在")
        fail_count += 1

print(f"\n{'='*50}")
print(f"📊 更新完成:")
print(f"  ✅ 成功: {success_count}")
print(f"  ⏭️  跳过: {skip_count + len(updated_files)} (已包含主题)")
print(f"  ❌ 失败: {fail_count}")
print(f"{'='*50}")
print("\n🔄 请刷新浏览器查看所有页面的新主题！")
