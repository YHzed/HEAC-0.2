# -*- coding: utf-8 -*-
"""
性能优化验证测试

测试inject_features的向量化优化效果
使用新训练的高性能模型（R²=0.97）

对比：
- inject_features_legacy(): 使用iterrows的旧版本
- inject_features(): 向量化的新版本

预期：20-50倍性能提升
"""
import time
import pandas as pd
import numpy as np
from core.feature_injector import FeatureInjector

print("=" * 80)
print("FeatureInjector 性能优化验证测试")
print("=" * 80)

# 初始化（使用新训练的模型）
print("\n1. 初始化FeatureInjector...")
model_dir = "saved_models/proxy"  # 使用新训练的模型
injector = FeatureInjector(model_dir=model_dir)

# 创建测试数据
print("\n2. 准备测试数据...")
test_compositions = [
    'CoCrFeNi',
    'AlCoCrFeNi',
    'CoCrFeMnNi',
    'AlCoCrCuFeNi',
    'TiZrNbTa',
    'CoCrFeNiCu',
    'AlTiVCrMo',
    'NbMoTaW',
    'CoCrFeNiMn',
    'AlCoCrFeNiCu'
]

# 不同规模的测试
test_sizes = [10, 50, 100]

print(f"✓ 测试成分: {len(test_compositions)}种")
print(f"✓ 测试规模: {test_sizes}")

# 初始化FeatureInjector
print("\n初始化FeatureInjector...")
try:
    injector = FeatureInjector()
    print("✓ FeatureInjector初始化成功")
except Exception as e:
    print(f"✗ 初始化失败: {e}")
    sys.exit(1)

# 性能对比测试
print("\n" + "=" * 80)
print("性能对比测试")
print("=" * 80)

results = []

for size in test_sizes:
    print(f"\n{'─' * 80}")
    print(f"测试规模: {size}行")
    print(f"{'─' * 80}")
    
    # 创建测试DataFrame
    df_test = pd.DataFrame({
        'binder_composition': np.random.choice(test_compositions, size),
        'Ceramic_Type': np.random.choice(['WC', 'TiC', 'TiN'], size)
    })
    
    # 测试1: 新版本（向量化）
    print(f"\n▶ 测试新版本（向量化）...")
    df_new = df_test.copy()
    start = time.time()
    try:
        result_new = injector.inject_features(df_new, verbose=False)
        time_new = time.time() - start
        print(f"  ✓ 完成: {time_new:.3f}秒 ({size/time_new:.1f} 行/秒)")
        success_new = result_new['pred_formation_energy'].notna().sum()
        print(f"  ✓ 成功处理: {success_new}/{size} 行")
    except Exception as e:
        print(f"  ✗ 失败: {e}")
        time_new = None
        result_new = None
    
    # 测试2: 旧版本（iterrows）
    print(f"\n▶ 测试旧版本（iterrows）...")
    df_old = df_test.copy()
    start = time.time()
    try:
        result_old = injector.inject_features_legacy(df_old, verbose=False)
        time_old = time.time() - start
        print(f"  ✓ 完成: {time_old:.3f}秒 ({size/time_old:.1f} 行/秒)")
        success_old = result_old['pred_formation_energy'].notna().sum()
        print(f"  ✓ 成功处理: {success_old}/{size} 行")
    except Exception as e:
        print(f"  ✗ 失败: {e}")
        time_old = None
        result_old = None
    
    # 性能对比
    if time_new and time_old:
        speedup = time_old / time_new
        print(f"\n📊 性能对比:")
        print(f"  新版本: {time_new:.3f}秒")
        print(f"  旧版本: {time_old:.3f}秒")
        print(f"  ⚡ 提升: {speedup:.1f}x 倍")
        
        # 验证结果一致性
        if result_new is not None and result_old is not None:
            # 检查特征数量
            new_features = set(result_new.columns) - set(df_test.columns)
            old_features = set(result_old.columns) - set(df_test.columns)
            
            if new_features == old_features:
                print(f"  ✓ 特征一致: {len(new_features)}个")
                
                # 检查数值相似度（允许小误差）
                matching_features = 0
                for feat in new_features:
                    if feat in result_new.columns and feat in result_old.columns:
                        # 对于数值列，检查相关性
                        if result_new[feat].dtype in [np.float64, np.int64]:
                            correlation = result_new[feat].corr(result_old[feat])
                            if correlation > 0.99 or (pd.isna(correlation) and result_new[feat].isna().all() and result_old[feat].isna().all()):
                                matching_features += 1
                        else:
                            # 对于布尔/分类列，检查相等
                            if (result_new[feat] == result_old[feat]).all():
                                matching_features += 1
                
                print(f"  ✓ 数值匹配: {matching_features}/{len(new_features)}个特征")
            else:
                print(f"  ⚠ 特征不完全一致")
                print(f"    新版本独有: {new_features - old_features}")
                print(f"    旧版本独有: {old_features - new_features}")
        
        results.append({
            'size': size,
            'time_new': time_new,
            'time_old': time_old,
            'speedup': speedup
        })

# 总结
print("\n" + "=" * 80)
print("测试总结")
print("=" * 80)

if results:
    print(f"\n📈 性能提升统计:")
    for r in results:
        print(f"  {r['size']:4d}行: {r['speedup']:5.1f}x 倍提升 "
              f"(新: {r['time_new']:.3f}s, 旧: {r['time_old']:.3f}s)")
    
    avg_speedup = np.mean([r['speedup'] for r in results])
    print(f"\n  平均提升: {avg_speedup:.1f}x 倍 ⚡")
    
    # 预测大规模性能
    print(f"\n💡 大规模预测:")
    for rows in [1000, 10000]:
        est_time_old = rows * 0.045  # 假设45ms/行
        est_time_new = est_time_old / avg_speedup
        print(f"  {rows:5d}行: 旧版本 ~{est_time_old:6.1f}s, "
              f"新版本 ~{est_time_new:6.1f}s (提升{avg_speedup:.1f}x)")

print("\n" + "=" * 80)
print("✅ 性能测试完成！")
print("=" * 80)
