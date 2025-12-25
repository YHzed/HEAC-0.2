"""
清空数据库脚本

删除数据库中的所有数据
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.db_manager import CermetDB, MaterialRecord
from sqlalchemy import delete

def clear_database():
    """清空数据库中的所有数据"""
    print("="*80)
    print("⚠️  数据库清空操作")
    print("="*80)
    
    db_path = 'cermet_materials.db'
    db = CermetDB(db_path)
    
    # 获取当前统计
    stats = db.get_statistics()
    total_records = stats['total_records']
    
    print(f"\n当前数据库状态:")
    print(f"  数据库文件: {db_path}")
    print(f"  总记录数: {total_records}")
    print(f"  HEA 记录: {stats['hea_records']}")
    print(f"  传统记录: {stats['traditional_records']}")
    
    if total_records == 0:
        print("\n✅ 数据库已经是空的")
        return
    
    # 执行清空
    print(f"\n🗑️  正在删除所有 {total_records} 条记录...")
    
    session = db.Session()
    try:
        # 删除所有记录
        session.query(MaterialRecord).delete()
        session.commit()
        
        # 验证
        remaining = session.query(MaterialRecord).count()
        
        if remaining == 0:
            print(f"✅ 成功清空数据库！")
            print(f"   已删除 {total_records} 条记录")
        else:
            print(f"⚠️  仍有 {remaining} 条记录未删除")
    
    except Exception as e:
        session.rollback()
        print(f"❌ 清空失败: {e}")
    
    finally:
        session.close()
    
    print("\n" + "="*80)
    print("操作完成")
    print("="*80)

if __name__ == '__main__':
    clear_database()
