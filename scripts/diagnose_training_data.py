"""
诊断训练数据质量

检查Zenodo数据集中各个目标变量的数据质量
"""
import pandas as pd
import sys
from pathlib import Path

# 数据路径
data_path = Path('training data/zenodo/structure_featurized.dat_all.csv')

if not data_path.exists():
    print(f"错误：找不到数据文件 {data_path}")
    print("请确保数据文件存在")
    sys.exit(1)

# 加载数据
print("加载数据...")
df = pd.read_csv(data_path)

print("=" * 80)
print("Zenodo HEA 数据集诊断报告")
print("=" * 80)

print(f"\n📊 数据集基本信息:")
print(f"  总样本数: {len(df)}")
print(f"  总列数: {len(df.columns)}")

# 显示前10列
print(f"\n前10列名:")
for i, col in enumerate(df.columns[:10], 1):
    print(f"  {i:2d}. {col}")
print(f"  ... (还有 {len(df.columns)-10} 列)")

# 检查目标变量
print("\n" + "=" * 80)
print("目标变量诊断")
print("=" * 80)

targets = {
    'formation_energy': [
        'formation_energy', 'e_form', 'delta_e', 'form_energy',
        'formation_energy_per_atom', 'e_above_hull'
    ],
    'lattice': [
        'volume_per_atom', 'lattice_constant', 'a', 'volume',
        'lattice_a', 'lattice_parameter'
    ],
    'magnetic_moment': [
        'magnetic_moment', 'total_magnetization', 'magmom',
        'mag_moment', 'magnetization'
    ],
    'bulk_modulus': [
        'bulk_modulus', 'k_vrh', 'k_voigt', 'k_reuss',
        'bulk_modulus_vrh', 'K_VRH'
    ],
    'shear_modulus': [
        'shear_modulus', 'g_vrh', 'g_voigt', 'g_reuss',
        'shear_modulus_vrh', 'G_VRH'
    ],
    'brittleness': [
        'pugh_ratio', 'b/g', 'brittleness', 'ductility',
        'pugh', 'K/G'
    ]
}

results = {}

for model_name, possible_cols in targets.items():
    print(f"\n{'─'*80}")
    print(f"📌 {model_name.upper()}")
    print(f"{'─'*80}")
    
    found = False
    for col in possible_cols:
        if col in df.columns:
            print(f"✓ 找到列: '{col}'")
            
            # 统计信息
            valid = df[col].notna().sum()
            missing = len(df) - valid
            valid_pct = valid / len(df) * 100
            
            print(f"\n  数据完整性:")
            print(f"    有效值: {valid:5d} / {len(df)} ({valid_pct:5.1f}%)")
            print(f"    缺失值: {missing:5d} ({100-valid_pct:5.1f}%)")
            
            if valid > 0:
                # 数值统计
                col_data = df[col].dropna()
                print(f"\n  数值分布:")
                print(f"    最小值: {col_data.min():10.4f}")
                print(f"    最大值: {col_data.max():10.4f}")
                print(f"    均值:   {col_data.mean():10.4f}")
                print(f"    中位数: {col_data.median():10.4f}")
                print(f"    标准差: {col_data.std():10.4f}")
                
                # 异常值检测（3-sigma）
                mean = col_data.mean()
                std = col_data.std()
                outliers = ((col_data < mean - 3*std) | (col_data > mean + 3*std)).sum()
                print(f"    异常值: {outliers} ({outliers/len(col_data)*100:.1f}%)")
                
                # 判断数据质量
                if valid_pct < 30:
                    quality = "🔴 差 - 缺失值过多"
                elif valid_pct < 70:
                    quality = "🟡 中 - 缺失值较多"
                elif outliers / len(col_data) > 0.1:
                    quality = "🟡 中 - 异常值较多"
                else:
                    quality = "🟢 好"
                
                print(f"\n  数据质量: {quality}")
                
                results[model_name] = {
                    'column': col,
                    'valid_pct': valid_pct,
                    'quality': quality,
                    'found': True
                }
            else:
                print(f"\n  ⚠️ 警告: 所有值都是NaN")
                results[model_name] = {
                    'column': col,
                    'valid_pct': 0,
                    'quality': '🔴 差 - 全部缺失',
                    'found': True
                }
            
            found = True
            break
    
    if not found:
        print(f"✗ 未找到任何相关列")
        print(f"  搜索的列名: {', '.join(possible_cols[:3])}...")
        results[model_name] = {'found': False}

# 总结
print("\n" + "=" * 80)
print("诊断总结")
print("=" * 80)

print(f"\n模型数据可用性:")
for model_name, result in results.items():
    if result.get('found'):
        status = result['quality']
        coverage = result['valid_pct']
        print(f"  {model_name:20s}: {status:20s} (覆盖率: {coverage:5.1f}%)")
    else:
        print(f"  {model_name:20s}: ✗ 数据不存在")

print("\n建议:")
print("─" * 80)
for model_name, result in results.items():
    if not result.get('found'):
        print(f"• {model_name}: 缺少数据，建议禁用此模型")
    elif result['valid_pct'] < 30:
        print(f"• {model_name}: 数据不足，建议从Materials Project补充或禁用")
    elif '差' in result['quality']:
        print(f"• {model_name}: 数据质量差，建议清理后重新训练")
    elif '中' in result['quality']:
        print(f"• {model_name}: 数据质量中等，建议清理异常值和缺失值")
    else:
        print(f"• {model_name}: 数据质量良好，可以正常使用 ✓")

print("\n" + "=" * 80)
print("诊断完成！")
print("=" * 80)
