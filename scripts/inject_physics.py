# -*- coding: utf-8 -*-
"""
物理特征注入脚本 (Feature Injection)

将辅助模型的预测智慧注入到实验数据中，生成高级物理特征

功能：
1. 加载实验数据
2. 提取粘结相成分
3. 调用辅助模型预测物理属性
4. 计算衍生特征（晶格失配、稳定性指标等）
5. 生成增强数据集

Author: HEAC Team
Date: 2025-12-18
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import joblib

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.feature_injector import FeatureInjector
from core.data_standardizer import standardize_dataframe

# 常量定义
WC_LATTICE_A = 2.906  # WC晶格常数 (Å)

def inject_physics_features(
    input_csv: str,
    output_csv: str = None,
    comp_col: str = 'binder_composition',
    model_dir: str = 'models/proxy_models'
):
    """
    物理特征注入主函数
    
    Args:
        input_csv: 输入CSV文件路径
        output_csv: 输出CSV文件路径（默认自动生成）
        comp_col: 成分列名
        model_dir: 模型目录
        
    Returns:
        增强后的DataFrame
    """
    print("=" * 80)
    print("物理特征注入系统 (Physics Feature Injection)")
    print("=" * 80)
    
    # 1. 加载数据
    print(f"\n[Step 1/5] 加载数据: {input_csv}")
    df = pd.read_csv(input_csv)
    print(f"原始数据: {df.shape[0]} 行 × {df.shape[1]} 列")
    
    # 数据标准化
    print("\n[Step 2/5] 数据标准化...")
    df_std = standardize_dataframe(df, merge_duplicates=True, validate_types=True)
    
    # 检查成分列
    if comp_col not in df_std.columns:
        print(f"\n[ERROR] 未找到成分列: {comp_col}")
        print(f"可用列: {df_std.columns.tolist()}")
        return None
    
    print(f"成分列: {comp_col}")
    print(f"有效成分数: {df_std[comp_col].notna().sum()}")
    
    # 2. 特征注入
    print("\n[Step 3/5] 调用辅助模型预测物理属性...")
    injector = FeatureInjector(model_dir=model_dir)
    
    df_enhanced = injector.inject_features(
        df_std,
        comp_col=comp_col,
        verbose=True
    )
    
    # 3. 计算衍生特征
    print("\n[Step 4/5] 计算衍生物理特征...")
    
    # A. 晶格常数估算 (FCC假设)
    if 'pred_lattice_param' in df_enhanced.columns:
        # pred_lattice_param 是 volume_per_atom
        # FCC: a = (4 * V_atom)^(1/3)
        df_enhanced['calc_lattice_constant_fcc'] = (
            4 * df_enhanced['pred_lattice_param']
        ) ** (1/3)
        
        print(f"  ✓ 晶格常数 (FCC) 计算完成")
    
    # B. 晶格失配度 (已包含在lattice_mismatch_wc中)
    if 'lattice_mismatch_wc' in df_enhanced.columns:
        print(f"  ✓ 晶格失配 vs WC 已计算")
    
    # C. 磁稳定性指标
    if 'pred_magnetic_moment' in df_enhanced.columns:
        df_enhanced['calc_mag_instability'] = df_enhanced['pred_magnetic_moment'].abs()
        
        # 分类
        df_enhanced['mag_category'] = pd.cut(
            df_enhanced['calc_mag_instability'],
            bins=[0, 0.5, 2, np.inf],
            labels=['Low', 'Medium', 'High']
        )
        
        print(f"  ✓ 磁稳定性分类完成")
    
    # D. 稳定性等级（基于形成能）
    if 'pred_formation_energy' in df_enhanced.columns:
        df_enhanced['stability_grade'] = pd.cut(
            df_enhanced['pred_formation_energy'],
            bins=[-np.inf, -0.1, 0, 0.1, np.inf],
            labels=['Excellent', 'Good', 'Fair', 'Poor']
        )
        
        print(f"  ✓ 稳定性等级划分完成")
    
    # E. 韧脆性判据（如果有Pugh比）
    if 'pred_pugh_ratio' in df_enhanced.columns:
        df_enhanced['ductility'] = df_enhanced['pred_pugh_ratio'].apply(
            lambda x: 'Ductile' if x > 1.75 else 'Brittle' if pd.notna(x) else None
        )
        
        print(f"  ✓ 韧脆性判据完成")
    
    # 4. 特征统计
    print("\n[Step 5/5] 特征统计汇总...")
    
    new_features = [col for col in df_enhanced.columns 
                   if col.startswith('pred_') or col.startswith('calc_') 
                   or col in ['lattice_mismatch_wc', 'stability_grade', 'mag_category', 'ductility']]
    
    print(f"\n新增特征数量: {len(new_features)}")
    print("新增特征列表:")
    for i, feat in enumerate(new_features, 1):
        print(f"  {i:2d}. {feat}")
    
    # 数值特征统计
    numeric_new = [col for col in new_features if df_enhanced[col].dtype in [np.float64, np.int64]]
    if numeric_new:
        print("\n数值特征统计:")
        stats = df_enhanced[numeric_new].describe()
        print(stats.to_string())
    
    # 5. 保存
    if output_csv is None:
        input_path = Path(input_csv)
        output_csv = str(input_path.parent / f"{input_path.stem}_physics_enhanced.csv")
    
    df_enhanced.to_csv(output_csv, index=False)
    
    print("\n" + "=" * 80)
    print(f"✅ 完成！增强数据已保存: {output_csv}")
    print("=" * 80)
    print(f"\n最终数据: {df_enhanced.shape[0]} 行 × {df_enhanced.shape[1]} 列")
    
    return df_enhanced


def filter_by_stability(df, ef_threshold=-0.05):
    """
    第一层过滤：稳定性筛选
    
    Args:
        df: DataFrame
        ef_threshold: 形成能阈值 (eV/atom)
        
    Returns:
        过滤后的DataFrame
    """
    if 'pred_formation_energy' not in df.columns:
        print("[WARNING] 无法进行稳定性过滤：缺少pred_formation_energy列")
        return df
    
    mask = df['pred_formation_energy'] < ef_threshold
    df_filtered = df[mask].copy()
    
    print(f"\n[Filter 1: Stability]")
    print(f"  阈值: Ef < {ef_threshold} eV/atom")
    print(f"  原始: {len(df)} 样本")
    print(f"  保留: {len(df_filtered)} 样本 ({len(df_filtered)/len(df)*100:.1f}%)")
    print(f"  淘汰: {len(df) - len(df_filtered)} 样本")
    
    return df_filtered


def filter_by_interface(df, mismatch_threshold=0.05):
    """
    第二层过滤：界面匹配筛选
    
    Args:
        df: DataFrame
        mismatch_threshold: 晶格失配阈值
        
    Returns:
        过滤后的DataFrame
    """
    if 'lattice_mismatch_wc' not in df.columns:
        print("[WARNING] 无法进行界面过滤：缺少lattice_mismatch_wc列")
        return df
    
    mask = df['lattice_mismatch_wc'].abs() < mismatch_threshold
    df_filtered = df[mask].copy()
    
    print(f"\n[Filter 2: Interface]")
    print(f"  阈值: |Mismatch| < {mismatch_threshold}")
    print(f"  原始: {len(df)} 样本")
    print(f"  保留: {len(df_filtered)} 样本 ({len(df_filtered)/len(df)*100:.1f}%)")
    print(f"  淘汰: {len(df) - len(df_filtered)} 样本")
    
    return df_filtered


def rank_by_hardness(df, hardness_col='hardness', top_n=20):
    """
    第三层：按硬度排序
    
    Args:
        df: DataFrame
        hardness_col: 硬度列名
        top_n: 返回Top N
        
    Returns:
        排序后的DataFrame
    """
    if hardness_col not in df.columns:
        print(f"[WARNING] 未找到硬度列: {hardness_col}")
        return df
    
    df_sorted = df.sort_values(hardness_col, ascending=False).head(top_n)
    
    print(f"\n[Ranking: Top {top_n} by Hardness]")
    print(df_sorted[[hardness_col, 'pred_formation_energy', 'lattice_mismatch_wc']].to_string(index=False))
    
    return df_sorted


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='物理特征注入')
    parser.add_argument('input', help='输入CSV文件')
    parser.add_argument('--output', help='输出CSV文件')
    parser.add_argument('--comp-col', default='binder_composition', help='成分列名')
    parser.add_argument('--model-dir', default='models/proxy_models', help='模型目录')
    parser.add_argument('--filter', action='store_true', help='应用多级过滤')
    
    args = parser.parse_args()
    
    # 注入特征
    df_enhanced = inject_physics_features(
        args.input,
        args.output,
        args.comp_col,
        args.model_dir
    )
    
    # 可选：多级过滤演示
    if args.filter and df_enhanced is not None:
        print("\n" + "=" * 80)
        print("应用多级筛选漏斗 (Multi-level Filtering Funnel)")
        print("=" * 80)
        
        df_filtered = filter_by_stability(df_enhanced, ef_threshold=-0.05)
        df_filtered = filter_by_interface(df_filtered, mismatch_threshold=0.05)
        
        if 'hardness' in df_filtered.columns:
            df_top = rank_by_hardness(df_filtered, 'hardness', top_n=20)
