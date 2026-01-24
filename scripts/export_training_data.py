"""
数据导出脚本 - 从数据库提取完整训练数据

功能:
1. JOIN所有表（experiments + compositions + properties + calculated_features）
2. 导出为CSV格式
3. 生成数据质量报告（缺失值、异常值统计）

使用:
    python scripts/export_training_data.py [--output datasets/exported_training_data.csv]
    
作者: HEAC验证流程
日期: 2026-01-15
"""

import sys
import os
import argparse
import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.db_models import Experiment, Composition, Property, CalculatedFeature
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def export_training_data(db_path='cermet_master_v2.db', output_path='datasets/exported_training_data.csv'):
    """从数据库导出完整训练数据"""
    
    print("=" * 80)
    print("🚀 数据导出脚本")
    print("=" * 80)
    print(f"📁 数据库: {db_path}")
    print(f"💾 输出文件: {output_path}")
    print("=" * 80)
    
    # 连接数据库
    engine = create_engine(f'sqlite:///{db_path}')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    print("\n[1/5] 正在查询数据库...")
    
    # 查询所有实验及其关联数据
    query = session.query(
        # Experiment表
        Experiment.id.label('exp_id'),
        Experiment.source_id,
        Experiment.raw_composition,
        Experiment.sinter_temp_c,
        Experiment.grain_size_um,
        Experiment.sinter_method,
        Experiment.load_kgf,
        
        # Composition表
        Composition.binder_formula,
        Composition.binder_wt_pct,
        Composition.binder_vol_pct,
        Composition.ceramic_formula,
        Composition.ceramic_wt_pct,
        Composition.ceramic_vol_pct,
        Composition.is_hea,
        Composition.element_count,
        
        # Property表
        Property.hv,
        Property.kic,
        Property.trs,
        Property.youngs_modulus,
        Property.hardness_grade,
        Property.toughness_grade,
        
        # CalculatedFeature表
        CalculatedFeature.pred_formation_energy,
        CalculatedFeature.pred_lattice_param,
        CalculatedFeature.pred_magnetic_moment,
        CalculatedFeature.pred_bulk_modulus,
        CalculatedFeature.pred_shear_modulus,
        CalculatedFeature.lattice_mismatch,
        CalculatedFeature.vec_binder,
        CalculatedFeature.mean_atomic_radius,
        CalculatedFeature.binder_density,
        CalculatedFeature.magpie_mean_atomic_mass,
        CalculatedFeature.magpie_std_electronegativity,
        CalculatedFeature.ceramic_magpie_features,
        CalculatedFeature.binder_magpie_features,
        CalculatedFeature.has_matminer,
        CalculatedFeature.has_full_matminer
    ).join(
        Composition, Experiment.id == Composition.exp_id
    ).join(
        Property, Experiment.id == Property.exp_id
    ).outerjoin(  # LEFT JOIN for features (可能缺失)
        CalculatedFeature, Experiment.id == CalculatedFeature.exp_id
    )
    
    # 转换为DataFrame
    df = pd.read_sql(query.statement, session.bind)
    session.close()
    
    print(f"✅ 成功查询 {len(df)} 条记录")
    
    # 展开JSON字段
    print("\n[2/5] 展开JSON特征字段...")
    
    def expand_json_features(df, json_col, prefix):
        """展开JSON列为独立列"""
        if json_col not in df.columns:
            return df
        
        expanded_data = []
        for idx, row in df.iterrows():
            if pd.notna(row[json_col]) and row[json_col]:
                try:
                    if isinstance(row[json_col], str):
                        features = json.loads(row[json_col])
                    else:
                        features = row[json_col]
                    expanded_data.append(features)
                except:
                    expanded_data.append({})
            else:
                expanded_data.append({})
        
        if expanded_data and any(expanded_data):
            expanded_df = pd.DataFrame(expanded_data)
            expanded_df.columns = [f"{prefix}_{col}" for col in expanded_df.columns]
            df = pd.concat([df, expanded_df], axis=1)
        
        return df
    
    df = expand_json_features(df, 'ceramic_magpie_features', 'ceramic_magpie')
    df = expand_json_features(df, 'binder_magpie_features', 'binder_magpie')
    
    # 删除原始JSON列
    df = df.drop(columns=['ceramic_magpie_features', 'binder_magpie_features'], errors='ignore')
    
    print(f"✅ 展开后特征数: {len(df.columns)}")
    
    # 生成数据质量报告
    print("\n[3/5] 生成数据质量报告...")
    
    quality_report = {
        'timestamp': datetime.now().isoformat(),
        'total_records': len(df),
        'total_features': len(df.columns),
        'missing_statistics': {},
        'target_statistics': {},
        'feature_coverage': {}
    }
    
    # 缺失值统计
    missing_stats = df.isnull().sum()
    quality_report['missing_statistics'] = {
        col: {
            'missing_count': int(count),
            'missing_percent': float(count / len(df) * 100)
        }
        for col, count in missing_stats.items() if count > 0
    }
    
    # 目标变量统计
    for target in ['hv', 'kic', 'trs']:
        if target in df.columns:
            valid_data = df[target].dropna()
            quality_report['target_statistics'][target] = {
                'count': int(len(valid_data)),
                'mean': float(valid_data.mean()),
                'std': float(valid_data.std()),
                'min': float(valid_data.min()),
                'max': float(valid_data.max()),
                'missing_count': int(df[target].isnull().sum())
            }
    
    # 特征覆盖率
    quality_report['feature_coverage'] = {
        'has_proxy_features': int(df['pred_formation_energy'].notna().sum()),
        'has_matminer': int(df['has_matminer'].sum()) if 'has_matminer' in df.columns else 0,
        'has_full_matminer': int(df['has_full_matminer'].sum()) if 'has_full_matminer' in df.columns else 0
    }
    
    # 保存数据
    print("\n[4/5] 保存导出数据...")
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_path, index=False)
    print(f"✅ 数据已保存: {output_path}")
    
    # 保存质量报告
    report_path = output_path.replace('.csv', '_quality_report.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(quality_report, f, indent=2, ensure_ascii=False)
    print(f"✅ 质量报告已保存: {report_path}")
    
    # 打印摘要
    print("\n[5/5] 数据质量摘要")
    print("=" * 80)
    print(f"📊 总记录数: {quality_report['total_records']}")
    print(f"📊 总特征数: {quality_report['total_features']}")
    print(f"\n🎯 目标变量统计:")
    for target, stats in quality_report['target_statistics'].items():
        print(f"  {target.upper()}: {stats['count']} 条有效数据 (缺失: {stats['missing_count']})")
        print(f"    范围: [{stats['min']:.2f}, {stats['max']:.2f}], 均值: {stats['mean']:.2f}")
    
    print(f"\n🔬 特征覆盖:")
    print(f"  Proxy特征: {quality_report['feature_coverage']['has_proxy_features']} 条")
    print(f"  简化Matminer: {quality_report['feature_coverage']['has_matminer']} 条")
    print(f"  完整Matminer: {quality_report['feature_coverage']['has_full_matminer']} 条")
    
    print(f"\n⚠️  高缺失率特征 (>50%):")
    high_missing = {k: v for k, v in quality_report['missing_statistics'].items() 
                    if v['missing_percent'] > 50}
    if high_missing:
        for col, stats in sorted(high_missing.items(), key=lambda x: x[1]['missing_percent'], reverse=True)[:10]:
            print(f"  {col}: {stats['missing_percent']:.1f}%")
    else:
        print("  无")
    
    print("\n" + "=" * 80)
    print("✅ 数据导出完成！")
    print("=" * 80)
    
    return df, quality_report


def main():
    parser = argparse.ArgumentParser(description='从数据库导出训练数据')
    parser.add_argument('--db', type=str, default='cermet_master_v2.db',
                       help='数据库文件路径')
    parser.add_argument('--output', type=str, 
                       default='datasets/exported_training_data.csv',
                       help='输出CSV文件路径')
    
    args = parser.parse_args()
    
    export_training_data(db_path=args.db, output_path=args.output)


if __name__ == "__main__":
    main()
