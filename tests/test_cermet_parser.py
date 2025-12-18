# -*- coding: utf-8 -*-
"""
测试增强的成分解析器 - 金属陶瓷格式支持

测试能否正确解析包含硬质相和粘结相的混合格式
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.data_standardizer import CompositionParser

def test_cermet_parser():
    """测试金属陶瓷格式解析"""
    parser = CompositionParser()
    
    print("=" * 80)
    print("金属陶瓷成分解析器测试")
    print("=" * 80)
    
    # 测试用例
    test_cases = [
        # 格式1: b WC XX Co (用户数据格式)
        "b WC 25 Co",
        "b WC 19.5 Co",
        "b WC 14 Co",
        "b WC 9 Co",
        
        # 格式2: WC + 多元粘结相
        "WC 85 Co 10 Ni 5",
        "WC 80 Co 15 Ni 3 Cr 2",
        
        # 格式3: 标准粘结相（无WC）
        "AlCoCrFeNi",
        "Co80Ni20",
    ]
    
    print("\n【测试1：提取粘结相（用于辅助模型）】")
    print("-" * 80)
    
    for comp_str in test_cases:
        result = parser.parse(comp_str, extract_binder_only=True)
        
        print(f"\n输入: {comp_str}")
        
        if result:
            print(f"粘结相成分: {result}")
            total = sum(result.values())
            print(f"归一化检验: {total:.6f} (应为1.0)")
            
            # 显示标准格式
            std_str = parser.to_standard_string(result)
            print(f"标准格式: {std_str}")
        else:
            print("❌ 解析失败")
    
    print("\n" + "=" * 80)
    print("【测试2：完整成分（包含硬质相）】")
    print("-" * 80)
    
    for comp_str in test_cases[:4]:  # 只测试WC格式
        result = parser.parse(comp_str, extract_binder_only=False)
        
        print(f"\n输入: {comp_str}")
        
        if result:
            print("完整成分:")
            for elem, frac in result.items():
                print(f"  {elem}: {frac:.2f}%")
        else:
            print("❌ 解析失败")
    
    print("\n" + "=" * 80)
    print("【测试3：实际应用场景】")
    print("-" * 80)
    
    # 模拟用户数据
    user_data = [
        "b WC 25 Co",
        "b WC 19.5 Co", 
        "b WC 9 Co"
    ]
    
    print("\n场景：为实验数据提取粘结相成分用于辅助模型预测")
    print()
    
    for comp_str in user_data:
        binder = parser.parse(comp_str, extract_binder_only=True)
        
        if binder:
            print(f"{comp_str:20s} -> 粘结相: {parser.to_standard_string(binder)}")
            print(f"{'':20s}    (可用于预测形成能、晶格常数等)")
        else:
            print(f"{comp_str:20s} -> ❌ 无法提取粘结相")
    
    print("\n" + "=" * 80)
    print("✅ 测试完成！")
    print("=" * 80)

if __name__ == "__main__":
    test_cermet_parser()
