# -*- coding: utf-8 -*-
"""
测试晶格失配度动态计算

验证不同陶瓷相的失配度计算是否正确
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.feature_injector import FeatureInjector

def test_ceramic_mismatch_calculation():
    """测试不同陶瓷相的失配度计算"""
    
    print("=" * 80)
    print("晶格失配度动态计算测试")
    print("=" * 80)
    
    # 初始化
    injector = FeatureInjector(model_dir='models/proxy_models')
    
    # 假设FCC粘结相晶格常数
    lattice_fcc = 3.6  # Å (典型的Co/Ni/Fe基FCC高熵合金)
    fcc_neighbor = lattice_fcc / (2 ** 0.5)  # 2.546 Å
    
    print(f"\n假设FCC粘结相:")
    print(f"  晶格常数: {lattice_fcc:.4f} Å")
    print(f"  最近邻距离: {fcc_neighbor:.4f} Å")
    
    # 测试不同陶瓷相
    ceramic_types = ['WC', 'TiC', 'TiN', 'Ti(C,N)', 'TiCN', 'VC', 'NbC', 'Cr3C2']
    
    print("\n" + "=" * 80)
    print("各陶瓷相的失配度计算结果")
    print("=" * 80)
    print(f"{'陶瓷相':<10} {'结构':<15} {'dNN(Å)':<10} {'失配度':<12} {'失配度(%)':<10}")
    print("-" * 80)
    
    results = []
    for ceramic in ceramic_types:
        try:
            mismatch = injector.calculate_lattice_mismatch(lattice_fcc, ceramic)
            
            # 获取陶瓷相参数
            if ceramic in injector.CERAMIC_PARAMS:
                params = injector.CERAMIC_PARAMS[ceramic]
            else:
                params = injector.CERAMIC_PARAMS.get('WC')
            
            print(f"{ceramic:<10} {params['structure']:<15} "
                  f"{params['neighbor_distance']:<10.4f} "
                  f"{mismatch:<12.4f} {mismatch*100:<10.2f}")
            
            results.append({
                'ceramic': ceramic,
                'structure': params['structure'],
                'neighbor_distance': params['neighbor_distance'],
                'mismatch': mismatch,
                'mismatch_pct': mismatch * 100
            })
        except Exception as e:
            print(f"{ceramic:<10} ERROR: {e}")
    
    # 验证结果
    print("\n" + "=" * 80)
    print("验证结果")
    print("=" * 80)
    
    # 1. WC应该与原来的计算一致
    wc_mismatch = [r for r in results if r['ceramic'] == 'WC'][0]['mismatch']
    expected_wc = abs(fcc_neighbor - 2.906) / 2.906
    if abs(wc_mismatch - expected_wc) < 0.0001:
        print("✅ WC失配度计算正确（与原算法一致）")
    else:
        print(f"❌ WC失配度计算错误：{wc_mismatch:.4f} vs 预期{expected_wc:.4f}")
    
    # 2. 不同陶瓷相的失配度应该不同
    mismatches = [r['mismatch'] for r in results]
    if len(set([round(m, 4) for m in mismatches])) > 1:
        print("✅ 不同陶瓷相的失配度不同（动态计算成功）")
    else:
        print("❌ 所有陶瓷相的失配度相同（动态计算失败）")
    
    # 3. 失配度范围合理性检查
    if all(0 <= m <= 0.5 for m in mismatches):
        print("✅ 所有失配度在合理范围内 (0-50%)")
    else:
        print("⚠️  部分失配度超出常见范围")
    
    return results


def test_inject_features_with_ceramic_types():
    """测试inject_features方法的ceramic_type支持"""
    
    print("\n\n" + "=" * 80)
    print("测试inject_features方法（多种陶瓷相）")
    print("=" * 80)
    
    # 创建测试数据
    df_test = pd.DataFrame({
        'Ceramic_Type': ['WC', 'TiC', 'TiN', 'Ti(C,N)', 'VC'],
        'binder_composition': ['CoCrFeNi'] * 5
    })
    
    print("\n测试数据:")
    print(df_test)
    
    # 特征注入
    try:
        injector = FeatureInjector(model_dir='models/proxy_models')
        df_result = injector.inject_features(
            df_test,
            comp_col='binder_composition',
            ceramic_type_col='Ceramic_Type',
            verbose=True
        )
        
        print("\n\n注入结果:")
        print(df_result[['Ceramic_Type', 'pred_lattice_param', 'lattice_mismatch_wc']])
        
        # 验证
        print("\n" + "=" * 80)
        print("验证结果")
        print("=" * 80)
        
        # 检查失配度是否不同
        mismatches = df_result['lattice_mismatch_wc'].dropna().values
        if len(set([round(m, 4) for m in mismatches])) > 1:
            print("✅ 不同陶瓷相的失配度不同")
        else:
            print("❌ 所有失配度相同（可能未正确读取Ceramic_Type）")
        
        # 显示每种陶瓷相的失配度
        print("\n各陶瓷相的失配度:")
        for idx, row in df_result.iterrows():
            print(f"  {row['Ceramic_Type']}: {row['lattice_mismatch_wc']:.4f} ({row['lattice_mismatch_wc']*100:.2f}%)")
        
        return df_result
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_unknown_ceramic_type():
    """测试未知陶瓷类型的回退机制"""
    
    print("\n\n" + "=" * 80)
    print("测试未知陶瓷类型回退机制")
    print("=" * 80)
    
    injector = FeatureInjector(model_dir='models/proxy_models')
    lattice_fcc = 3.6
    
    # 测试未知类型
    unknown_types = ['Unknown', 'SiC', 'AlN', '']
    
    for ceramic in unknown_types:
        print(f"\n测试陶瓷类型: '{ceramic}'")
        mismatch = injector.calculate_lattice_mismatch(lattice_fcc, ceramic)
        print(f"  失配度: {mismatch:.4f} ({mismatch*100:.2f}%)")
        
        # 应该回退到WC
        wc_mismatch = injector.calculate_lattice_mismatch(lattice_fcc, 'WC')
        if abs(mismatch - wc_mismatch) < 0.0001:
            print(f"  ✅ 正确回退到WC")
        else:
            print(f"  ⚠️  未回退到WC (WC失配度: {wc_mismatch:.4f})")


if __name__ == "__main__":
    # 测试1: 基本失配度计算
    results = test_ceramic_mismatch_calculation()
    
    # 测试2: inject_features方法
    df_result = test_inject_features_with_ceramic_types()
    
    # 测试3: 未知类型回退
    test_unknown_ceramic_type()
    
    print("\n\n" + "=" * 80)
    print("✅ 所有测试完成！")
    print("=" * 80)
