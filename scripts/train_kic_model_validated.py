"""
KIC模型训练脚本（增强验证版）

功能:
1. 使用GBFS选定的特征训练KIC模型
2. 实施严格的交叉验证
3. 过拟合检测
4. 生成详细训练报告

使用:
    python scripts/train_kic_model_validated.py
    
作者: HEAC验证流程
日期: 2026-01-15
"""

import sys
import os
import argparse
import pandas as pd
import numpy as np
import joblib
import json
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from xgboost import XGBRegressor
from sklearn.model_selection import KFold, cross_val_score, cross_val_predict
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error


def train_kic_model(data_path, features_path, output_dir='models/validated_kic'):
    """训练KIC预测模型"""
    
    print("=" * 80)
    print("🚀 KIC模型训练脚本（增强验证版）")
    print("=" * 80)
    print(f"📁 数据: {data_path}")
    print(f"🌟 特征配置: {features_path}")
    print(f"💾 输出目录: {output_dir}")
    print("=" * 80)
    
    # 加载数据
    print("\n[1/6] 加载数据...")
    df = pd.read_csv(data_path)
    print(f"✅ 加载 {len(df)} 条记录")
    
    # 加载特征列表
    print("\n[2/6] 加载特征配置...")
    with open(features_path, 'r', encoding='utf-8') as f:
        feature_config = json.load(f)
    
    selected_features = feature_config['selected_features']
    print(f"✅ 使用 {len(selected_features)} 个选定特征")
    
    # 准备训练数据
    print("\n[3/6] 准备训练数据...")
    df_clean = df.dropna(subset=['kic'])
    print(f"   KIC有效记录: {len(df_clean)}")
    
    # 检查特征可用性
    missing_features = [f for f in selected_features if f not in df_clean.columns]
    if missing_features:
        print(f"   ⚠️  数据中缺失 {len(missing_features)} 个特征:")
        for f in missing_features[:5]:
            print(f"      - {f}")
        selected_features = [f for f in selected_features if f in df_clean.columns]
        print(f"   调整后使用 {len(selected_features)} 个特征")
    
    X = df_clean[selected_features].copy()
    y = df_clean['kic'].copy()
    
    # 填充缺失值
    for col in X.columns:
        X[col] = pd.to_numeric(X[col], errors='coerce')
    X = X.fillna(X.median())
    
    print(f"   ✅ 训练集: {len(X)} 样本, {len(selected_features)} 特征")
    print(f"   KIC范围: [{y.min():.1f}, {y.max():.1f}], 均值: {y.mean():.1f}")
    
    # 交叉验证
    print("\n[4/6] 交叉验证训练...")
    
    # 使用XGBoost
    model = XGBRegressor(
        n_estimators=1000,
        learning_rate=0.05,
        max_depth=6,
        subsample=0.8,
        colsample_bytree=0.8,
        n_jobs=-1,
        random_state=42
    )
    
    # 5-Fold交叉验证
    cv = KFold(n_splits=5, shuffle=True, random_state=42)
    
    print("   执行5-Fold交叉验证...")
    y_pred_cv = cross_val_predict(model, X, y, cv=cv, n_jobs=1)
    
    # 计算CV指标
    r2_cv = r2_score(y, y_pred_cv)
    mae_cv = mean_absolute_error(y, y_pred_cv)
    rmse_cv = np.sqrt(mean_squared_error(y, y_pred_cv))
    
    print(f"\n   交叉验证结果:")
    print(f"      R² Score: {r2_cv:.4f}")
    print(f"      MAE: {mae_cv:.4f} MPa·m^1/2")
    print(f"      RMSE: {rmse_cv:.4f} MPa·m^1/2")
    
    # 训练最终模型
    print("\n[5/6] 训练最终模型...")
    model.fit(X, y)
    
    # 训练集评估（检测过拟合）
    y_pred_train = model.predict(X)
    r2_train = r2_score(y, y_pred_train)
    mae_train = mean_absolute_error(y, y_pred_train)
    rmse_train = np.sqrt(mean_squared_error(y, y_pred_train))
    
    print(f"\n   训练集结果:")
    print(f"      R² Score: {r2_train:.4f}")
    print(f"      MAE: {mae_train:.4f} MPa·m^1/2")
    print(f"      RMSE: {rmse_train:.4f} MPa·m^1/2")
    
    # 过拟合检测
    overfitting_ratio = r2_train / r2_cv if r2_cv > 0 else float('inf')
    print(f"\n   过拟合检测:")
    print(f"      R² (Train/CV): {overfitting_ratio:.3f}")
    if overfitting_ratio > 1.1:
        print(f"      ⚠️  可能存在轻度过拟合")
    elif overfitting_ratio > 1.2:
        print(f"      ⚠️⚠️  可能存在中度过拟合")
    else:
        print(f"      ✅ 过拟合风险低")
    
    # 特征重要性
    print("\n   特征重要性（Top 15）:")
    feature_importance = pd.DataFrame({
        'feature': selected_features,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    for idx, row in feature_importance.head(15).iterrows():
        print(f"      {row['feature']:<40} {row['importance']:.4f}")
    
    # 保存模型和结果
    print("\n[6/6] 保存模型和结果...")
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 保存模型
    model_path = output_path / 'kic_validated_model.pkl'
    joblib.dump(model, model_path)
    print(f"   ✅ 模型: {model_path}")
    
    # 保存特征列表
    features_output_path = output_path / 'kic_feature_list.json'
    with open(features_output_path, 'w', encoding='utf-8') as f:
        json.dump(selected_features, f, indent=2, ensure_ascii=False)
    print(f"   ✅ 特征列表: {features_output_path}")
    
    # 保存训练报告
    report = {
        'timestamp': datetime.now().isoformat(),
        'data_path': data_path,
        'sample_count': len(X),
        'feature_count': len(selected_features),
        'target': 'kic',
        'target_stats': {
            'mean': float(y.mean()),
            'std': float(y.std()),
            'min': float(y.min()),
            'max': float(y.max())
        },
        'cv_metrics': {
            'r2': float(r2_cv),
            'mae': float(mae_cv),
            'rmse': float(rmse_cv)
        },
        'train_metrics': {
            'r2': float(r2_train),
            'mae': float(mae_train),
            'rmse': float(rmse_train)
        },
        'overfitting_ratio': float(overfitting_ratio),
        'feature_importance': feature_importance.to_dict('records'),
        'model_params': model.get_params()
    }
    
    report_path = output_path / 'kic_training_report.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"   ✅ 训练报告: {report_path}")
    
    print("\n" + "=" * 80)
    print("✅ 训练完成！")
    print("=" * 80)
    
    return model, report


def main():
    parser = argparse.ArgumentParser(description='训练KIC预测模型（增强验证版）')
    parser.add_argument('--data', type=str,
                       default='datasets/exported_training_data_fixed.csv',
                       help='训练数据路径')
    parser.add_argument('--features', type=str,
                       default='models/selected_features_kic.json',
                       help='特征配置文件路径')
    parser.add_argument('--output', type=str,
                       default='models/validated_kic',
                       help='输出目录')
    
    args = parser.parse_args()
    
    train_kic_model(
        data_path=args.data,
        features_path=args.features,
        output_dir=args.output
    )


if __name__ == "__main__":
    main()
