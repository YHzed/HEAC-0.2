"""
分析项目中的导入语句，找出重复和优化机会
"""

import os
import re
from collections import Counter, defaultdict
from pathlib import Path

def extract_imports(file_path):
    """提取文件中的所有导入语句"""
    imports = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 匹配 import xxx
                if line.startswith('import '):
                    module = line.replace('import ', '').split(' as ')[0].split(',')[0].strip()
                    imports.append(('import', module))
                # 匹配 from xxx import yyy
                elif line.startswith('from '):
                    match = re.match(r'from\s+([\w\.]+)\s+import\s+(.+)', line)
                    if match:
                        module = match.group(1)
                        items = match.group(2)
                        imports.append(('from', module, items))
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return imports

def analyze_project_imports(root_dir):
    """分析整个项目的导入情况"""
    
    # 统计信息
    all_imports = []
    file_imports = defaultdict(list)
    
    # 需要分析的目录
    target_dirs = ['core', 'pages', 'scripts', 'tests']
    
    for target_dir in target_dirs:
        dir_path = os.path.join(root_dir, target_dir)
        if not os.path.exists(dir_path):
            continue
            
        for root, dirs, files in os.walk(dir_path):
            # 跳过 __pycache__
            if '__pycache__' in root:
                continue
                
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, root_dir)
                    
                    imports = extract_imports(file_path)
                    all_imports.extend(imports)
                    file_imports[rel_path] = imports
    
    return all_imports, file_imports

def print_import_analysis(all_imports, file_imports):
    """打印导入分析结果"""
    
    print("=" * 80)
    print("项目导入分析报告")
    print("=" * 80)
    
    # 1. 统计最常用的标准库
    print("\n1. 标准库导入频率 TOP 10:")
    print("-" * 80)
    
    stdlib_modules = [
        'os', 'sys', 'json', 'math', 'datetime', 'time', 'pathlib', 're',
        'io', 'typing', 'dataclasses', 'collections', 'functools', 'itertools'
    ]
    
    import_counter = Counter()
    for imp in all_imports:
        if imp[0] == 'import':
            module = imp[1].split('.')[0]
            import_counter[module] += 1
        else:  # from import
            module = imp[1].split('.')[0]
            import_counter[module] += 1
    
    stdlib_count = {k: v for k, v in import_counter.items() if k in stdlib_modules}
    for module, count in sorted(stdlib_count.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {module:20s} : {count:3d} 次")
    
    # 2. 统计第三方库
    print("\n2. 第三方库导入频率:")
    print("-" * 80)
    
    third_party = [
        'pandas', 'numpy', 'streamlit', 'plotly', 'sklearn', 'optuna',
        'joblib', 'pymatgen', 'mp_api', 'emmet'
    ]
    
    third_party_count = {k: v for k, v in import_counter.items() if k in third_party}
    for module, count in sorted(third_party_count.items(), key=lambda x: x[1], reverse=True):
        print(f"  {module:20s} : {count:3d} 次")
    
    # 3. 统计core模块导入
    print("\n3. core模块内部导入频率:")
    print("-" * 80)
    
    core_imports = defaultdict(int)
    for imp in all_imports:
        if imp[0] == 'from' and imp[1].startswith('core.'):
            module = imp[1]
            core_imports[module] += 1
    
    for module, count in sorted(core_imports.items(), key=lambda x: x[1], reverse=True):
        print(f"  {module:40s} : {count:3d} 次")
    
    # 4. 按文件类别分析
    print("\n4. 各目录导入统计:")
    print("-" * 80)
    
    dir_stats = defaultdict(lambda: {'files': 0, 'imports': 0})
    for file_path, imports in file_imports.items():
        dir_name = file_path.split(os.sep)[0]
        dir_stats[dir_name]['files'] += 1
        dir_stats[dir_name]['imports'] += len(imports)
    
    for dir_name, stats in sorted(dir_stats.items()):
        avg = stats['imports'] / stats['files'] if stats['files'] > 0 else 0
        print(f"  {dir_name:15s} : {stats['files']:2d} 文件, {stats['imports']:3d} 导入, 平均 {avg:.1f}/文件")
    
    # 5. 重复导入检测
    print("\n5. 重复导入模式分析:")
    print("-" * 80)
    
    # 检查pages目录中的重复导入
    pages_imports = defaultdict(list)
    for file_path, imports in file_imports.items():
        if file_path.startswith('pages'):
            for imp in imports:
                if imp[0] == 'import':
                    pages_imports[imp[1]].append(file_path)
                else:
                    pages_imports[imp[1]].append(file_path)
    
    print("\n  Pages目录中被多个文件导入的模块:")
    for module, files in sorted(pages_imports.items(), key=lambda x: len(x[1]), reverse=True):
        if len(files) > 2:  # 至少3个文件使用
            print(f"    {module:30s} : {len(files)} 文件使用")
    
    # 6. 可优化的导入建议
    print("\n6. 优化建议:")
    print("-" * 80)
    
    suggestions = []
    
    # streamlit在多个pages中使用
    if import_counter.get('streamlit', 0) > 3:
        suggestions.append("✓ streamlit 在多个页面中使用，可以考虑统一配置")
    
    # pandas在多处使用
    if import_counter.get('pandas', 0) > 3:
        suggestions.append("✓ pandas 使用频繁，建议在core/__init__.py统一导入常用功能")
    
    # core模块导入不统一
    if len(core_imports) > 10:
        suggestions.append("✓ core模块导入较为分散，建议完善core/__init__.py导出接口")
    
    # sklearn导入分散
    sklearn_imports = [k for k in import_counter.keys() if k == 'sklearn']
    if sklearn_imports:
        suggestions.append("✓ sklearn子模块导入分散，可以在core/models.py统一管理")
    
    for suggestion in suggestions:
        print(f"  {suggestion}")
    
    print("\n" + "=" * 80)
    print(f"总计分析: {len(file_imports)} 个文件, {len(all_imports)} 个导入语句")
    print("=" * 80)

if __name__ == '__main__':
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    all_imports, file_imports = analyze_project_imports(project_root)
    print_import_analysis(all_imports, file_imports)
