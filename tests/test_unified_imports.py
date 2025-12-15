"""
测试core模块的统一导入功能
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_core_basic_imports():
    """测试核心模块的基本导入"""
    print("\n测试1: 核心模块基本导入")
    print("-" * 60)
    
    try:
        from core import (
            HEACalculator, hea_calc, MaterialProcessor,
            MaterialDatabase, db, DatasetManager,
            ModelManager, Config, config, get_text,
            ActivityLogger, initialize_session_state
        )
        
        # 验证导入成功
        assert HEACalculator is not None, "HEACalculator导入失败"
        assert hea_calc is not None, "hea_calc导入失败"
        assert MaterialProcessor is not None, "MaterialProcessor导入失败"
        assert db is not None, "db导入失败"
        assert ModelManager is not None, "ModelManager导入失败"
        assert get_text is not None, "get_text导入失败"
        
        print("✓ 所有核心模块导入成功")
        return True
    except Exception as e:
        print(f"✗ 导入失败: {e}")
        return False

def test_optional_imports():
    """测试可选依赖的导入"""
    print("\n测试2: 可选依赖导入")
    print("-" * 60)
    
    try:
        import core
        
        # 检查sklearn相关
        print(f"sklearn支持: {core._HAS_SKLEARN}")
        if core._HAS_SKLEARN:
            from core import DataProcessor, Analyzer
            assert DataProcessor is not None
            assert Analyzer is not None
            print("✓ DataProcessor和Analyzer导入成功")
        else:
            print("⚠ sklearn未安装，DataProcessor和Analyzer不可用")
        
        # 检查ML模型
        print(f"ML模型支持: {core._HAS_ML}")
        if core._HAS_ML:
            from core import ModelFactory, ModelTrainer, Optimizer
            assert ModelFactory is not None
            assert ModelTrainer is not None
            assert Optimizer is not None
            print("✓ ML模型导入成功")
        else:
            print("⚠ ML依赖未完全安装")
        
        # 检查MP API
        print(f"Materials Project API支持: {core._HAS_MP_API}")
        if core._HAS_MP_API:
            from core import MaterialsProjectClient
            assert MaterialsProjectClient is not None
            print("✓ MaterialsProjectClient导入成功")
        else:
            print("⚠ MP API未安装")
        
        return True
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

def test_calculator_functionality():
    """测试导入的计算器功能"""
    print("\n测试3: 计算器功能验证")
    print("-" * 60)
    
    try:
        from core import HEACalculator
        
        calc = HEACalculator()
        composition = {'Al': 1.0, 'Co': 1.0, 'Cr': 1.0, 'Fe': 1.0, 'Ni': 1.0}
        vec = calc.calculate_vec(composition)
        
        assert abs(vec - 7.2) < 0.01, f"VEC计算错误: {vec} != 7.2"
        print(f"✓ VEC计算正确: {vec}")
        
        return True
    except Exception as e:
        print(f"✗ 功能测试失败: {e}")
        return False

def test_backward_compatibility():
    """测试向后兼容性"""
    print("\n测试4: 向后兼容性")
    print("-" * 60)
    
    try:
        # 旧的导入方式应该仍然有效
        from core.hea_calculator import HEACalculator as HEACalc1
        from core.material_database import db as db1
        from core.localization import get_text as get_text1
        
        # 新的导入方式
        from core import HEACalculator as HEACalc2
        from core import db as db2
        from core import get_text as get_text2
        
        # 应该是同一个对象
        assert HEACalc1 is HEACalc2, "HEACalculator不一致"
        assert db1 is db2, "db不一致"
        assert get_text1 is get_text2, "get_text不一致"
        
        print("✓ 向后兼容性测试通过")
        return True
    except Exception as e:
        print(f"✗ 兼容性测试失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("=" * 60)
    print("Core模块统一导入测试")
    print("=" * 60)
    
    results = []
    
    results.append(("基本导入", test_core_basic_imports()))
    results.append(("可选依赖", test_optional_imports()))
    results.append(("计算器功能", test_calculator_functionality()))
    results.append(("向后兼容", test_backward_compatibility()))
    
    # 汇总
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{status} | {name}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！core模块统一导入功能正常。")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败。")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
