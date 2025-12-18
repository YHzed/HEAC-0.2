# -*- coding: utf-8 -*-
"""
虚拟高通量筛选 (Virtual High-Throughput Screening)

多级漏斗筛选策略，从大量虚拟配方中筛选最优候选

三级筛选漏斗：
1. 稳定性过滤 (Stability Filter) - 淘汰80%
2. 界面匹配过滤 (Interface Filter) - 优选韧性潜力
3. 硬度排序 (Hardness Ranking) - Top 20

Author: HEAC Team
Date: 2025-12-18
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import joblib
from itertools import product

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.feature_injector import FeatureInjector
from scripts.inject_physics import filter_by_stability, filter_by_interface

# 元素范围定义
ELEMENT_SPACE = {
    'Co': (0, 80),  # 0-80 wt%
    'Cr': (0, 30),
    'Ni': (0, 40),
    'Fe': (0, 20),
    'W': (0, 10),
    'Mo': (0, 10),
    'Ti': (0, 5)
}

WC_CONTENT_RANGE = (85, 95)  # WC content: 85-95%

def generate_virtual_recipes(n_samples=100000, seed=42):
    """
    生成虚拟HEA配方
    
    Args:
        n_samples: 生成数量
        seed: 随机种子
        
    Returns:
        DataFrame with virtual recipes
    """
    np.random.seed(seed)
    
    print(f"\n[Generation] 生成 {n_samples:,} 个虚拟配方...")
    
    recipes = []
    elements = list(ELEMENT_SPACE.keys())
    
    for i in range(n_samples):
        # 随机生成成分
        composition = {}
        for elem, (min_val, max_val) in ELEMENT_SPACE.items():
            composition[elem] = np.random.uniform(min_val, max_val)
        
        # 归一化到100%
        total = sum(composition.values())
        if total > 0:
            composition = {k: v/total*100 for k, v in composition.items()}
        else:
            continue
        
        # 生成配方字符串
        comp_str = ''.join([f"{elem}{comp:.1f}" for elem, comp in composition.items() if comp > 0.1])
        
        # WC含量
        wc_content = np.random.uniform(*WC_CONTENT_RANGE)
        
        # 工艺参数（随机）
        sinter_temp = np.random.uniform(1350, 1450)
        grain_size = np.random.uniform(0.5, 2.0)
        
        recipes.append({
            'recipe_id': f'VR_{i:06d}',
            'binder_composition': comp_str,
            'wc_content': wc_content,
            'sinter_temp': sinter_temp,
            'grain_size': grain_size,
            **composition  # 添加各元素含量
        })
    
    df = pd.DataFrame(recipes)
    
    print(f"  ✓ 成功生成 {len(df):,} 个配方")
    print(f"  平均元素数: {(df[elements] > 0.1).sum(axis=1).mean():.1f}")
    
    return df


def virtual_screening_funnel(
    n_generate=100000,
    ef_threshold=-0.05,
    mismatch_threshold=0.05,
    top_n=20,
    hardness_model_path=None,
    model_dir='models/proxy_models'
):
    """
    虚拟筛选漏斗主函数
    
    Args:
        n_generate: 生成配方数量
        ef_threshold: 形成能阈值
        mismatch_threshold: 晶格失配阈值
        top_n: 最终返回Top N
        hardness_model_path: 硬度预测模型路径
        model_dir: 辅助模型目录
        
    Returns:
        筛选后的Top N配方
    """
    print("=" * 80)
    print("虚拟高通量筛选系统")
    print("Multi-Level Filtering Funnel for Virtual HEA Screening")
    print("=" * 80)
    
    # 阶段1: 生成
    df_virtual = generate_virtual_recipes(n_samples=n_generate)
    
    print(f"\n{'='*80}")
    print(f"原始池: {len(df_virtual):,} 个虚拟配方")
    print(f"{'='*80}")
    
    # 阶段2: 特征注入
    print(f"\n[Injection] 调用辅助模型预测物理属性...")
    injector = FeatureInjector(model_dir=model_dir)
    
    print("  处理中...（这可能需要几分钟）")
    df_enhanced = injector.inject_features(
        df_virtual,
        comp_col='binder_composition',
        verbose=False
    )
    
    print(f"  ✓ 特征注入完成")
    
    # 阶段3: 多级过滤
    print(f"\n{'='*80}")
    print("开始多级筛选")
    print(f"{'='*80}")
    
    # Filter 1: 稳定性
    df_stable = filter_by_stability(df_enhanced, ef_threshold=ef_threshold)
    
    if len(df_stable) == 0:
        print("\n[ERROR] 所有配方都被稳定性过滤淘汰！请放宽阈值。")
        return None
    
    # Filter 2: 界面匹配
    df_matched = filter_by_interface(df_stable, mismatch_threshold=mismatch_threshold)
    
    if len(df_matched) == 0:
        print("\n[WARNING] 所有配方都被界面过滤淘汰！放宽阈值或返回稳定性通过的配方")
        df_matched = df_stable
    
    # 阶段4: 硬度预测或多指标评分
    print(f"\n[Ranking] 最终排序...")
    
    if hardness_model_path and Path(hardness_model_path).exists():
        # 如果有硬度模型，使用它预测
        print(f"  使用硬度模型: {hardness_model_path}")
        model = joblib.load(hardness_model_path)
        
        # 准备特征 (需要与训练时一致)
        # TODO: 这里需要根据实际模型调整
        print("  [TODO] 硬度预测需要完整的特征工程流程")
        
    else:
        # 否则使用物理指标综合评分
        print(f"  使用物理指标综合评分")
        
        # 评分规则（可调整）
        df_matched['score'] = 0
        
        # 形成能越负越好（-0.2分最佳，0分最差）
        if 'pred_formation_energy' in df_matched.columns:
            df_matched['score'] += -df_matched['pred_formation_energy'] * 10
        
        # 晶格失配越小越好
        if 'lattice_mismatch_wc' in df_matched.columns:
            df_matched['score'] += (1 - df_matched['lattice_mismatch_wc'].abs()) * 10
        
        # Pugh比 > 1.75 (韧性优先)
        if 'pred_pugh_ratio' in df_matched.columns:
            df_matched['score'] += (df_matched['pred_pugh_ratio'] - 1.75).clip(0, 1) * 5
        
        # 磁矩适中最好
        if 'pred_magnetic_moment' in df_matched.columns:
            df_matched['score'] += (1 - (df_matched['pred_magnetic_moment'] / 10).clip(0, 1)) * 3
        
        df_ranked = df_matched.sort_values('score', ascending=False).head(top_n)
    
    # 结果展示
    print(f"\n{'='*80}")
    print(f"筛选完成！最终候选: Top {top_n}")
    print(f"{'='*80}\n")
    
    display_cols = [
        'recipe_id', 'binder_composition', 
        'pred_formation_energy', 'lattice_mismatch_wc', 
        'pred_pugh_ratio'
    ]
    
    if 'score' in df_ranked.columns:
        display_cols.append('score')
    
    available_cols = [col for col in display_cols if col in df_ranked.columns]
    print(df_ranked[available_cols].to_string(index=False))
    
    # 保存结果
    output_path = 'virtual_screening_top_candidates.csv'
    df_ranked.to_csv(output_path, index=False)
    print(f"\n✓ 结果已保存: {output_path}")
    
    return df_ranked


def analyze_funnel_efficiency(df_original, df_final):
    """分析筛选漏斗的效率"""
    print(f"\n{'='*80}")
    print("筛选效率分析")
    print(f"{'='*80}")
    
    print(f"原始池:   {len(df_original):>8,} 配方 (100.0%)")
    print(f"最终池:   {len(df_final):>8,} 配方 ({len(df_final)/len(df_original)*100:>5.2f}%)")
    print(f"筛选率:   {(1 - len(df_final)/len(df_original))*100:>5.1f}% 被淘汰")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='虚拟高通量筛选')
    parser.add_argument('--n-generate', type=int, default=100000, help='生成配方数量')
    parser.add_argument('--ef-threshold', type=float, default=-0.05, help='形成能阈值')
    parser.add_argument('--mismatch-threshold', type=float, default=0.05, help='晶格失配阈值')
    parser.add_argument('--top-n', type=int, default=20, help='返回Top N')
    parser.add_argument('--model-dir', default='models/proxy_models', help='辅助模型目录')
    parser.add_argument('--hardness-model', help='硬度预测模型路径（可选）')
    
    args = parser.parse_args()
    
    # 运行虚拟筛选
    df_top = virtual_screening_funnel(
        n_generate=args.n_generate,
        ef_threshold=args.ef_threshold,
        mismatch_threshold=args.mismatch_threshold,
        top_n=args.top_n,
        hardness_model_path=args.hardness_model,
        model_dir=args.model_dir
    )
    
    print("\n" + "=" * 80)
    print("✅ 虚拟筛选完成！")
    print("=" * 80)
    print("\n下一步建议：")
    print("  1. 检查 virtual_screening_top_candidates.csv")
    print("  2. 分析Top候选的成分特点")
    print("  3. 选择3-5个配方进行实验验证")
