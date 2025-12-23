import pandas as pd
import numpy as np
import re

def parse_composition_string(comp_str):
    """
    解析复杂的成分字符串，分离硬质相和粘结相。
    返回: 
        - binder_dict: 粘结相元素及含量 (归一化前)
        - ceramic_dict: 陶瓷相及含量
        - total_binder_wt: 估算的粘结相总质量分数
    """
    # 1. 预处理：去除 'b ' 前缀，去除多余空格
    comp_str = str(comp_str).strip()
    if comp_str.lower().startswith('b '):
        comp_str = comp_str[2:]
    
    # 2. 定义硬质相列表 (常见碳化物/氮化物)
    # 注意顺序：长的在前面，防止 'TiCN' 被识别为 'TiC'
    hard_phases = [
        'WC', 'TiCN', 'TiC', 'TiN', 'TaC', 'NbC', 'VC', 'Mo2C', 'Cr3C2', 
        'ZrC', 'HfC', 'MoC', 'ZrO2', 'Al2O3' # 包含氧化物
    ]
    
    # 3. 正则提取：匹配 "数字+空格+化学式" 或 "化学式+空格+数字" 或 纯化学式
    # 示例: "17.5 TiN" -> (17.5, TiN)
    # 这是一个简化的解析器，假设格式为 "Num Chem" 或 "Chem Num" 或 "Chem"
    
    # 将字符串按空格分割
    tokens = comp_str.split()
    
    parsed_items = {}
    
    i = 0
    while i < len(tokens):
        item = tokens[i]
        
        # 尝试解析数字
        try:
            val = float(item)
            # 如果是数字，下一个应该是化学式
            if i + 1 < len(tokens):
                chem = tokens[i+1]
                parsed_items[chem] = val
                i += 2
            else:
                i += 1
        except ValueError:
            # 如果不是数字，可能是化学式
            chem = item
            # 检查下一个是不是数字
            val = 1.0 # 默认值
            if i + 1 < len(tokens):
                try:
                    val = float(tokens[i+1])
                    i += 2
                except ValueError:
                    i += 1
            else:
                i += 1
            parsed_items[chem] = val

    # 4. 分类：粘结相 vs 硬质相
    binder_dict = {}
    ceramic_dict = {}
    
    for chem, amount in parsed_items.items():
        # 清洗化学式 (去除括号等)
        chem_clean = re.sub(r'[^a-zA-Z0-9]', '', chem)
        
        # 判断逻辑：
        # 如果在硬质相列表中 -> Ceramic
        # 如果包含 C, N, O 且不是纯金属 -> Ceramic (简单启发式)
        # 否则 -> Binder (金属)
        
        is_ceramic = False
        if any(hp.lower() == chem_clean.lower() for hp in hard_phases):
            is_ceramic = True
        elif ('C' in chem_clean or 'N' in chem_clean or 'O' in chem_clean) and len(chem_clean) > 2:
             # 简单的判断：含C/N/O通常是硬质相，除非是 Co, Ni 等单元素
             # 排除 Co, Cr, Cu 等
             if chem_clean not in ['Co', 'Cr', 'Cu', 'Ni', 'Fe', 'Mo', 'W', 'Ti', 'Al', 'Nb', 'Ta', 'Re', 'Mn']:
                 is_ceramic = True
        
        if is_ceramic:
            ceramic_dict[chem_clean] = amount
        else:
            binder_dict[chem_clean] = amount
            
    # 计算总质量
    total_wt = sum(binder_dict.values()) + sum(ceramic_dict.values())
    
    # 估算粘结相质量分数 (如果总和接近100，直接用；否则归一化)
    binder_wt_pct = 0.0
    if total_wt > 0:
        binder_wt_pct = (sum(binder_dict.values()) / total_wt) * 100
        
    return binder_dict, ceramic_dict, binder_wt_pct

def generate_binder_formula(binder_dict):
    """将 {'Co': 10, 'Ni': 20} 转换为 'Co1Ni2' 格式"""
    if not binder_dict:
        return None
    
    # 归一化为原子比或质量比 (Matminer不挑剔，只要有比例即可)
    # 这里直接拼接
    formula = ""
    for el, amt in binder_dict.items():
        formula += f"{el}{amt}"
    return formula

