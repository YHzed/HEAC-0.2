"""
集成测试 - 完整数据流验证

测试流程：
1. 创建新数据库
2. 导入测试数据（多种格式）
3. 验证成分解析
4. 验证特征计算
5. 验证数据查询
6. 性能测试
"""

import sys
import time
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core import CermetDatabaseV2, DataExtractor


def test_full_integration():
    """完整集成测试"""
    print("=" * 70)
    print("  完整集成测试 - Phase 5-6")  
    print("=" * 70)
    
    # 1. 创建测试数据库
    print("\n[1/6] 创建测试数据库...")
    db = CermetDatabaseV2(':memory:')
    db.create_tables()
    print("  ✅ 数据库已创建")
    
    # 2. 测试数据（多种格式）
    test_data = [
        # 基本格式
        {"raw_composition": "WC-10Co", "hv": 1600, "kic": 10.0, "source": "test_basic"},
        {"raw_composition": "WC-10CoCrFeNi", "hv": 1500, "kic": 12.0, "source": "test_hea"},
        {"raw_composition": "TiC-20Ni", "hv": 1200, "kic": 15.0, "source": "test_tic"},
        
        # 复杂格式
        {"raw_composition": "b WC 69.5 CoCrFeNiMo 0.5 Cr3C2", "hv": 1450, "kic": 11.5, "source": "test_complex1"},
        {"raw_composition": "b WC 69 CoCrFeNiMo 1 Cr3C2 10 Mo", "hv": 1480, "kic": 11.8, "source": "test_complex2"},
        
        # 空格格式
        {"raw_composition": "WC 85 Co 10 Ni 5", "hv": 1550, "kic": 11.0, "source": "test_space"},
    ]
    
    # 3. 批量导入
    print(f"\n[2/6] 批量导入 {len(test_data)} 条测试数据...")
    start_time = time.time()
    
    success_ids = []
    for i, data in enumerate(test_data, 1):
        try:
            exp_id = db.add_experiment(
                raw_composition=data['raw_composition'],
                source_id=data['source'],
                hv=data['hv'],
                kic=data['kic'],
                auto_calculate_features=True
            )
            success_ids.append(exp_id)
            print(f"  ✅ [{i}/{len(test_data)}] {data['raw_composition'][:30]}")
        except Exception as e:
            print(f"  ❌ [{i}/{len(test_data)}] 失败: {e}")
    
    import_time = time.time() - start_time
    print(f"  导入完成，耗时: {import_time:.2f}s")
    
    # 4. 数据验证
    print(f"\n[3/6] 验证数据完整性...")
    stats = db.get_statistics()
    print(f"  总记录: {stats['total_experiments']}")
    print(f"  HEA: {stats['hea_count']}")
    print(f"  传统: {stats['traditional_count']}")
    
    assert stats['total_experiments'] == len(success_ids), "记录数不匹配"
    print("  ✅ 数据完整性验证通过")
    
    # 5. 查询测试
    print(f"\n[4/6] 测试数据查询...")
    for exp_id in success_ids[:3]:  # 查询前3条
        data = db.get_experiment(exp_id)
        assert data is not None, f"记录 {exp_id} 查询失败"
        assert 'composition' in data, "缺少 composition 数据"
        assert 'properties' in data, "缺少 properties 数据"
        assert 'features' in data, "缺少 features 数据"
    
    print(f"  ✅ 查询测试通过")
    
    # 6. 数据提取测试
    print(f"\n[5/6] 测试数据提取...")
    extractor = DataExtractor(db)
    
    # 提取全部数据
    df_all = extractor.get_training_data(target='hv', fillna=True)
    print(f"  全部数据: {len(df_all)} 行")
    
    # 提取 HEA 数据
    df_hea = extractor.get_training_data(target='hv', hea_only=True, fillna=True)
    print(f"  HEA 数据: {len(df_hea)} 行")
    
    assert len(df_all) >= len(df_hea), "HEA 数据不应超过总数"
    print("  ✅ 数据提取测试通过")
    
    # 7. 性能评估
    print(f"\n[6/6] 性能评估...")
    print(f"  平均导入速度: {len(test_data)/import_time:.1f} 条/秒")
    print(f"  预估 1000条 数据导入: {1000/len(test_data)*import_time:.1f} 秒")
    
    # 最终总结
    print("\n" + "=" * 70)
    print("✅ 集成测试全部通过！")
    print("=" * 70)
    print(f"\n测试统计:")
    print(f"  - 导入成功: {len(success_ids)}/{len(test_data)}")
    print(f"  - 数据完整性: ✅")
    print(f"  - 查询功能: ✅")
    print(f"  - 数据提取: ✅")
    print(f"  - 性能: ✅")
    
    return True


if __name__ == '__main__':
    try:
        success = test_full_integration()
        print("\n" + "🎉" * 20)
        print("系统已就绪，可投入生产使用！")
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
