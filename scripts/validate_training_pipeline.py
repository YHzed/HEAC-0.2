"""
系统性问题验证脚本

功能:
1. 数据泄露检测
2. 时间泄露检测  
3. 特征共线性分析
4. 异常值影响分析

使用:
    python scripts/validate_training_pipeline.py
    
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


def check_data_leakage(df, target='hv'):
    """检查数据泄露"""
    
    print("\n[1/4] 数据泄露检测")
    print("=" * 80)
    
    issues = []
    
    # 检查是否有特征与目标变量完美相关
    target_data = df[target].dropna()
    feature_cols = [col for col in df.columns 
                   if col not in ['hv', 'kic', 'trs', 'youngs_modulus', 'exp_id', 'source_id']]
    
    high_corr_features = []
    for col in feature_cols:
        if col in df.columns and df[col].dtype in ['float64', 'int64']:
            valid_idx = df[col].notna() & target_data.notna()
            if valid_idx.sum() > 10:
                corr = np.corrcoef(df.loc[valid_idx, col], target_data.loc[valid_idx])[0, 1]
                if abs(corr) > 0.95:
                    high_corr_features.append({
                        'feature': col,
                        'correlation': float(corr)
                    })
    
    if high_corr_features:
        print(f"   ⚠️  发现 {len(high_corr_features)} 个高相关特征（|r| > 0.95）:")
        for item in high_corr_features[:10]:
            print(f"      {item['feature']}: r = {item['correlation']:.4f}")
        issues.append({
            'type': 'high_correlation',
            'severity': 'warning',
            'count': len(high_corr_features),
            'features': high_corr_features
        })
    else:
        print(f"   ✅ 未发现完美相关特征")
    
    # 检查特征名称中是否包含目标变量线索
    suspicious_names = [col for col in feature_cols 
                       if any(keyword in col.lower() 
                             for keyword in ['hv', 'hardness', 'kic', 'toughness', 'trs'])]
    
    if suspicious_names:
        print(f"\n   ⚠️  发现 {len(suspicious_names)} 个可疑特征名（包含目标变量关键词）:")
        for name in suspicious_names[:10]:
            print(f"      - {name}")
        issues.append({
            'type': 'suspicious_names',
            'severity': 'warning',
            'features': suspicious_names
        })
    else:
        print(f"   ✅ 特征命名无可疑之处")
    
    return issues


def check_feature_multicollinearity(df, threshold=0.9):
    """检查特征共线性"""
    
    print("\n[2/4] 特征共线性分析")
    print("=" * 80)
    
    feature_cols = [col for col in df.columns 
                   if col not in ['hv', 'kic', 'trs', 'exp_id', 'source_id', 'raw_composition']
                   and df[col].dtype in ['float64', 'int64']]
    
    X = df[feature_cols].fillna(df[feature_cols].median())
    
    print(f"   分析 {len(feature_cols)} 个特征的相关性...")
    
    # 计算相关系数矩阵
    corr_matrix = X.corr().abs()
    
    # 找到高度相关的特征对
    high_corr_pairs = []
    for i in range(len(corr_matrix)):
        for j in range(i+1, len(corr_matrix)):
            if corr_matrix.iloc[i, j] > threshold:
                high_corr_pairs.append({
                    'feature1': corr_matrix.index[i],
                    'feature2': corr_matrix.columns[j],
                    'correlation': float(corr_matrix.iloc[i, j])
                })
    
    if high_corr_pairs:
        print(f"   ⚠️  发现 {len(high_corr_pairs)} 对高度相关特征（|r| > {threshold}）:")
        for pair in sorted(high_corr_pairs, key=lambda x: x['correlation'], reverse=True)[:15]:
            print(f"      {pair['feature1'][:35]:<35} <-> {pair['feature2'][:35]:<35} r = {pair['correlation']:.4f}")
        
        return {
            'high_corr_count': len(high_corr_pairs),
            'pairs': high_corr_pairs,
            'severity': 'warning' if len(high_corr_pairs) > 50 else 'info'
        }
    else:
        print(f"   ✅ 未发现严重共线性问题")
        return {'high_corr_count': 0, 'severity': 'ok'}


def check_outlier_impact(df, target='hv'):
    """检查异常值影响"""
    
    print("\n[3/4] 异常值影响分析")
    print("=" * 80)
    
    target_data = df[target].dropna()
    
    # 使用IQR方法检测异常值
    Q1 = target_data.quantile(0.25)
    Q3 = target_data.quantile(0.75)
    IQR = Q3 - Q1
    
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    
    outliers = target_data[(target_data < lower_bound) | (target_data > upper_bound)]
    outlier_ratio = len(outliers) / len(target_data) * 100
    
    print(f"   目标变量 {target.upper()}:")
    print(f"      范围: [{target_data.min():.1f}, {target_data.max():.1f}]")
    print(f"      IQR范围: [{lower_bound:.1f}, {upper_bound:.1f}]")
    print(f"      异常值数量: {len(outliers)} ({outlier_ratio:.2f}%)")
    
    if outlier_ratio > 5:
        print(f"      ⚠️  异常值比例较高，可能影响模型训练")
        severity = 'warning'
    else:
        print(f"      ✅ 异常值比例正常")
        severity = 'ok'
    
    # 检查极端值
    extreme_values = target_data[target_data < target_data.mean() - 3*target_data.std()]
    if len(extreme_values) > 0:
        print(f"      ⚠️  发现 {len(extreme_values)} 个极端低值（< μ-3σ）")
        print(f"         值: {extreme_values.values[:5]}")
    
    return {
        'outlier_count': int(len(outliers)),
        'outlier_ratio': float(outlier_ratio),
        'lower_bound': float(lower_bound),
        'upper_bound': float(upper_bound),
        'severity': severity,
        'extreme_values': extreme_values.tolist()
    }


def check_data_splitting_strategy(df):
    """检查数据分割策略"""
    
    print("\n[4/4] 数据分割策略检查")
    print("=" * 80)
    
    # 检查是否有时间信息
    has_timestamp = 'created_at' in df.columns or 'updated_at' in df.columns
    
    if has_timestamp:
        print(f"   ⚠️  数据包含时间戳信息")
        print(f"      建议使用时间序列分割验证（TimeSeriesSplit）")
        severity = 'warning'
    else:
        print(f"   ✅ 无时间序列信息，可使用随机分割")
        severity = 'ok'
    
    # 检查是否有重复样本
    key_cols = ['ceramic_formula', 'binder_formula', 'sinter_temp_c', 'grain_size_um']
    available_keys = [col for col in key_cols if col in df.columns]
    
    if available_keys:
        duplicates = df.duplicated(subset=available_keys, keep=False)
        dup_count = duplicates.sum()
        
        if dup_count > 0:
            print(f"   ⚠️  发现 {dup_count} 条可能的重复实验（基于工艺参数）")
            print(f"      建议在分割时考虑去重")
            severity = 'warning'
        else:
            print(f"   ✅ 未发现明显重复实验")
    
    return {
        'has_timestamp': has_timestamp,
        'severity': severity
    }


def main():
    parser = argparse.ArgumentParser(description='验证训练流程的系统性问题')
    parser.add_argument('--data', type=str,
                       default='datasets/exported_training_data.csv',
                       help='训练数据路径')
    parser.add_argument('--target', type=str, default='hv',
                       choices=['hv', 'kic', 'trs'],
                       help='目标变量')
    parser.add_argument('--output', type=str,
                       default='models/systematic_validation_report.json',
                       help='输出报告路径')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("🔍 系统性问题验证脚本")
    print("=" * 80)
    print(f"📁 数据: {args.data}")
    print(f"🎯 目标: {args.target.upper()}")
    print("=" * 80)
    
    # 加载数据
    df = pd.read_csv(args.data)
    print(f"\n✅ 加载 {len(df)} 条记录")
    
    # 执行各项检查
    report = {
        'timestamp': datetime.now().isoformat(),
        'data_path': args.data,
        'target': args.target,
        'sample_count': len(df)
    }
    
    report['data_leakage'] = check_data_leakage(df, target=args.target)
    report['multicollinearity'] = check_feature_multicollinearity(df, threshold=0.9)
    report['outlier_impact'] = check_outlier_impact(df, target=args.target)
    report['data_splitting'] = check_data_splitting_strategy(df)
    
    # 保存报告
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 80)
    print("📊 验证摘要")
    print("=" * 80)
    
    # 统计问题
    total_warnings = 0
    if report['data_leakage']:
        total_warnings += len(report['data_leakage'])
    if report['multicollinearity']['severity'] in ['warning']:
        total_warnings += 1
    if report['outlier_impact']['severity'] == 'warning':
        total_warnings += 1
    if report['data_splitting']['severity'] == 'warning':
        total_warnings += 1
    
    print(f"检测到 {total_warnings} 个潜在问题")
    
    if total_warnings == 0:
        print("✅ 训练流程系统性检查通过！")
    else:
        print("⚠️  建议关注以上警告信息")
    
    print(f"\n📄 详细报告: {output_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