# ==========================================
# 主处理流程
# ==========================================
input_file = "xg.csv" # 您的原始文件名
output_file = "xg_cleaned_for_injection.csv"

df = pd.read_csv(input_file, encoding='utf-8-sig') # 处理可能的BOM

# 1. 清洗列名
df.columns = df.columns.str.strip()

processed_data = []

for idx, row in df.iterrows():
    comp_str = row['Composition']
    
    # 跳过空行
    if pd.isna(comp_str):
        continue
        
    # 解析成分
    binder_elements, ceramic_elements, calc_binder_wt = parse_composition_string(comp_str)
    
    # 如果解析出的粘结相为空 (比如纯WC)，跳过或标记
    if not binder_elements:
        # 尝试看 Binder_vol 列是否有值，如果有，可能成分写得不全
        # 这里做简单处理：如果没有金属粘结相，设为纯 Co (权宜之计) 或跳过
        if 'WC' in str(comp_str):
             binder_elements = {'Co': 0.01} # 极少量，避免报错
        else:
             continue # 无法处理
    
    # 生成 Matminer 可用的粘结相字符串
    binder_formula = generate_binder_formula(binder_elements)
    
    # 获取/填充工艺参数
    # 优先使用 csv 里的 'Binder, vol-%' 如果有的话，没有就用算的 wt%
    # 注意：模型训练用的是 wt% 还是 vol% ? 您之前的模型用了 Binder_Wt_Pct
    # 这里我们优先用 csv 自带的 'Binder, vol-%' 转换为 wt (如果能算)，或者直接用解析出的 calc_binder_wt
    
    # 处理 HV (去除逗号、空格)
    try:
        hv = float(str(row['HV, kgf/mm2']).replace(',', '').strip())
    except:
        hv = np.nan
        
    # 处理 Sinter Temp
    try:
        temp = float(row['T, °C'])
    except:
        temp = 1400.0 # 默认值
        
    # 处理 Grain Size (d, mm -> um)
    # 注意：原表单位是 mm 吗？通常 WC 粒径是 um。
    # 检查数据：0.8, 0.2... 看起来像 um。如果是 mm 就太大了。
    # 假设原表表头写错了，实际是 um。或者如果是 mm，需要 * 1000。
    # 观察数据: "d, mm" 列有 7.1, 6, 0.8... 对于晶粒尺寸，7um 是粗晶，7mm 是不可能的。
    # 但对于试样直径，7mm 是合理的。
    # ！！！重点：请确认 "d, mm" 是晶粒尺寸还是试样尺寸？
    # 根据 "0.8, 0.2" 这种值，这绝对是晶粒尺寸 (um)。
    try:
        grain_size = float(row['d, mm'])
    except:
        grain_size = 1.0 # 默认值
        
    # 构建新行
    new_row = {
        'Binder_Composition': binder_formula,
        'Binder_Wt_Pct': calc_binder_wt, # 使用解析出的质量分数
        'Ceramic_Wt_Pct': 100 - calc_binder_wt,
        'Sinter_Temp_C': temp,
        'Grain_Size_um': grain_size,
        'HV, kgf/mm2': hv,
        'Original_Composition': comp_str # 保留原始字符串备查
    }
    processed_data.append(new_row)

# 2. 创建 DataFrame
df_clean = pd.DataFrame(processed_data)

# 3. 再次清洗
df_clean = df_clean.dropna(subset=['HV, kgf/mm2']) # 去掉没有硬度值的
df_clean = df_clean[df_clean['Binder_Composition'].notnull()]

# 4. 导出
df_clean.to_csv(output_file, index=False)

print(f"处理完成！")
print(f"原始数据: {len(df)} 行")
print(f"清洗后数据: {len(df_clean)} 行")
print(f"已保存至: {output_file}")
print("前5行预览:")
print(df_clean[['Binder_Composition', 'Binder_Wt_Pct', 'HV, kgf/mm2']].head())