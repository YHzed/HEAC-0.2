import sys
import os
from sqlalchemy import text, create_engine

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import CermetDatabaseV2

def migrate():
    print("开始数据库迁移...")
    db_path = 'cermet_master_v2.db'
    
    if not os.path.exists(db_path):
        print(f"数据库文件 {db_path} 不存在，无需迁移。")
        return

    # 直接创建引擎
    engine = create_engine(f'sqlite:///{db_path}')
    
    with engine.connect() as conn:
        try:
            print("添加 ceramic_magpie_features 列...")
            conn.execute(text("""
                ALTER TABLE calculated_features 
                ADD COLUMN ceramic_magpie_features JSON
            """))
        except Exception as e:
            if "duplicate column name" in str(e):
                print("ceramic_magpie_features 列已存在，跳过。")
            else:
                print(f"添加 ceramic_magpie_features 失败: {e}")

        try:
            print("添加 binder_magpie_features 列...")
            conn.execute(text("""
                ALTER TABLE calculated_features 
                ADD COLUMN binder_magpie_features JSON
            """))
        except Exception as e:
            if "duplicate column name" in str(e):
                print("binder_magpie_features 列已存在，跳过。")
            else:
                print(f"添加 binder_magpie_features 失败: {e}")
        
        try:
            print("添加 has_full_matminer 列...")
            conn.execute(text("""
                ALTER TABLE calculated_features 
                ADD COLUMN has_full_matminer BOOLEAN DEFAULT 0
            """))
        except Exception as e:
            if "duplicate column name" in str(e):
                print("has_full_matminer 列已存在，跳过。")
            else:
                print(f"添加 has_full_matminer 失败: {e}")
        
        conn.commit()
    
    print("✅ 迁移完成")

if __name__ == "__main__":
    migrate()
