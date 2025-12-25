"""
数据库管理系统集成测试

验证：
1. 数据库基本操作
2. 查询功能
3. 与 ML Pipeline 的集成
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from core.db_manager import CermetDB
from core.db_config import STANDARD_SCHEMA

def test_database_operations():
    """测试数据库基本操作"""
    print("="*80)
    print("测试 1: 数据库基本操作")
    print("="*80)
    
    # 连接数据库
    db = CermetDB('cermet_materials.db')
    
    # 测试统计功能
    stats = db.get_statistics()
    print(f"\n✅ 数据库统计:")
    print(f"   总记录数: {stats['total_records']}")
    print(f"   HEA 记录: {stats['hea_records']}")
    print(f"   传统记录: {stats['traditional_records']}")
    
    assert stats['total_records'] > 0, "数据库应该包含数据"
    print("\n✅ 测试通过: 数据库包含数据")
    
    return stats

def test_query_filters():
    """测试查询筛选功能"""
    print("\n" + "="*80)
    print("测试 2: 查询筛选功能")
    print("="*80)
    
    db = CermetDB('cermet_materials.db')
    
    # 场景 A: 仅查询 HEA 数据
    print("\n场景 A: 仅查询 HEA 粘结相")
    df_hea = db.fetch_data(filters={'is_hea': 1})
    print(f"   找到 {len(df_hea)} 条 HEA 数据")
    assert all(df_hea['is_hea'] == 1), "所有记录应该是 HEA"
    print("   ✅ 筛选正确")
    
    # 场景 B: 必须包含 HV 数据
    print("\n场景 B: 必须包含 HV 数据")
    df_hv = db.fetch_data(drop_na_cols=['hv'])
    null_count = df_hv['hv'].isnull().sum()
    print(f"   找到 {len(df_hv)} 条数据，HV 缺失: {null_count}")
    assert null_count == 0, "不应该有 HV 缺失值"
    print("   ✅ 缺失值筛选正确")
    
    # 场景 C: 温度范围筛选
    print("\n场景 C: 烧结温度 1200-1600°C")
    df_temp = db.fetch_data(filters={'sinter_temp_c': (1200, 1600)})
    print(f"   找到 {len(df_temp)} 条数据")
    if len(df_temp) > 0:
        df_temp_valid = df_temp.dropna(subset=['sinter_temp_c'])
        if len(df_temp_valid) > 0:
            assert all(df_temp_valid['sinter_temp_c'] >= 1200), "温度应 >= 1200"
            assert all(df_temp_valid['sinter_temp_c'] <= 1600), "温度应 <= 1600"
            print("   ✅ 温度范围筛选正确")
    
    print("\n✅ 所有查询测试通过")

def test_ml_pipeline_integration():
    """测试与 ML Pipeline 的集成"""
    print("\n" + "="*80)
    print("测试 3: ML Pipeline 集成")
    print("="*80)
    
    db = CermetDB('cermet_materials.db')
    
    # 提取训练数据
    print("\n提取训练数据 (HEA + 完整工艺参数)")
    df_train = db.fetch_data(
        filters={'is_hea': 1},
        drop_na_cols=['hv', 'grain_size_um', 'sinter_temp_c']
    )
    
    print(f"   找到 {len(df_train)} 条可用于训练的数据")
    print(f"   列名: {list(df_train.columns[:10])}...")
    
    # 验证关键列存在
    required_cols = ['composition_raw', 'hv', 'grain_size_um', 'sinter_temp_c']
    for col in required_cols:
        assert col in df_train.columns, f"缺少必要列: {col}"
    
    print(f"\n   ✅ 数据格式正确")
    
    # 显示数据示例
    if len(df_train) > 0:
        print("\n   数据示例:")
        sample = df_train[['composition_raw', 'hv', 'grain_size_um', 'sinter_temp_c']].head(3)
        for idx, row in sample.iterrows():
            print(f"     {idx}: {row['composition_raw'][:30]} | HV={row['hv']:.0f}")
    
    print("\n✅ ML Pipeline 集成测试通过")
    
    return df_train

def test_field_mapping():
    """测试字段映射功能"""
    print("\n" + "="*80)
    print("测试 4: 字段映射")
    print("="*80)
    
    # 测试列名识别
    test_columns = [
        'HV, kgf/mm2',
        'KIC, MPa·m1/2',
        'Grain_Size_um',
        'd, mm',
        'Composition'
    ]
    
    print("\n测试列名映射:")
    from core.db_config import get_standard_field_name
    
    for col in test_columns:
        std_field = get_standard_field_name(col)
        status = "✅" if std_field else "❌"
        print(f"   {status} '{col}' -> {std_field}")
    
    print("\n✅ 字段映射测试完成")

def main():
    """运行所有测试"""
    print("\n")
    print("🧪 金属陶瓷数据库管理系统 - 集成测试")
    print("\n")
    
    try:
        # 运行测试
        stats = test_database_operations()
        test_query_filters()
        df_train = test_ml_pipeline_integration()
        test_field_mapping()
        
        # 总结
        print("\n" + "="*80)
        print("✅ 所有测试通过！")
        print("="*80)
        print(f"\n数据库状态:")
        print(f"  • 总数据量: {stats['total_records']} 条")
        print(f"  • 可用于训练的 HEA 数据: {len(df_train)} 条")
        print(f"  • HV 完整性: {stats['field_completeness']['hv']['completeness_pct']:.1f}%")
        print(f"  • KIC 完整性: {stats['field_completeness']['kic']['completeness_pct']:.1f}%")
        
        print("\n🎉 数据库管理系统已准备就绪！")
        print("\n建议下一步:")
        print("  1. 运行 Streamlit 应用: streamlit run app.py")
        print("  2. 访问 '数据库管理' 页面")
        print("  3. 尝试单条录入和批量导入功能")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
