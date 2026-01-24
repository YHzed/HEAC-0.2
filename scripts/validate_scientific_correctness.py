"""
科学性验证脚本

功能:
1. 物理特征计算验证
2. HEA判定逻辑验证
3. 特征-性能相关性验证
4. 预测合理性验证

使用:
    python scripts/validate_scientific_correctness.py
    
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


def validate_physics_calculations(df):
    """验证物理特征计算"""
    
    print("\n[1/4] 物理特征计算验证")
    print("=" * 80)
    
    issues = []
    
    # 检查lattice mismatch计算
    if 'lattice_mismatch' in df.columns and 'pred_lattice_param' in df.columns:
        lm = df['lattice_mismatch'].dropna()
        print(f"\n   Lattice Mismatch:")
        print(f"      范围: [{lm.min():.4f}, {lm.max():.4f}]")
        print(f"      均值: {lm.mean():.4f}")
        
        # 检查是否有异常值（lattice mismatch应该是小的正数）
        if lm.min() < 0:
            print(f"      ⚠️  发现负值，可能计算有误")
            issues.append({'feature': 'lattice_mismatch', 'issue': 'negative_values'})
        elif lm.max() > 1:
            print(f"      ⚠️  发现过大值（> 1），可能不合理")
            issues.append({'feature': 'lattice_mismatch', 'issue': 'extreme_values'})
        else:
            print(f"      ✅ 数值范围合理")
    
    # 检查VEC （Valence Electron Concentration）
    if 'vec_binder' in df.columns:
        vec = df['vec_binder'].dropna()
        print(f"\n   VEC (Binder):")
        print(f"      范围: [{vec.min():.2f}, {vec.max():.2f}]")
        print(f"      均值: {vec.mean():.2f}")
        
        # VEC通常在4-11范围内
        if vec.min() < 3 or vec.max() > 12:
            print(f"      ⚠️  VEC值超出常见范围（3-12）")
            issues.append({'feature': 'vec_binder', 'issue': 'out_of_range'})
        else:
            print(f"      ✅ VEC范围合理")
    
    # 检查密度
    if 'binder_density' in df.columns:
        density = df['binder_density'].dropna()
        print(f"\n   Binder Density:")
        print(f"      范围: [{density.min():.2f}, {density.max():.2f}] g/cm³")
        print(f"      均值: {density.mean():.2f} g/cm³")
        
        # 金属密度通常在2-20 g/cm³
        if density.min() < 1 or density.max() > 25:
            print(f"      ⚠️  密度值不合理")
            issues.append({'feature': 'binder_density', 'issue': 'unrealistic_values'})
        else:
            print(f"      ✅ 密度范围合理")
    
    # 检查formation energy
    if 'pred_formation_energy' in df.columns:
        fe = df['pred_formation_energy'].dropna()
        print(f"\n   Formation Energy:")
        print(f"      范围: [{fe.min():.4f}, {fe.max():.4f}] eV/atom")
        print(f"      均值: {fe.mean():.4f} eV/atom")
        
        # Formation energy通常是负值（稳定态）
        positive_ratio = (fe > 0).sum() / len(fe) * 100
        if positive_ratio > 10:
            print(f"      ⚠️  {positive_ratio:.1f}% 的值为正（不稳定），比例偏高")
            issues.append({'feature': 'pred_formation_energy', 'issue': 'high_positive_ratio'})
        else:
            print(f"      ✅ Formation energy分布合理")
    
    return issues


def validate_hea_classification(df):
    """验证HEA判定逻辑"""
    
    print("\n[2/4] HEA判定逻辑验证")
    print("=" * 80)
    
    issues = []
    
    if 'is_hea' in df.columns and 'element_count' in df.columns:
        # HEA定义：通常需要 >= 5个元素，且摩尔分数都在5-35%之间
        hea_count = df['is_hea'].sum()
        total_count = len(df)
        
        print(f"   HEA样本: {hea_count} / {total_count} ({hea_count/total_count*100:.1f}%)")
        
        # 分析元素数量分布
        print(f"\n   元素数量分布:")
        for elem_count in sorted(df['element_count'].dropna().unique()):
            count = (df['element_count'] == elem_count).sum()
            hea_in_this = ((df['element_count'] == elem_count) & (df['is_hea'] == True)).sum()
            print(f"      {int(elem_count)}元: {count} 样本, HEA: {hea_in_this}")
        
        # 检查是否有<5元素被标记为HEA
        false_hea = df[(df['element_count'] < 5) & (df['is_hea'] == True)]
        if len(false_hea) > 0:
            print(f"\n      ⚠️  发现 {len(false_hea)} 个<5元素但被标记为HEA的样本")
            issues.append({
                'issue': 'low_element_marked_as_hea',
                'count': len(false_hea),
                'severity': 'error'
            })
        else:
            print(f"\n      ✅ 未发现低元素数误判为HEA")
        
        # 检查二元合金（应该不是HEA）
        binary_alloys = df[df['element_count'] == 2]
        if len(binary_alloys) > 0:
            binary_hea = binary_alloys[binary_alloys['is_hea'] == True]
            if len(binary_hea) > 0:
                print(f"      ❌ 严重错误: {len(binary_hea)} 个二元合金被误判为HEA!")
                issues.append({
                    'issue': 'binary_alloy_as_hea',
                    'count': len(binary_hea),
                    'severity': 'critical'
                })
            else:
                print(f"      ✅ 二元合金未被误判为HEA")
    else:
        print(f"   ⚠️  缺少HEA分类字段，无法验证")
    
    return issues


def validate_feature_correlation(df, target='hv'):
    """验证特征-性能相关性的物理意义"""
    
    print("\n[3/4] 特征-性能相关性验证")
    print("=" * 80)
    
    # 定义预期的相关性
    expected_correlations = {
        'binder_vol_pct': {
            'hv': 'negative',  # 粘结相增加，硬度降低
            'kic': 'positive'   # 粘结相增加，韧性提高
        },
        'grain_size_um': {
            'hv': 'negative',  # Hall-Petch: 晶粒细化提高硬度
            'kic': 'positive'   # 晶粒增大提高韧性
        },
        'sinter_temp_c': {
            'hv': 'positive',  # 烧结温度提高，致密度提高，硬度提高
            'kic': 'uncertain'
        }
    }
    
    issues = []
    
    target_data = df[target].dropna()
    
    print(f"   分析与 {target.upper()} 的相关性:\n")
    
    for feature, expectations in expected_correlations.items():
        if feature in df.columns and target in expectations:
            valid_idx = df[feature].notna() & target_data.notna()
            if valid_idx.sum() > 10:
                corr = np.corrcoef(df.loc[valid_idx, feature], target_data.loc[valid_idx])[0, 1]
                expected = expectations[target]
                
                # 检查相关性是否符合预期
                符合预期 = False
                if expected == 'positive' and corr > 0.1:
                    符合预期 = True
                    status = "✅"
                elif expected == 'negative' and corr < -0.1:
                    符合预期 = True
                    status = "✅"
                elif expected == 'uncertain':
                    符合预期 = True
                    status = "ℹ️"
                else:
                    status = "⚠️"
                    issues.append({
                        'feature': feature,
                        'target': target,
                        'expected': expected,
                        'actual_corr': float(corr),
                        'severity': 'warning'
                    })
                
                print(f"      {status} {feature:<30} r = {corr:>7.4f}  (预期: {expected})")
    
    return issues


def validate_prediction_range(model_path, data_path, feature_list_path):
    """验证预测值合理性"""
    
    print("\n[4/4] 预测合理性验证")
    print("=" * 80)
    
    import joblib
    
    if not os.path.exists(model_path):
        print(f"   ⚠️  模型文件不存在: {model_path}")
        return {}
    
    # 加载模型和特征
    model = joblib.load(model_path)
    
    with open(feature_list_path, 'r') as f:
        features = json.load(f)
    
    # 加载数据
    df = pd.read_csv(data_path)
    df_clean = df.dropna(subset=['hv'])
    
    # 准备数据
    missing_features = [f for f in features if f not in df_clean.columns]
    if missing_features:
        print(f"   ⚠️  缺少 {len(missing_features)} 个特征，跳过验证")
        return {}
    
    X = df_clean[features].fillna(df_clean[features].median())
    y_true = df_clean['hv']
    
    # 预测
    y_pred = model.predict(X)
    
    print(f"   预测值分析:")
    print(f"      真实值范围: [{y_true.min():.1f}, {y_true.max():.1f}]")
    print(f"      预测值范围: [{y_pred.min():.1f}, {y_pred.max():.1f}]")
    
    # 检查预测值是否合理
    issues = []
    
    # 1. 是否有负值
    negative_pred = (y_pred < 0).sum()
    if negative_pred > 0:
        print(f"      ❌ 发现 {negative_pred} 个负值预测（硬度不应为负）")
        issues.append({'issue': 'negative_predictions', 'count': int(negative_pred)})
    else:
        print(f"      ✅ 无负值预测")
    
    # 2. 是否有超出合理范围的值
    # WC-Co硬度通常在1000-2500 HV范围
    unrealistic_low = (y_pred < 500).sum()
    unrealistic_high = (y_pred > 3000).sum()
    
    if unrealistic_low > 0:
        print(f"      ⚠️  {unrealistic_low} 个预测值 < 500 HV（可能过低）")
        issues.append({'issue': 'unrealistic_low', 'count': int(unrealistic_low)})
    
    if unrealistic_high > 0:
        print(f"      ⚠️  {unrealistic_high} 个预测值 > 3000 HV（可能过高）")
        issues.append({'issue': 'unrealistic_high', 'count': int(unrealistic_high)})
    
    if unrealistic_low == 0 and unrealistic_high == 0:
        print(f"      ✅ 预测值范围合理")
    
    return {
        'pred_min': float(y_pred.min()),
        'pred_max': float(y_pred.max()),
        'pred_mean': float(y_pred.mean()),
        'issues': issues
    }


def main():
    parser = argparse.ArgumentParser(description='验证科学性问题')
    parser.add_argument('--data', type=str,
                       default='datasets/exported_training_data.csv',
                       help='训练数据路径')
    parser.add_argument('--model', type=str,
                       default='models/validated/hv_validated_model.pkl',
                       help='训练好的模型路径')
    parser.add_argument('--features', type=str,
                       default='models/validated/hv_feature_list.json',
                       help='特征列表路径')
    parser.add_argument('--output', type=str,
                       default='models/scientific_validation_report.json',
                       help='输出报告路径')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("🔬 科学性验证脚本")
    print("=" * 80)
    print(f"📁 数据: {args.data}")
    print("=" * 80)
    
    # 加载数据
    df = pd.read_csv(args.data)
    print(f"\n✅ 加载 {len(df)} 条记录")
    
    # 执行各项验证
    report = {
        'timestamp': datetime.now().isoformat(),
        'data_path': args.data
    }
    
    report['physics_calculations'] = validate_physics_calculations(df)
    report['hea_classification'] = validate_hea_classification(df)
    report['feature_correlation'] = validate_feature_correlation(df, target='hv')
    
    # 如果模型存在，验证预测
    if os.path.exists(args.model) and os.path.exists(args.features):
        report['prediction_validation'] = validate_prediction_range(
            args.model, args.data, args.features
        )
    else:
        print(f"\n   ⚠️  模型或特征文件不存在，跳过预测验证")
        report['prediction_validation'] = {}
    
    # 保存报告
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # 打印摘要
    print("\n" + "=" * 80)
    print("📊 科学性验证摘要")
    print("=" * 80)
    
    total_issues = 0
    critical_issues = 0
    
    for key, issues in report.items():
        if isinstance(issues, list):
            total_issues += len(issues)
            critical_issues += sum(1 for i in issues if isinstance(i, dict) and i.get('severity') == 'critical')
    
    print(f"发现 {total_issues} 个问题")
    if critical_issues > 0:
        print(f"❌ 其中 {critical_issues} 个严重问题需要立即修复")
    elif total_issues > 0:
        print(f"⚠️  建议关注并改进这些问题")
    else:
        print(f"✅ 科学性检查通过！")
    
    print(f"\n📄 详细报告: {output_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
