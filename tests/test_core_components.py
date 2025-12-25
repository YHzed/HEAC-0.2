"""
核心组件单元测试

测试模块：
1. CompositionParser - 成分解析器
2. PhysicsCalculator - 物理计算器
3. FeatureEngine - 特征计算引擎
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.composition_parser import CompositionParser
from core.physics_calculator import PhysicsCalculator
from core.feature_engine import FeatureEngine


def test_composition_parser():
    """测试成分解析器"""
    print("=" * 70)
    print("测试 1: CompositionParser (成分解析器)")
    print("=" * 70)
    
    parser = CompositionParser()
    
    # 测试用例
    test_cases = [
        # (输入, 描述)
        ("WC-10CoCrFeNi", "短横线格式 - HEA粘结相"),
        ("80TiC-20Mo", "短横线格式 - 带百分比"),
        ("WC 85 Co 10 Ni 5", "空格格式"),
        ("b WC 25 Co", "b前缀格式"),
        ("WC x Co", "x占位符"),
        ("94.12 WC x Co", "硬质相已知"),
    ]
    
    passed = 0
    failed = 0
    
    for comp_str, desc in test_cases:
        print(f"\n测试: {desc}")
        print(f"输入: '{comp_str}'")
        
        result = parser.parse(comp_str)
        
        if result.get('success'):
            print(f"✅ 解析成功")
            print(f"   粘结相化学式: {result['binder_formula']}")
            print(f"   陶瓷相: {result['ceramic_formula']}")
            print(f"   粘结相 wt%: {result.get('binder_wt_pct', 'N/A')}")
            passed += 1
        else:
            print(f"❌ 解析失败: {result.get('message')}")
            failed += 1
    
    print(f"\n总结: {passed} 通过, {failed} 失败")
    return failed == 0


def test_physics_calculator():
    """测试物理计算器"""
    print("\n" + "=" * 70)
    print("测试 2: PhysicsCalculator (物理计算器)")
    print("=" * 70)
    
    calc = PhysicsCalculator()
    
    # 测试用例
    test_cases = [
        {
            'name': 'wt% → vol% 转换',
            'func': calc.wt_to_vol,
            'args': (10.0, 'Co1', 'WC'),
            'expected_range': (15.0, 18.0)  # WC-Co系统：高密度陶瓷，vol%>wt%
        },
        {
            'name': '密度计算 - 单元素',
            'func': calc.calculate_density,
            'args': ('Co1',),
            'expected_range': (8.5, 9.2)  # Co 密度约 8.9
        },
        {
            'name': '密度计算 - HEA',
            'func': calc.calculate_density,
            'args': ('Co1Cr1Fe1Ni1',),
            'expected_range': (7.5, 9.0)
        },
        {
            'name': 'VEC 计算',
            'func': calc.calculate_vec,
            'args': ('Co1Cr1Fe1Ni1',),
            'expected_range': (8.0, 9.0)
        },
        {
            'name': '晶格失配度',
            'func': calc.lattice_mismatch,
            'args': (3.6, 'WC', 'fcc'),
            'expected_range': (0.0, 0.3)
        }
    ]
    
    passed = 0
    failed = 0
    
    for test in test_cases:
        print(f"\n测试: {test['name']}")
        try:
            result = test['func'](*test['args'])
            
            if result is None:
                print(f"⚠️  返回 None")
                failed += 1
            elif 'expected_range' in test:
                min_val, max_val = test['expected_range']
                if min_val <= result <= max_val:
                    print(f"✅ 结果: {result:.4f} (在预期范围内)")
                    passed += 1
                else:
                    print(f"❌ 结果: {result:.4f} (超出预期范围 [{min_val}, {max_val}])")
                    failed += 1
            else:
                print(f"✅ 结果: {result}")
                passed += 1
                
        except Exception as e:
            print(f"❌ 异常: {e}")
            failed += 1
    
    print(f"\n总结: {passed} 通过, {failed} 失败")
    return failed == 0


def test_feature_engine():
    """测试特征计算引擎"""
    print("\n" + "=" * 70)
    print("测试 3: FeatureEngine (特征计算引擎)")
    print("=" * 70)
    
    engine = FeatureEngine()
    
    # 测试用例
    test_formulas = [
        ('Co1', 'WC', 10.0),  # (粘结相, 陶瓷相, wt%)
        ('Co1Cr1Fe1Ni1', 'WC', 15.0),  # HEA
        ('Ni1', 'TiC', 20.0),
    ]
    
    passed = 0
    failed = 0
    
    for binder, ceramic, wt_pct in test_formulas:
        print(f"\n测试配方: {ceramic}-{wt_pct:.0f}wt% {binder}")
        
        try:
            # 计算特征（不使用 Matminer 以加快速度）
            features = engine.calculate_features(
                binder_formula=binder,
                ceramic_formula=ceramic,
                binder_wt_pct=wt_pct,
                use_matminer=False
            )
            
            # 检查返回结构
            if 'proxy_features' in features and 'physics_features' in features:
                print("✅ 特征计算成功")
                
                # 显示部分结果
                proxy = features['proxy_features']
                physics = features['physics_features']
                
                print(f"   Proxy 特征:")
                for key, value in list(proxy.items())[:3]:
                    print(f"     - {key}: {value}")
                
                print(f"   物理特征:")
                for key, value in list(physics.items())[:3]:
                    print(f"     - {key}: {value}")
                
                passed += 1
            else:
                print("❌ 返回结构不完整")
                failed += 1
                
        except Exception as e:
            print(f"❌ 异常: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print(f"\n总结: {passed} 通过, {failed} 失败")
    return failed == 0


def main():
    """主测试函数"""
    print("\n" + "=" * 70)
    print("  核心组件单元测试")
    print("=" * 70)
    
    all_passed = True
    
    # 测试 1: 成分解析器
    if not test_composition_parser():
        all_passed = False
    
    # 测试 2: 物理计算器
    if not test_physics_calculator():
        all_passed = False
    
    # 测试 3: 特征计算引擎
    if not test_feature_engine():
        all_passed = False
    
    # 总结
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ 所有测试通过！")
    else:
        print("❌ 部分测试失败，请检查错误信息")
    print("=" * 70)
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    exit(main())
