# 批量修复Tab4缩进的脚本
import sys

# 读取文件
with open('pages/11_Database_Manager_V2.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 找到Tab4的范围 (with tab4: 到 # Tab 5:)
tab4_start = None
tab4_end = None

for i, line in enumerate(lines):
    if 'with tab4:' in line:
        tab4_start = i
    if tab4_start is not None and '# Tab 5:' in line:
        tab4_end = i
        break

if tab4_start is None:
    print("错误: 未找到 'with tab4:'")
    sys.exit(1)

if tab4_end is None:
    print("错误: 未找到Tab5开始")
    sys.exit(1)

print(f"找到Tab4范围: 行 {tab4_start+1} 到 {tab4_end}")

# 修复缩进：为Tab4内容添加4个空格
fixed_lines = lines[:tab4_start+1]  # 保留tab4之前的内容（包括with tab4:）

for i in range(tab4_start + 1, tab4_end):
    line = lines[i]
    # 只为非空行添加4个空格
    if line.strip():  # 非空行
        fixed_lines.append('    ' + line)
    else:  # 空行保持不变
        fixed_lines.append(line)

# 添加Tab5之后的内容
fixed_lines.extend(lines[tab4_end:])

# 写回文件
with open('pages/11_Database_Manager_V2.py', 'w', encoding='utf-8') as f:
    f.writelines(fixed_lines)

print(f"✅ 修复完成！处理了 {tab4_end - tab4_start - 1} 行")
