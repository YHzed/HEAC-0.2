"""
特征选择脚本 - 命令行版GBFS

功能:
1. 读取导出的训练数据
2. 生成复合特征（ceramic-binder交互）
3. 执行GBFS分层聚类特征选择
4. 保存选定的特征列表

使用:
    python scripts/run_feature_selection.py --target hv [--threshold 0.7]
    
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
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
from scipy.stats import spearmanr
from scipy.spatial.distance import squareform

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def generate_composite_features(df):
    """生成ceramic-binder复合特征"""
    
    print("\n[2/5] 生成复合特征...")
    
    df_new = df.copy()
    new_features = []
    
    # 定义ceramic和binder特征配对
    ceramic_features = [col for col in df.columns if col.startswith('ceramic_magpie_')]
    binder_features = [col for col in df.columns if col.startswith('binder_magpie_')]
    
    # 提取共同的特征名（去掉前缀）
    ceramic_base = {col.replace('ceramic_magpie_', ''): col for col in ceramic_features}
    binder_base = {col.replace('binder_magpie_', ''): col for col in binder_features}
    
    common_features = set(ceramic_base.keys()) & set(binder_base.keys())
    
    print(f"   发现 {len(common_features)} 个共同特征可生成复合特征")
    
    # 1. 加权平均特征 (Weighted Average)
    for feat in common_features:
        ceramic_col = ceramic_base[feat]
        binder_col = binder_base[feat]
        
        if ceramic_col in df.columns and binder_col in df.columns:
            # 使用体积百分比作为权重
            if 'ceramic_vol_pct' in df.columns and 'binder_vol_pct' in df.columns:
                df_new[f'Mean_{feat}'] = (
                    df[ceramic_col] * df['ceramic_vol_pct'] / 100 +
                    df[binder_col] * df['binder_vol_pct'] / 100
                )
                new_features.append(f'Mean_{feat}')
    
    # 2. 差异特征 (Difference) - 界面应力、失配
    for feat in common_features:
        ceramic_col = ceramic_base[feat]
        binder_col = binder_base[feat]
        
        if ceramic_col in df.columns and binder_col in df.columns:
            df_new[f'Diff_{feat}'] = abs(df[ceramic_col] - df[binder_col])
            new_features.append(f'Diff_{feat}')
    
    # 3. 比值特征 (Ratio) - 相对关系
    for feat in common_features:
        ceramic_col = ceramic_base[feat]
        binder_col = binder_base[feat]
        
        if ceramic_col in df.columns and binder_col in df.columns:
            # 避免除零
            df_new[f'Ratio_{feat}'] = df[ceramic_col] / (df[binder_col] + 1e-6)
            new_features.append(f'Ratio_{feat}')
    
    # 4. 界面特征 (Interface)
    # 界面复杂度 = Ceramic Vol% * Binder Vol%
    if 'ceramic_vol_pct' in df.columns and 'binder_vol_pct' in df.columns:
        df_new['Interface_Complexity'] = (
            df['ceramic_vol_pct'] * df['binder_vol_pct'] / 10000
        )
        new_features.append('Interface_Complexity')
    
    # 平均自由程 ∝ Grain Size / Binder Vol%
    if 'grain_size_um' in df.columns and 'binder_vol_pct' in df.columns:
        df_new['Mean_Free_Path'] = df['grain_size_um'] / (df['binder_vol_pct'] + 1)
        new_features.append('Mean_Free_Path')
    
    print(f"   ✅ 生成 {len(new_features)} 个复合特征")
    
    return df_new, new_features


def perform_gbfs_clustering(X, y, threshold=0.7, critical_features=None):
    """执行GBFS分层聚类特征选择"""
    
    print("\n[3/5] 执行GBFS分层聚类...")
    
    if critical_features is None:
        critical_features = []
    
    # 先清理数据中的无穷值和NaN
    X_clean = X.copy()
    X_clean = X_clean.replace([np.inf, -np.inf], np.nan)
    X_clean = X_clean.fillna(X_clean.median())
    
    # 计算Spearman相关性矩阵
    print("   计算Spearman相关性矩阵...")
    try:
        corr_matrix, _ = spearmanr(X_clean)
    except Exception as e:
        print(f"   ⚠️  Spearman计算失败: {e}")
        print(f"   使用Pearson相关系数替代...")
        corr_matrix = X_clean.corr().values
    
    # 确保是numpy数组
    if not isinstance(corr_matrix, np.ndarray):
        corr_matrix = np.array(corr_matrix)
    
    # 如果只有一列，corr_matrix是标量，处理特殊情况
    if corr_matrix.ndim == 0:
        corr_matrix = np.array([[1.0]])
    
    # 处理NaN值（用0替换）
    corr_matrix = np.nan_to_num(corr_matrix, nan=0.0, posinf=1.0, neginf=-1.0)
    
    corr_matrix = np.abs(corr_matrix)  # 使用绝对值
    
    # 转换为距离矩阵，确保对称性和有限性
    distance_matrix = 1 - corr_matrix
    # 强制对称（取上三角和下三角的平均）
    distance_matrix = (distance_matrix + distance_matrix.T) / 2
    np.fill_diagonal(distance_matrix, 0)
    
    # 确保所有值都是有限的
    distance_matrix = np.nan_to_num(distance_matrix, nan=1.0, posinf=1.0, neginf=0.0)
    
    # 执行分层聚类
    print("   执行Ward's Linkage聚类...")
    try:
        condensed_dist = squareform(distance_matrix, checks=False)
        linkage_matrix = linkage(condensed_dist, method='ward')
    except Exception as e:
        print(f"   ⚠️  聚类失败: {e}")
        # 降级方案：随机选择特征
        print(f"   使用降级方案：基于相关性排序选择特征...")
        n_features = min(50, len(X.columns))  # 最多选50个
        selected_features = critical_features.copy()
        
        # 计算与目标变量的相关性
        correlations = []
        for col in X.columns:
            if col not in selected_features:
                corr, _ = spearmanr(X[col], y)
                correlations.append((col, abs(corr)))
        
        # 按相关性排序，选择top特征
        correlations.sort(key=lambda x: x[1], reverse=True)
        for col, _ in correlations[:n_features - len(selected_features)]:
            selected_features.append(col)
        
        return selected_features, None, None
    
    # 切割树状图
    cluster_labels = fcluster(linkage_matrix, t=threshold, criterion='distance')
    
    print(f"   聚类阈值: {threshold}")
    print(f"   生成聚类数: {len(np.unique(cluster_labels))}")
    
    # 从每个聚类中选择代表特征
    selected_features = []
    feature_names = X.columns.tolist()
    
    for cluster_id in np.unique(cluster_labels):
        cluster_members = [feature_names[i] for i, label in enumerate(cluster_labels) if label == cluster_id]
        
        # 优先选择关键物理特征
        critical_in_cluster = [f for f in cluster_members if f in critical_features]
        if critical_in_cluster:
            selected_features.append(critical_in_cluster[0])
            continue
        
        # 否则选择与目标变量相关性最高的
        cluster_indices = [i for i, label in enumerate(cluster_labels) if label == cluster_id]
        cluster_X = X.iloc[:, cluster_indices]
        
        correlations = []
        for col in cluster_X.columns:
            corr, _ = spearmanr(cluster_X[col], y)
            correlations.append(abs(corr))
        
        best_idx = np.argmax(correlations)
        selected_features.append(cluster_members[best_idx])
    
    print(f"   ✅ 从 {len(feature_names)} 个特征中选择了 {len(selected_features)} 个")
    
    return selected_features, cluster_labels, linkage_matrix


def main():
    parser = argparse.ArgumentParser(description='GBFS特征选择')
    parser.add_argument('--data', type=str,
                       default='datasets/exported_training_data.csv',
                       help='输入数据路径')
    parser.add_argument('--target', type=str, default='hv',
                       choices=['hv', 'kic', 'trs'],
                       help='目标变量')
    parser.add_argument('--threshold', type=float, default=0.7,
                       help='聚类距离阈值（越低保留特征越多）')
    parser.add_argument('--output', type=str,
                       default='models/selected_features.json',
                       help='输出文件路径')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("🌳 GBFS特征选择脚本")
    print("=" * 80)
    print(f"📁 数据: {args.data}")
    print(f"🎯 目标: {args.target.upper()}")
    print(f"🔧 聚类阈值: {args.threshold}")
    print("=" * 80)
    
    # 加载数据
    print("\n[1/5] 加载数据...")
    df = pd.read_csv(args.data)
    print(f"✅ 加载 {len(df)} 条记录，{len(df.columns)} 个字段")
    
    # 生成复合特征
    df_with_composite, new_features = generate_composite_features(df)
    
    # 准备训练数据
    print("\n[4/5] 准备训练数据...")
    
    # 删除目标变量为空的行
    df_clean = df_with_composite.dropna(subset=[args.target])
    print(f"   目标变量 {args.target}: {len(df_clean)} 条有效记录")
    
    # 选择特征列
    exclude_cols = [
        'exp_id', 'source_id', 'raw_composition', 'sinter_method',
        'binder_formula', 'ceramic_formula', 'hardness_grade', 'toughness_grade',
        'hv', 'kic', 'trs', 'youngs_modulus',  # 目标变量
        'has_matminer', 'has_full_matminer', 'created_at', 'updated_at',
        'is_hea', 'element_count'  # 分类变量
    ]
    
    feature_cols = [col for col in df_clean.columns 
                   if col not in exclude_cols and df_clean[col].dtype in ['float64', 'int64']]
    
    print(f"   候选特征数: {len(feature_cols)}")
    
    # 填充缺失值
    X = df_clean[feature_cols].copy()
    for col in X.columns:
        X[col] = pd.to_numeric(X[col], errors='coerce')
    X = X.fillna(X.median())
    
    y = df_clean[args.target].copy()
    
    # 定义关键物理特征（始终保留）
    critical_physics_features = [
        'pred_formation_energy',
        'pred_lattice_param',
        'lattice_mismatch',
        'pred_magnetic_moment',
        'binder_vol_pct',
        'grain_size_um',
        'sinter_temp_c'
    ]
    
    critical_features = [f for f in critical_physics_features if f in feature_cols]
    
    # 执行GBFS
    selected_features, cluster_labels, linkage_matrix = perform_gbfs_clustering(
        X, y, threshold=args.threshold, critical_features=critical_features
    )
    
    # 保存结果
    print("\n[5/5] 保存结果...")
    
    output_data = {
        'target': args.target,
        'threshold': args.threshold,
        'total_features': len(feature_cols),
        'selected_features': selected_features,
        'selected_count': len(selected_features),
        'critical_features': critical_features,
        'composite_features': new_features,
        'timestamp': pd.Timestamp.now().isoformat()
    }
    
    output_path = Path(args.output)
    output_dir = output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 特征列表已保存: {output_path}")
    
    # 打印摘要
    print("\n" + "=" * 80)
    print("📊 特征选择摘要")
    print("=" * 80)
    print(f"原始特征数: {len(feature_cols)}")
    print(f"复合特征数: {len(new_features)}")
    print(f"选定特征数: {len(selected_features)}")
    print(f"压缩比: {len(selected_features)/len(feature_cols)*100:.1f}%")
    
    print(f"\n🌟 选定的关键特征（前20个）:")
    for i, feat in enumerate(selected_features[:20], 1):
        is_critical = "⭐" if feat in critical_features else "  "
        is_composite = "🧬" if feat in new_features else "  "
        print(f"   {i:2d}. {is_critical} {is_composite} {feat}")
    
    if len(selected_features) > 20:
        print(f"   ... 还有 {len(selected_features)-20} 个特征")
    
    print("\n" + "=" * 80)
    print("✅ 特征选择完成！")
    print("=" * 80)


if __name__ == "__main__":
    main()
