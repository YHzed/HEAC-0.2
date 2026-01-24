"""
恢复所有页面到原始状态 - 移除Apex主题
"""
import re
from pathlib import Path

pages_dir = Path("d:/ML/HEAC 0.2/pages")

# 需要处理的文件
all_files = [
    "1_General_ML_Lab.py",
    "2_HEA_Cermet_Lab.py",
    "3_Cermet_Library.py",
    "4_Literature_Lab.py",
    "5_Process_Agent.py",
    "6_GBFS_Feature_Selection.py",
    "6_Proxy_Models.py",
    "7_Model_Training.py",
    "8_Virtual_Screening.py",
    "9_HEA_Data_Preprocessing.py",
    "10_Database_Manager.py"
]

def remove_apex_theme(file_path):
    """移除Apex主题代码"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 移除Apex导入块
        content = re.sub(
            r'# 导入Apex主题\s*\n.*?from ui\.apex_theme.*?\n.*?except ImportError:.*?\n.*?THEME_AVAILABLE = False\s*\n',
            '',
            content,
            flags=re.DOTALL
        )
        
        # 移除apex_theme相关导入
        content = re.sub(
            r'from ui\.apex_theme import.*?\n',
            '',
            content
        )
        
        # 移除dark_theme相关导入
        content = re.sub(
            r'from ui\.dark_theme import.*?\n',
            '',
            content
        )
        
        # 移除主题应用块
        content = re.sub(
            r'\n# 应用Apex主题.*?\n.*?if THEME_AVAILABLE:.*?\n.*?apply_apex_theme\(\).*?\n',
            '',
            content,
            flags=re.DOTALL
        )
        
        content = re.sub(
            r'\n# 应用深色主题.*?\n.*?apply_dark_theme\(\).*?\n',
            '',
            content,
            flags=re.DOTALL
        )
        
        # 移除try-except包裹的apply调用
        content = re.sub(
            r'try:\s*\n\s*apply_(?:apex|dark)_theme\(\)\s*\nexcept:\s*\n\s*pass.*?\n',
            '',
            content,
            flags=re.DOTALL
        )
        
        # 移除create_apex_header等调用，恢复为st.title
        content = re.sub(
            r'create_apex_header\(\s*"([^"]+)",\s*"([^"]*)"\s*\)',
            r'st.title("\1")\nst.markdown("""\2""")',
            content
        )
        
        content = re.sub(
            r'create_dashboard_header\(\s*"([^"]+)",\s*"([^"]*)"\s*\)',
            r'st.title("\1")\nst.markdown("""\2""")',
            content
        )
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✅ {file_path.name} - 已恢复原状")
            return True
        else:
            print(f"  ⏭️  {file_path.name} - 无需修改")
            return False
            
    except Exception as e:
        print(f"  ❌ {file_path.name} - 错误: {e}")
        return False

print("🔄 开始恢复所有页面到原始状态...\n")

success_count = 0
skip_count = 0

# 恢复pages目录下的文件
for filename in all_files:
    file_path = pages_dir / filename
    if file_path.exists():
        if remove_apex_theme(file_path):
            success_count += 1
        else:
            skip_count += 1
    else:
        print(f"  ⚠️  {filename} - 文件不存在")

# 恢复Home.py
home_file = Path("d:/ML/HEAC 0.2/Home.py")
if home_file.exists():
    # 删除Home.py，因为它是新创建的
    home_file.unlink()
    print(f"  ✅ Home.py - 已删除")
    success_count += 1

print(f"\n{'='*50}")
print(f"📊 恢复完成:")
print(f"  ✅ 已恢复: {success_count}")
print(f"  ⏭️  无需修改: {skip_count}")
print(f"{'='*50}")
print("\n✅ 所有页面已恢复到原始状态！")
print("🔄 请刷新浏览器查看")
