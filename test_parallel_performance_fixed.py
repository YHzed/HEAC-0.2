"""
并行特征注入性能测试（Windows兼容版本）

对比三个版本的性能：
1. inject_features (向量化)
2. inject_features_parallel (多进程) ✅ Windows修复
3. inject_features_cached (缓存)
"""
import time
import pandas as pd
import numpy as np
from core.feature_injector import FeatureInjector
from core.parallel_feature_injector import ParallelFeatureInjector


def run_tests():
    """运行性能测试"""
    print("=" * 80)
    print("并行特征注入性能测试（Windows兼容）")
    print("=" * 80)

    # 初始化
    print("\n初始化...")
    injector = FeatureInjector(model_dir="saved_models/proxy")
    parallel_injector = ParallelFeatureInjector(injector)

    # 准备测试数据
    compositions = [
        'CoCrFeNi',
        'AlCoCrFeNi',
        'CoCrFeMnNi',
        'TiZrNbTa',
        'CoCrFeNiCu'
    ]

    # 测试配置
    test_configs = [
        {'size': 50, 'name': '50行（小型）'},
        {'size': 200, 'name': '200行（中等）'},
        {'size': 500, 'name': '500行（大型）'},
    ]

    print(f"测试成分: {len(compositions)}种")
    print(f"测试配置: {len(test_configs)}个")

    # 性能测试
    print("\n" + "=" * 80)
    print("性能对比测试")
    print("=" * 80)

    all_results = []

    for config in test_configs:
        size = config['size']
        name = config['name']
        
        print(f"\n{'─' * 80}")
        print(f"测试: {name}")
        print(f"{'─' * 80}")
        
        # 创建测试数据（包含重复以测试缓存效果）
        df_test = pd.DataFrame({
            'binder_composition': np.random.choice(compositions, size)
        })
    
        unique_ratio = len(df_test['binder_composition'].unique()) / len(df_test)
        print(f"唯一成分比例: {unique_ratio*100:.1f}%")
        
        results = {'size': size, 'name': name, 'unique_ratio': unique_ratio}
        
        # 测试1: 向量化版本（作为基准）
        print("\n▶ 测试向量化版本（基准）...")
        df1 = df_test.copy()
        start = time.time()
        try:
            result1 = injector.inject_features(df1, verbose=False)
            time1 = time.time() - start
            print(f"  ✓ 完成: {time1:.2f}秒 ({size/time1:.1f} 行/秒)")
            results['vectorized'] = time1
        except Exception as e:
            print(f"  ✗ 失败: {e}")
            results['vectorized'] = None
        
        # 测试2: 并行处理版本 ✅ 修复
        print("\n▶ 测试并行处理版本（4进程）...")
        df2 = df_test.copy()
        start = time.time()
        try:
            result2 = parallel_injector.inject_features_parallel(df2, n_jobs=4, verbose=False)
            time2 = time.time() - start
            print(f"  ✓ 完成: {time2:.2f}秒 ({size/time2:.1f} 行/秒)")
            results['parallel'] = time2
        except Exception as e:
            print(f"  ✗ 失败: {e}")
            results['parallel'] = None
        
        # 测试3: 缓存版本  
        print("\n▶ 测试缓存版本...")
        # 清空缓存
        parallel_injector._feature_cache = {}
        df3 = df_test.copy()
        start = time.time()
        try:
            result3 = parallel_injector.inject_features_cached(df3, verbose=False)
            time3 = time.time() - start
            print(f"  ✓ 完成: {time3:.2f}秒 ({size/time3:.1f} 行/秒)")
            results['cached'] = time3
        except Exception as e:
            print(f"  ✗ 失败: {e}")
            results['cached'] = None
        
        # 性能对比
        print(f"\n📊 性能对比:")
        if results['vectorized']:
            print(f"  向量化（基准）: {results['vectorized']:.2f}s")
        if results['parallel']:
            speedup_p = results['vectorized'] / results['parallel'] if results['vectorized'] else 0
            print(f"  并行处理（4核）: {results['parallel']:.2f}s (提升 {speedup_p:.2f}x)")
        if results['cached']:
            speedup_c = results['vectorized'] / results['cached'] if results['vectorized'] else 0
            print(f"  缓存优化:       {results['cached']:.2f}s (提升 {speedup_c:.2f}x)")
        
        all_results.append(results)

    # 总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)

    print("\n📈 性能提升统计:")
    for r in all_results:
        print(f"\n{r['name']}:")
        if r['vectorized'] and r['parallel']:
            speedup_p = r['vectorized'] / r['parallel']
            print(f"  并行处理: {speedup_p:.2f}x 倍提升")
        if r['vectorized'] and r['cached']:
            speedup_c = r['vectorized'] / r['cached']
            print(f"  缓存优化: {speedup_c:.2f}x 倍提升")

    # 平均提升
    parallel_speedups = [r['vectorized']/r['parallel'] for r in all_results if r['vectorized'] and r['parallel']]
    cached_speedups = [r['vectorized']/r['cached'] for r in all_results if r['vectorized'] and r['cached']]

    if parallel_speedups:
        print(f"\n⚡ 并行处理平均提升: {np.mean(parallel_speedups):.2f}x")
    if cached_speedups:
        print(f"💾 缓存优化平均提升: {np.mean(cached_speedups):.2f}x")

    print("\n" + "=" * 80)
    print("✅ 测试完成！")
    print("=" * 80)


# Windows multiprocessing 必需的保护
if __name__ == '__main__':
    # 设置multiprocessing启动方法（可选，但推荐）
    import multiprocessing as mp
    try:
        mp.set_start_method('spawn')
    except RuntimeError:
        pass  # 已经设置过了
    
    # 运行测试
    run_tests()
