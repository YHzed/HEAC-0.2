"""
测试FeatureInjector缓存集成

验证缓存功能是否正确工作
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
import numpy as np
from core.feature_injector import FeatureInjector

print("=" * 80)
print("FeatureInjector缓存集成测试")
print("=" * 80)

# 测试1: 默认启用缓存
print("\n[测试1] 默认启用缓存")
injector = FeatureInjector()
print(f"  缓存启用: {injector.enable_cache}")
print(f"  缓存初始化: {injector._feature_cache is not None}")

# 测试2: 简单数据测试
print("\n[测试2] 缓存功能测试")
test_data = pd.DataFrame({
    'binder_composition': [
        'CoCrFeNi',
        'AlCoCrFeNi',  # 重复
        'CoCrFeMnNi',
        'AlCoCrFeNi',  # 重复
        'CoCrFeNi'      # 重复（第3次）
    ]
})

print(f"  测试数据: {len(test_data)}行，{len(test_data['binder_composition'].unique())}个唯一成分")

result = injector.inject_features(test_data, verbose=True)

print(f"\n  结果shape: {result.shape}")
print(f"  添加的特征: {[col for col in result.columns if col not in test_data.columns]}")

# 测试3: 缓存统计
print("\n[测试3] 缓存统计")
stats = injector.get_cache_stats()
print(f"  缓存大小: {stats['cache_size']} 个成分")
print(f"  缓存命中: {stats['cache_hits']}")
print(f"  缓存未命中: {stats['cache_misses']}")
print(f"  命中率: {stats['hit_rate']*100:.1f}%")
print(f"  内存占用: {stats['memory_mb']:.2f} MB")

# 测试4: 禁用缓存测试
print("\n[测试4] 禁用缓存测试")
injector_no_cache = FeatureInjector(enable_cache=False)
print(f"  缓存启用: {injector_no_cache.enable_cache}")

result_no_cache = injector_no_cache.inject_features(test_data, verbose=False)
print(f"  结果shape: {result_no_cache.shape}")

# 测试5: 结果一致性
print("\n[测试5] 缓存vs非缓存结果一致性")
numeric_cols = result.select_dtypes(include=[np.number]).columns
differences = []
for col in numeric_cols:
    if col in result_no_cache.columns:
        diff = (result[col] - result_no_cache[col]).abs().max()
        if diff > 1e-6:
            differences.append((col, diff))

if differences:
    print(f"  ❌ 发现差异:")
    for col, diff in differences:
        print(f"     {col}: {diff}")
else:
    print(f"  ✅ 结果完全一致！")

# 测试6: 清空缓存
print("\n[测试6] 清空缓存")
print(f"  清空前缓存大小: {len(injector._feature_cache)}")
injector.clear_cache()
print(f"  清空后缓存大小: {len(injector._feature_cache)}")

print("\n" + "=" * 80)
print("✅ 所有测试完成！")
print("=" * 80)
