"""
Materials Project数据下载脚本 - 专用于Proxy模型升级

目标:
- 下载WC-Co体系及相关材料的真实物理数据
- 用于重训formation_energy, lattice_param等Proxy模型

使用:
    python scripts/download_mp_proxy_data.py
    
作者: HEAC Proxy模型升级
日期: 2026-01-21
"""

import sys
import os
from pathlib import Path
import pandas as pd
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mp_api.client import MPRester
from core.config import config

print("=" * 80)
print("🌐 Materials Project数据下载 - Proxy模型升级")
print("=" * 80)

# 验证API key
if not config.MP_API_KEY:
    print("❌ 错误: MP_API_KEY未配置")
    print("请在.env文件中设置MP_API_KEY")
    sys.exit(1)

print(f"✅ API Key已配置: {config.MP_API_KEY[:10]}...")

# 初始化MPRester
mpr = MPRester(config.MP_API_KEY)

# 定义目标材料体系
target_systems = {
    'ceramics': {
        'WC': ['W', 'C'],
        'TiC': ['Ti', 'C'],
        'VC': ['V', 'C'],
        'NbC': ['Nb', 'C'],
        'TaC': ['Ta', 'C'],
        'Cr3C2': ['Cr', 'C'],
        'TiN': ['Ti', 'N'],
        'TiCN': ['Ti', 'C', 'N']
    },
    'binders': {
        'Co': ['Co'],
        'Ni': ['Ni'],
        'Fe': ['Fe'],
        'CoCr': ['Co', 'Cr'],
        'CoNi': ['Co', 'Ni'],
        'NiFe': ['Ni', 'Fe'],
        'FeCoNi': ['Fe', 'Co', 'Ni']
    }
}

# 需要的字段
fields = [
    "material_id",
    "formula_pretty",
    "composition",
    "nelements",
    "nsites",
    "volume",
    "density",
    "formation_energy_per_atom",
    "energy_above_hull",
    "is_stable",
    "band_gap",
    "efermi",
    "total_magnetization",
    "structure"
]

print("\n[1/5] 下载陶瓷相材料数据...")
ceramic_data = []

for name, elements in target_systems['ceramics'].items():
    print(f"   查询 {name} ({elements})...", end='')
    
    try:
        results = mpr.materials.summary.search(
            elements=elements,
            fields=fields,
            num_chunks=1
        )
        
        for mat in results:
            ceramic_data.append({
                'material_id': mat.material_id,
                'formula': mat.formula_pretty,
                'system': name,
                'type': 'ceramic',
                'nelements': mat.nelements,
                'volume': mat.volume,
                'density': mat.density,
                'formation_energy_per_atom': mat.formation_energy_per_atom,
                'energy_above_hull': mat.energy_above_hull,
                'is_stable': mat.is_stable,
                'band_gap': mat.band_gap if hasattr(mat, 'band_gap') else None,
                'efermi': mat.efermi if hasattr(mat, 'efermi') else None,
                'magnetization': mat.total_magnetization if hasattr(mat, 'total_magnetization') else None
            })
        
        print(f" 找到{len(results)}条")
    except Exception as e:
        print(f" 错误: {str(e)[:50]}")

print(f"\n   陶瓷相总计: {len(ceramic_data)}条")

print("\n[2/5] 下载粘结相材料数据...")
binder_data = []

for name, elements in target_systems['binders'].items():
    print(f"   查询 {name} ({elements})...", end='')
    
    try:
        results = mpr.materials.summary.search(
            elements=elements,
            fields=fields,
            num_chunks=1
        )
        
        for mat in results:
            binder_data.append({
                'material_id': mat.material_id,
                'formula': mat.formula_pretty,
                'system': name,
                'type': 'binder',
                'nelements': mat.nelements,
                'volume': mat.volume,
                'density': mat.density,
                'formation_energy_per_atom': mat.formation_energy_per_atom,
                'energy_above_hull': mat.energy_above_hull,
                'is_stable': mat.is_stable,
                'band_gap': mat.band_gap if hasattr(mat, 'band_gap') else None,
                'efermi': mat.efermi if hasattr(mat, 'efermi') else None,
                'magnetization': mat.total_magnetization if hasattr(mat, 'total_magnetization') else None
            })
        
        print(f" 找到{len(results)}条")
    except Exception as e:
        print(f" 错误: {str(e)[:50]}")

print(f"\n   粘结相总计: {len(binder_data)}条")

print("\n[3/5] 下载弹性常数数据...")
elastic_data = []

