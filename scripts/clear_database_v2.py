"""
清空 V2 数据库脚本 - 完全清理版

直接删除数据库文件并重建
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.db_models_v2 import CermetDatabaseV2

def clear_v2_database_completely():
    """彻底清空 V2 数据库"""
    print("=" * 80)
    print("⚠️  V2 数据库完全清理")
    print("=" * 80)
    
    db_path = 'cermet_master_v2.db'
    
    # 方式1：直接删除数据库文件
    if os.path.exists(db_path):
        file_size = os.path.getsize(db_path)
        print(f"\n📁 发现数据库文件:")
        print(f"   路径: {db_path}")
        print(f"   大小: {file_size / 1024:.2f} KB")
        
        try:
            os.remove(db_path)
            print(f"\n✅ 已删除数据库文件")
        except Exception as e:
            print(f"❌ 删除失败: {e}")
            return
    else:
        print(f"\n✅ 数据库文件不存在: {db_path}")
    
    # 重建空数据库
    print(f"\n🏗️  重建空数据库...")
    try:
        db = CermetDatabaseV2(db_path)
        db.create_tables()
        
        # 验证
        stats = db.get_statistics()
        print(f"\n✅ 新数据库已创建:")
        print(f"   总记录数: {stats['total_experiments']}")
        print(f"   HEA: {stats['hea_count']}")
        print(f"   传统: {stats['traditional_count']}")
        
        if stats['total_experiments'] == 0:
            print(f"\n🎉 数据库清理完成！")
        else:
            print(f"\n⚠️  警告：仍有数据残留")
    
    except Exception as e:
        print(f"❌ 重建失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("操作完成")
    print("=" * 80)

if __name__ == '__main__':
    clear_v2_database_completely()
