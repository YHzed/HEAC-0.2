"""
测试新增的成分格式

测试格式: 数字在前的空格格式
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.composition_parser import CompositionParser


def test_number_first_format():
    """测试数字在前的格式"""
    print("=" * 70)
    print("  测试数字在前的空格格式")
    print("=" * 70)
    
    parser = CompositionParser()
    
    # 测试用例（来自用户Excel）
    test_cases = [
        "90 WC 10 Co",
        "94 WC 6 Co",
        "85 WC 15 Co",
        "87 WC 13 Co",
        "93 WC 7 Co",
        "80 TiC 20 Ni",
        "75 TiC 25 Co",
    ]
    
    passed = 0
    failed = 0
    
    for comp_str in test_cases:
        print(f"\n测试: {comp_str}")
        
        result = parser.parse(comp_str)
        
        if result.get('success'):
            print(f"  ✅ 解析成功")
            print(f"     硬质相: {result['ceramic_formula']}")
            print(f"     粘结相: {result['binder_formula']}")
            print(f"     粘结相 wt%: {result['binder_wt_pct']:.1f}%")
            passed += 1
        else:
            print(f"  ❌ 解析失败: {result.get('message')}")
            failed += 1
    
    print(f"\n" + "=" * 70)
    print(f"总结: {passed}/{len(test_cases)} 通过")
    print("=" * 70)
    
    return failed == 0


if __name__ == '__main__':
    success = test_number_first_format()
    exit(0 if success else 1)
