import pandas as pd
import json

# 加载数据
with open(r'd:\ML\HEAC 0.2\core\data\heac_mp_library.json', encoding='utf-8') as f:
    data = json.load(f)

materials = data['materials']

# 构建测试数据
rows_hea = []
for mid, props in list(materials.items())[:50]:
    row = {
        'ID': mid,
        'Formula': props.get('formula_pretty'),
        'Density': props.get('density'),
        'Structure': props.get('symmetry', {}).get('crystal_system'),
        'Formation E': props.get('formation_energy_per_atom'),
        'Is Stable': props.get('is_stable'),
        'VEC': props.get('vec'),
        'delta': props.get('delta_size_diff'),
        'H_mix': props.get('mixing_enthalpy'),
        'Omega': props.get('omega'),
        'Bulk Modulus': props.get('bulk_modulus'),
        'Shear Modulus': props.get('shear_modulus'),
        'Hv (Est)': props.get('hardness_chen')
    }
    rows_hea.append(row)

df_hea = pd.DataFrame(rows_hea)

print("Before type conversion:")
print(df_hea.dtypes)
print()

# 应用类型转换（与修复后的代码相同）
# 1. 字符串列
string_columns = ['ID', 'Formula', 'Structure']
for col in string_columns:
    if col in df_hea.columns:
        df_hea[col] = df_hea[col].fillna('N/A').astype(str)

# 2. 布尔列
if 'Is Stable' in df_hea.columns:
    df_hea['Is Stable'] = df_hea['Is Stable'].map({True: 'Yes', False: 'No', None: 'Unknown'})

# 3. 数值列
numeric_columns = ['Density', 'Formation E', 'VEC', 'delta', 'H_mix', 'Omega', 
                  'Bulk Modulus', 'Shear Modulus', 'Hv (Est)']
for col in numeric_columns:
    if col in df_hea.columns:
        df_hea[col] = pd.to_numeric(df_hea[col], errors='coerce')

print("After type conversion:")
print(df_hea.dtypes)
print()

print("First 5 rows:")
print(df_hea.head())
print()

# 测试排序
print("Testing sort by ID...")
df_sorted = df_hea.sort_values('ID')
print("✓ Sort successful!")

print("\nTesting sort by Density...")
df_sorted = df_hea.sort_values('Density')
print("✓ Sort successful!")

print("\nAll type conversions working correctly!")
