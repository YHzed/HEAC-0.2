"""
简化性能测试

直接测试inject_features向量化优化效果
"""
import time
import pandas as pd
import numpy as np
from core.feature_injector import FeatureInjector

print("=" * 80)
print("FeatureInjector 性能测试（简化版）")
print("=" * 80)

# 初始化FeatureInjector
print("\n初始化...")
injector = FeatureInjector(model_dir="saved_models/proxy")

# 准备测试数据
print("\n准备测试数据...")
compositions = [
    'CoCrFeNi',
    'AlCoCrFeNi', 
    'CoCrFeMnNi',
    'TiZrNbTa',
    'CoCrFeNiCu'
]

# 测试不同规模
test_sizes = [10, 50, 100, 500]

print(f"测试成分: {len(compositions)}种")
print(f"测试规模: {test_sizes}")

# 性能测试
print("\n" + "=" * 80)
print("性能测试")
print("=" * 80)

results = []

for size in test_sizes:
    print(f"\n{'─' * 80}")
    print(f"测试规模: {size}行")
    print(f"{'─' * 80}")
    
    # 创建测试数据
    df_test = pd.DataFrame({
        'binder_composition': np.random.choice(compositions, size)
    })
    
    # 测试向量化版本
    print("\n▶ 测试向量化版本...")
    df_new = df_test.copy()
    start = time.time()
    try:
        result_new = injector.inject_features(df_new, comp_col='binder_composition', verbose=False)
        time_new = time.time() - start
        print(f"  ✓ 完成: {time_new:.3f}秒 ({size/time_new:.1f} 行/秒)")
        
        # 检查生成的特征
        new_features = [c for c in result_new.columns if c.startswith('pred_')]
        print(f"  ✓ 生成特征: {len(new_features)}个")
        
        # 检查有效值
        valid_formation = result_new['pred_formation_energy'].notna().sum()
        print(f"  ✓ 有效预测: {valid_formation}/{size} 行")
        
    except Exception as e:
        print(f"  ✗ 失败: {e}")
        time_new = None
    
    # 测试iterrows版本  
    print("\n▶ 测试iterrows版本...")
    df_old = df_test.copy()
    start = time.time()
    try:
        result_old = injector.inject_features_legacy(df_old, comp_col='binder_composition', verbose=False)
        time_old = time.time() - start
        print(f"  ✓ 完成: {time_old:.3f}秒 ({size/time_old:.1f} 行/秒)")
        
        # 检查生成的特征
        old_features = [c for c in result_old.columns if c.startswith('pred_')]
        print(f"  ✓ 生成特征: {len(old_features)}个")
        
        # 检查有效值
        valid_formation = result_old['pred_formation_energy'].notna().sum()
        print(f"  ✓ 有效预测: {valid_formation}/{size} 行")
        
    except Exception as e:
        print(f"  ✗ 失败: {e}")
        time_old = None
    
    # 性能对比
    if time_new and time_old:
        speedup = time_old / time_new
        print(f"\n📊 性能对比:")
        print(f"  新版本: {time_new:.3f}秒")
        print(f"  旧版本: {time_old:.3f}秒")  
        print(f"  ⚡ 提升: {speedup:.1f}x 倍")
        
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
    print("\n📈 性能提升统计:")
    for r in results:
        print(f"  {r['size']:4d}行: {r['speedup']:5.1f}x 倍提升 "
              f"(新: {r['time_new']:.3f}s, 旧: {r['time_old']:.3f}s)")
    
    avg_speedup = np.mean([r['speedup'] for r in results])
    print(f"\n  ⚡ 平均提升: {avg_speedup:.1f}x 倍")
    
    # 预测大规模性能
    if avg_speedup > 1:
        print(f"\n💡 大规模预测:")
        for rows in [1000, 10000]:
            # 基于平均速度估算
            avg_rate_old = np.mean([r['size']/r['time_old'] for r in results])
            est_time_old = rows / avg_rate_old
            est_time_new = est_time_old / avg_speedup
            print(f"  {rows:5d}行: 旧版本 ~{est_time_old:6.1f}s, "
                  f"新版本 ~{est_time_new:6.1f}s (节省{est_time_old-est_time_new:.1f}s)")
else:
    print("\n⚠️  没有成功的测试结果")

print("\n" + "=" * 80)
print("✅ 测试完成！")
print("=" * 80)
