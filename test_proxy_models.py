"""
Proxy模型诊断脚本
用于测试FeatureInjector和3个proxy模型是否正常工作
"""

import sys
sys.path.append('d:/ML/HEAC 0.2')

import warnings
warnings.simplefilter("always")

print("=" * 70)
print("Proxy Models 诊断工具")
print("=" * 70)

# 1. 导入模块
print("\n步骤1: 导入FeatureInjector...")
try:
    from core.feature_injector import FeatureInjector
    print("✓ FeatureInjector导入成功")
except Exception as e:
    print(f"✗ 导入失败: {e}")
    sys.exit(1)

# 2. 初始化
print("\n步骤2: 初始化FeatureInjector...")
try:
    fi = FeatureInjector(model_dir='models/proxy_models')
    print(f"✓ 已加载 {len(fi.models)} 个模型")
    print(f"  模型列表: {list(fi.models.keys())}")
except Exception as e:
    print(f"✗ 初始化失败: {e}")
    sys.exit(1)

# 3. 测试成分
test_cases = [
    {'Co': 0.33, 'Ni': 0.33, 'Fe': 0.34},  # 标准CoNiFe
    {'Co': 1.0, 'Ni': 1.0, 'Fe': 1.0, 'Cr': 0.5, 'Mo': 0.2},  # 用户的成分
]

for i, test_comp in enumerate(test_cases, 1):
    print(f"\n{'='*70}")
    print(f"测试用例 {i}: {test_comp}")
    print(f"{'='*70}")
    
    # 归一化
    total = sum(test_comp.values())
    test_comp_norm = {k: v/total for k, v in test_comp.items()}
    print(f"归一化成分: {test_comp_norm}")
    
    # 测试形成能
    print("\n  [1/3] 形成能预测:")
    try:
        ef = fi.predict_formation_energy(test_comp_norm)
        if ef is not None:
            print(f"    ✓ 结果: {ef:.4f} eV/atom")
            if -3.0 < ef < 1.0:
                print(f"    ✓ 数值合理")
            else:
                print(f"    ⚠ 数值异常（通常范围: -3.0 到 1.0）")
        else:
            print(f"    ✗ 返回None（预测失败）")
    except Exception as e:
        print(f"    ✗ 异常: {e}")
    
    # 测试晶格参数
    print("\n  [2/3] 晶格参数预测:")
    try:
        lp = fi.predict_lattice_parameter(test_comp_norm)
        if lp is not None:
            print(f"    ✓ 结果: {lp:.4f} Å")
            if 3.0 < lp < 4.5:
                print(f"    ✓ 数值合理（FCC HEA典型范围）")
            else:
                print(f"    ⚠ 数值异常（FCC HEA通常: 3.0-4.5 Å）")
        else:
            print(f"    ✗ 返回None（预测失败）")
    except Exception as e:
        print(f"    ✗ 异常: {e}")
    
    # 测试磁矩
    print("\n  [3/3] 磁矩预测:")
    try:
        mm = fi.predict_magnetic_moment(test_comp_norm)
        if mm is not None:
            print(f"    ✓ 结果: {mm:.4f} μB/atom")
            if -5.0 < mm < 5.0:
                print(f"    ✓ 数值合理")
            else:
                print(f"    ⚠ 数值异常（通常范围: -5 到 5）")
        else:
            print(f"    ✗ 返回None（预测失败）")
    except Exception as e:
        print(f"    ✗ 异常: {e}")

print(f"\n{'='*70}")
print("诊断完成")
print(f"{'='*70}")

# 汇总建议
print("\n诊断建议:")
print("1. 如果所有预测都返回None:")
print("   - 检查models/proxy_models/目录下的.pkl文件是否存在")
print("   - 检查matminer是否正确安装: pip show matminer")
print("   - 重新训练proxy模型")
print("\n2. 如果部分预测成功:")
print("   - 可能是特定成分的问题")
print("   - 检查是否包含稀有元素")
print("\n3. 如果全部成功:")
print("   - Proxy模型工作正常")
print("   - 问题可能在上层调用逻辑中")
