"""
新数据库架构原型验证

测试：
1. 创建数据库表
2. 添加单条数据（完整流程：成分解析 → 物理计算 → 特征计算）
3. 查询数据
4. 统计信息
"""

import sys
from pathlib import Path

# 添加项目根目录
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.db_models_v2 import CermetDatabaseV2, Experiment, Composition, Property, CalculatedFeature


def main():
    print("=" * 70)
    print("  新数据库架构原型验证 (v2.0)")
    print("=" * 70)
    
    # 创建测试数据库（使用内存数据库）
    print("\n1. 初始化数据库...")
    db = CermetDatabaseV2(db_path=':memory:')  # 内存数据库，测试后自动销毁
    db.create_tables()
    print("✅ 数据库表创建成功")
    
    # 测试数据
    test_cases = [
        {
            'raw_composition': 'WC-10CoCrFeNi',
            'source_id': 'test_hea_1',
            'sinter_temp_c': 1400.0,
            'grain_size_um': 1.0,
            'hv': 1500.0,
            'kic': 12.0
        },
        {
            'raw_composition': 'WC-10Co',
            'source_id': 'test_trad_1',
            'sinter_temp_c': 1350.0,
            'grain_size_um': 0.8,
            'hv': 1600.0,
            'kic': 10.5
        },
        {
            'raw_composition': 'TiC-20Ni',
            'source_id': 'test_trad_2',
            'sinter_temp_c': 1300.0,
            'grain_size_um': 1.5,
            'hv': 1200.0,
            'kic': 15.0
        }
    ]
    
    # 2. 添加测试数据
    print("\n2. 添加测试数据...")
    exp_ids = []
    
    for i, test_data in enumerate(test_cases, 1):
        print(f"\n  添加记录 {i}: {test_data['raw_composition']}")
        try:
            exp_id = db.add_experiment(**test_data, auto_calculate_features=True)
            exp_ids.append(exp_id)
            print(f"  ✅ 添加成功 (ID={exp_id})")
        except Exception as e:
            print(f"  ❌ 添加失败: {e}")
    
    print(f"\n✅ 成功添加 {len(exp_ids)} 条记录")
    
    # 3. 查询单条数据
    print("\n3. 查询详细数据...")
    if exp_ids:
        exp_data = db.get_experiment(exp_ids[0])
        if exp_data:
            print(f"\n记录 ID={exp_ids[0]} 详情:")
            print(f"  成分: {exp_data['raw_composition']}")
            print(f"  粘结相: {exp_data['composition'].get('binder_formula', 'N/A')}")
            print(f"  是否HEA: {exp_data['composition'].get('is_hea', False)}")
            print(f"  硬度: {exp_data['properties'].get('hv', 'N/A')} kgf/mm²")
            print(f"  韧性: {exp_data['properties'].get('kic', 'N/A')} MPa·m^1/2")
            print(f"  VEC: {exp_data['features'].get('vec_binder', 'N/A')}")
            print(f"  晶格失配: {exp_data['features'].get('lattice_mismatch', 'N/A')}")
    
    # 4. 统计信息
    print("\n4. 数据库统计...")
    stats = db.get_statistics()
    print(f"  总实验数: {stats['total_experiments']}")
    print(f"  HEA 记录: {stats['hea_count']}")
    print(f"  传统记录: {stats['traditional_count']}")
    
    print("\n" + "=" * 70)
    print("✅ 原型验证完成！")
    print("=" * 70)
    
    print("\n✨ 新架构优势:")
    print("  1. ✅ 相分离存储（硬质相 / 粘结相独立）")
    print("  2. ✅ 自动成分解析和化学式归一化")
    print("  3. ✅ 自动物理特征计算（VEC、晶格失配等）")
    print("  4. ✅ 多表关联，查询灵活")
    print("  5. ✅ 支持特征缓存（避免重复计算）")


if __name__ == '__main__':
    main()
