"""
数据迁移脚本 - v1 → v2

功能：
- 从旧数据库（单表）读取数据
- 解析成分并分离相
- 写入新数据库（多表）
- 计算物理特征
"""

import sys
from pathlib import Path

# 添加项目根目录
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from tqdm import tqdm
from core.db_manager import CermetDB  # 旧数据库
from core.db_models_v2 import CermetDatabaseV2  # 新数据库


def migrate_data(
    old_db_path: str = 'cermet_materials.db',
    new_db_path: str = 'cermet_master_v2.db',
    limit: int = None,
    calculate_features: bool = True
):
    """
    执行数据迁移
    
    Args:
        old_db_path: 旧数据库路径
        new_db_path: 新数据库路径
        limit: 迁移数据条数限制（None=全部）
        calculate_features: 是否计算物理特征
    """
    print("=" * 70)
    print("  数据库迁移: v1 → v2")
    print("=" * 70)
    
    # 1. 连接旧数据库
    print(f"\n1. 连接旧数据库: {old_db_path}")
    old_db = CermetDB(old_db_path)
    
    # 2. 创建新数据库
    print(f"2. 创建新数据库: {new_db_path}")
    new_db = CermetDatabaseV2(new_db_path)
    new_db.create_tables()
    
    # 3. 读取旧数据
    print("\n3. 读取旧数据...")
    df_old = old_db.fetch_data(limit=limit)
    print(f"   总记录数: {len(df_old)}")
    
    if len(df_old) == 0:
        print("⚠️  旧数据库为空，迁移终止")
        return
    
    # 4. 迁移数据
    print(f"\n4. 开始迁移数据...(计算特征: {calculate_features})")
    
    success_count = 0
    fail_count = 0
    errors = []
    
    for idx, row in tqdm(df_old.iterrows(), total=len(df_old), desc="迁移进度"):
        try:
            # 准备数据
            raw_comp = row.get('composition_raw', '')
            if not raw_comp or pd.isna(raw_comp):
                fail_count += 1
                errors.append(f"Row {idx}: missing composition")
                continue
            
            # 添加到新数据库
            exp_id = new_db.add_experiment(
                raw_composition=str(raw_comp),
                source_id=str(row.get('group_id', 'unknown')),
                sinter_temp_c=row.get('sinter_temp_c'),
                grain_size_um=row.get('grain_size_um'),
                sinter_method=str(row.get('sinter_method', '')),
                load_kgf=row.get('load_kgf'),
                hv=row.get('hv'),
                kic=row.get('kic'),
                trs=row.get('trs'),
                binder_vol_pct=row.get('binder_vol_pct'),
                auto_calculate_features=calculate_features
            )
            
            success_count += 1
            
        except Exception as e:
            fail_count += 1
            error_msg = f"Row {idx}: {str(e)}"
            errors.append(error_msg)
    
    # 5. 统计结果
    print("\n" + "=" * 70)
    print("  迁移完成")
    print("=" * 70)
    print(f"✅ 成功: {success_count} 条")
    print(f"❌ 失败: {fail_count} 条")
    
    if errors:
        print(f"\n错误详情 (前10条):")
        for err in errors[:10]:
            print(f"  - {err}")
    
    # 6. 新数据库统计
    stats = new_db.get_statistics()
    print(f"\n新数据库统计:")
    print(f"  总实验数: {stats['total_experiments']}")
    print(f"  HEA 记录: {stats['hea_count']}")
    print(f"  传统记录: {stats['traditional_count']}")
    
    return success_count, fail_count, errors


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='数据库迁移工具 v1→v2')
    parser.add_argument('--old-db', default='cermet_materials.db', help='旧数据库路径')
    parser.add_argument('--new-db', default='cermet_master_v2.db', help='新数据库路径')
    parser.add_argument('--limit', type=int, default=None, help='迁移数据条数限制')
    parser.add_argument('--no-features', action='store_true', help='不计算物理特征（加快速度）')
    
    args = parser.parse_args()
    
    # 执行迁移
    migrate_data(
        old_db_path=args.old_db,
        new_db_path=args.new_db,
        limit=args.limit,
        calculate_features=not args.no_features
    )


if __name__ == '__main__':
    main()
