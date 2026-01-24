"""
Top特征选择脚本 - 减少过拟合

从训练报告中提取Top N个最重要特征，确保包含关键物理特征

使用:
    python scripts/select_top_features.py --input models/validated_fixed/hv_training_report.json --top 30
    
作者: HEAC优化流程
日期: 2026-01-15
"""

import sys
import os
import argparse
import json
from pathlib import Path

def select_top_features(report_path, top_n=30, output_path=None):
    """从训练报告中选择Top N特征"""
    
    print("=" * 80)
    print("🎯 Top特征选择脚本")
    print("=" * 80)
    print(f"📁 输入报告: {report_path}")
    print(f"🔢 选择数量: Top {top_n}")
    print("=" * 80)
    
    # 加载训练报告
    with open(report_path, 'r', encoding='utf-8') as f:
        report = json.load(f)
    
    # 提取特征重要性
    feature_importance = report.get('feature_importance', [])
    if not feature_importance:
        print("❌ 训练报告中未找到特征重要性数据")
        return
    
    print(f"\n原始特征数: {len(feature_importance)}")
    
    # 定义关键物理特征（必须保留）
    critical_features = {
        'grain_size_um',
        'binder_vol_pct', 
        'sinter_temp_c',
        'ceramic_vol_pct',
        'lattice_mismatch',
        'vec_binder',
        'pred_formation_energy',
        'pred_lattice_param',
        'pred_magnetic_moment',
        'pred_bulk_modulus',
        'pred_shear_modulus'
    }
    
    # 从重要性列表中找到关键特征
    selected_features = []
    critical_found = []
    
    for feat_info in feature_importance:
        feat_name = feat_info['feature']
        if feat_name in critical_features:
            selected_features.append(feat_name)
            critical_found.append(feat_name)
            if len(selected_features) >= top_n:
                break
    
    # 如果关键特征不够top_n，继续添加其他高重要性特征
    if len(selected_features) < top_n:
        for feat_info in feature_importance:
            feat_name = feat_info['feature']
            if feat_name not in selected_features:
                selected_features.append(feat_name)
                if len(selected_features) >= top_n:
                    break
    
    print(f"\n✅ 选定特征数: {len(selected_features)}")
    print(f"   其中关键物理特征: {len(critical_found)}")
    
    # 显示选定的特征
    print(f"\n🌟 选定的Top {len(selected_features)}特征:")
    for i, feat in enumerate(selected_features, 1):
        # 从原始列表中找到重要性
        importance = next((f['importance'] for f in feature_importance if f['feature'] == feat), 0)
        is_critical = "⭐" if feat in critical_features else "  "
        print(f"   {i:2d}. {is_critical} {feat:<40} {importance:.4f}")
    
    # 创建输出数据
    output_data = {
        'selected_features': selected_features,
        'selected_count': len(selected_features),
        'critical_features': list(critical_found),
        'source_report': report_path,
        'target': report.get('target', 'unknown'),
        'timestamp': report.get('timestamp')
    }
    
    # 保存
    if output_path is None:
        output_path = f"models/selected_features_top{top_n}.json"
    
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 特征列表已保存: {output_path}")
    
    # 统计特征类型
    print(f"\n📊 特征类型分布:")
    categories = {
        '工艺参数': ['grain_size', 'binder_vol', 'ceramic_vol', 'sinter_temp', 'load'],
        'Proxy特征': ['pred_', 'lattice_mismatch', 'vec_binder'],
        'Magpie特征': ['magpie_']
    }
    
    for cat_name, keywords in categories.items():
        count = sum(1 for f in selected_features if any(kw in f.lower() for kw in keywords))
        print(f"   {cat_name}: {count}")
    
    print("\n" + "=" * 80)
    print("✅ 特征选择完成！")
    print("=" * 80)
    
    return output_data


def main():
    parser = argparse.ArgumentParser(description='选择Top N重要特征')
    parser.add_argument('--input', type=str, required=True,
                       help='训练报告JSON文件路径')
    parser.add_argument('--top', type=int, default=30,
                       help='选择前N个特征（默认30）')
    parser.add_argument('--output', type=str, default=None,
                       help='输出JSON文件路径（默认自动生成）')
    
    args = parser.parse_args()
    
    select_top_features(
        report_path=args.input,
        top_n=args.top,
        output_path=args.output
    )


if __name__ == "__main__":
    main()
