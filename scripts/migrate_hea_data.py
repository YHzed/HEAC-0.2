"""
数据迁移脚本：将 HEA.xlsx 导入数据库

使用方法：
    python scripts/migrate_hea_data.py
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from core.db_manager import CermetDB
from core.db_config import create_column_mapping

def migrate_hea_data():
    """
    将 training data/HEA.xlsx 导入数据库
    """
    # 数据文件路径
    hea_file = 'training data/HEA.xlsx'
    
    if not os.path.exists(hea_file):
        print(f"❌ 文件不存在: {hea_file}")
        return
    
    print("="*80)
    print("金属陶瓷数据库迁移脚本")
    print("="*80)
    print(f"\n📂 读取数据文件: {hea_file}")
    
    # 读取数据
    try:
        df = pd.read_excel(hea_file)
        print(f"✅ 成功读取 {len(df)} 行数据")
        print(f"   列名: {list(df.columns)}")
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return
    
    # 创建列映射
    print(f"\n🔄 创建列映射...")
    column_mapping = create_column_mapping(df.columns.tolist())
    
    print(f"   识别到 {len(column_mapping)} 个可映射字段:")
    for orig_col, std_field in column_mapping.items():
        print(f"     • {orig_col} -> {std_field}")
    
    # 初始化数据库
    db_path = 'cermet_materials.db'
    print(f"\n💾 初始化数据库: {db_path}")
    db = CermetDB(db_path)
    
    # 批量导入
    print(f"\n📥 开始批量导入...")
    success, failed, errors = db.add_batch_data(
        df=df,
        column_mapping=column_mapping,
        source_name="HEA.xlsx"
    )
    
    # 输出结果
    print("\n" + "="*80)
    print("导入结果")
    print("="*80)
    print(f"✅ 成功: {success} 条")
    print(f"❌ 失败: {failed} 条")
    
    if errors:
        print(f"\n错误详情 (显示前 10 条):")
        for error in errors[:10]:
            print(f"  • {error}")
    
    # 统计信息
    print("\n📊 数据库统计信息:")
    stats = db.get_statistics()
    print(f"  总记录数: {stats['total_records']}")
    print(f"  HEA 粘结相: {stats['hea_records']}")
    print(f"  传统粘结相: {stats['traditional_records']}")
    
    print(f"\n🎯 关键字段完整性:")
    key_fields = ['hv', 'kic', 'trs', 'sinter_temp_c', 'grain_size_um']
    for field in key_fields:
        if field in stats['field_completeness']:
            completeness = stats['field_completeness'][field]['completeness_pct']
            non_null = stats['field_completeness'][field]['non_null']
            print(f"  • {field}: {completeness:.1f}% ({non_null} 条)")
    
    print("\n" + "="*80)
    print("✅ 迁移完成！")
    print("="*80)


if __name__ == '__main__':
    migrate_hea_data()
