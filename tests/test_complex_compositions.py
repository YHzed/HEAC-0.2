"""
复杂成分格式测试

测试特殊格式：
- 第二硬质相（如 0.5 Cr3C2）
- 粘结相添加剂（如 10 Mo, 10 Ni）
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.composition_parser import CompositionParser


def test_complex_formats():
    """测试复杂成分格式"""
    print("=" * 70)
    print("  复杂成分格式测试")
    print("=" * 70)
    
    parser = CompositionParser()
    
    # 测试用例（来自用户图片）
    test_cases = [
        "b WC 69.5 CoCrFeNiMo 0.5 Cr3C2",  # 第二硬质相
        "b WC 69 CoCrFeNiMo 1 Cr3C2",
        "b WC 69.5 CoCrFeNiMo 0.5 Cr3C2 10 Mo",  # + 粘结相添加剂
        "b WC 69 CoCrFeNiMo 1 Cr3C2 10 Mo",
        "b WC 69.5 CoCrFeNiMo 0.5 Cr3C2 10 Mo 10 Ni",  # 多个添加剂
        "b WC 69 CoCrFeNiMo 1 Cr3C2 15 Ni",
    ]
    
    passed = 0
    failed = 0
    
    for comp_str in test_cases:
        print(f"\n测试: {comp_str}")
        
        result = parser.parse(comp_str)
        
        if result.get('success'):
            print(f"  ✅ 解析成功")
            print(f"     主硬质相: {result['ceramic_formula']}")
            print(f"     第二硬质相: {result.get('secondary_phase', 'None')}")
            print(f"     粘结相: {result['binder_formula']}")
            print(f"     粘结相 wt%: {result['binder_wt_pct']:.2f}%")
            
            # 显示所有陶瓷元素
            if result['ceramic_elements']:
                print(f"     陶瓷相详情: {result['ceramic_elements']}")
            
            passed += 1
        else:
            print(f"  ❌ 解析失败: {result.get('message')}")
            failed += 1
    
    print(f"\n" + "=" * 70)
    print(f"总结: {passed}/{len(test_cases)} 通过")
    print("=" * 70)
    
    return failed == 0


if __name__ == '__main__':
    success = test_complex_formats()
    exit(0 if success else 1)