# 查询具有弹性数据的材料
print("   查询陶瓷相弹性常数...")
try:
    # WC, TiC等典型陶瓷相
    for name, elements in list(target_systems['ceramics'].items())[:3]:  # 限制数量避免超时
        results = mpr.materials.elasticity.search(
            elements=elements,
            num_chunks=1
        )
        
        for mat in results:
            if hasattr(mat, 'homogeneous_poisson'):
                elastic_data.append({
                    'material_id': mat.material_id,
                    'type': 'ceramic',
                    'bulk_modulus': mat.k_vrh if hasattr(mat, 'k_vrh') else None,
                    'shear_modulus': mat.g_vrh if hasattr(mat, 'g_vrh') else None,
                    'poisson_ratio': mat.homogeneous_poisson,
                    'youngs_modulus': mat.universal_youngs_modulus if hasattr(mat, 'universal_youngs_modulus') else None
                })
        
        print(f"   {name}: {len([e for e in elastic_data if e['type']=='ceramic'])}条")
except Exception as e:
    print(f"   弹性数据查询错误: {str(e)[:100]}")

print(f"\n   弹性常数总计: {len(elastic_data)}条")

# 合并数据
print("\n[4/5]合并并保存数据...")
all_data = ceramic_data + binder_data

df = pd.DataFrame(all_data)
df_elastic = pd.DataFrame(elastic_data) if elastic_data else pd.DataFrame()

# 保存
output_dir = Path('datasets/mp_proxy_data')
output_dir.mkdir(parents=True, exist_ok=True)

df.to_csv(output_dir / 'mp_materials_data.csv', index=False)
if not df_elastic.empty:
    df_elastic.to_csv(output_dir / 'mp_elastic_data.csv', index=False)

# 保存元数据
metadata = {
    'download_date': datetime.now().isoformat(),
    'total_materials': len(df),
    'total_elastic': len(df_elastic),
    'ceramic_count': len(ceramic_data),
    'binder_count': len(binder_data),
    'target_systems': target_systems,
    'fields_downloaded': fields
}

with open(output_dir / 'metadata.json', 'w', encoding='utf-8') as f:
    json.dump(metadata, f, indent=2, ensure_ascii=False)

print(f"   ✅ 材料数据: {output_dir / 'mp_materials_data.csv'}")
if not df_elastic.empty:
    print(f"   ✅ 弹性数据: {output_dir / 'mp_elastic_data.csv'}")
print(f"   ✅ 元数据: {output_dir / 'metadata.json'}")

# 数据质量检查
print("\n[5/5] 数据质量检查...")
print(f"   总样本数: {len(df)}")
print(f"   陶瓷相: {len(ceramic_data)}")
print(f"   粘结相: {len(binder_data)}")

if len(df) > 0:
    # Formation energy统计
    fe_valid = df[df['formation_energy_per_atom'].notna()]
    fe_negative = fe_valid[fe_valid['formation_energy_per_atom'] < 0]
    
    print(f"\n   Formation Energy:")
    print(f"      有效样本: {len(fe_valid)}")
    print(f"      负值样本: {len(fe_negative)} ({len(fe_negative)/len(fe_valid)*100:.1f}%)")
    print(f"      均值: {fe_valid['formation_energy_per_atom'].mean():.3f} eV/atom")
    
    # Stability统计
    stable = df[df['is_stable'] == True]
    print(f"\n   Stability:")
    print(f"      稳定相: {len(stable)} ({len(stable)/len(df)*100:.1f}%)")
    
    # Magnetization统计
    mag_valid = df[df['magnetization'].notna()]
    print(f"\n   Magnetization:")
    print(f"      有效样本: {len(mag_valid)}")
    if len(mag_valid) > 0:
        print(f"      均值: {mag_valid['magnetization'].abs().mean():.2f} μB")

if not df_elastic.empty:
    print(f"\n   Elastic Moduli:")
    print(f"      有效样本: {len(df_elastic)}")
    bm_valid = df_elastic[df_elastic['bulk_modulus'].notna()]
    sm_valid = df_elastic[df_elastic['shear_modulus'].notna()]
    if len(bm_valid) > 0:
        print(f"      体模量均值: {bm_valid['bulk_modulus'].mean():.1f} GPa")
    if len(sm_valid) > 0:
        print(f"      剪切模量均值: {sm_valid['shear_modulus'].mean():.1f} GPa")

print("\n" + "=" * 80)
print("✅ 数据下载完成！")
print("=" * 80)
print(f"\n下一步:")
print(f"  1. 查看数据: {output_dir / 'mp_materials_data.csv'}")
print(f"  2. 数据预处理和特征工程")
print(f"  3. 重训Proxy模型")
print("=" * 80)
