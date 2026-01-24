"""
使用Optuna优化参数训练最终HV模型

使用:
    python scripts/train_hv_final_optimized.py
    
作者: HEAC高质量优化
日期: 2026-01-15
"""

import sys
import os
import argparse
import pandas as pd
import numpy as np
import json
import joblib
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from xgboost import XGBRegressor
from sklearn.model_selection import cross_validate, cross_val_predict, KFold
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error


def train_final_optimized_model(data_path, features_path, params_path, output_dir='models/high_quality'):
    """使用Optuna优化参数训练最终模型"""
    
    print("=" * 80)
    print("🏆 高质量HV模型训练 - Optuna优化版")
    print("=" * 80)
    print(f"📁 数据: {data_path}")
    print(f"⚙️ 参数: {params_path}")
    print("=" * 80)
    
    # 加载数据
    print("\n[1/5] 加载数据...")
    df = pd.read_csv(data_path)
    
    with open(features_path, 'r', encoding='utf-8') as f:
        feature_config = json.load(f)
    features = feature_config['selected_features']
    
    df_clean = df.dropna(subset=['hv'])
    X = df_clean[features].copy()
    y = df_clean['hv'].copy()
    
    for col in X.columns:
        X[col] = pd.to_numeric(X[col], errors='coerce')
    X = X.fillna(X.median())
    
    print(f"✅ {len(X)} 样本, {len(features)} 特征")
    
    # 加载Optuna优化参数
    print("\n[2/5] 加载Optuna优化参数...")
    with open(params_path, 'r', encoding='utf-8') as f:
        optuna_results = json.load(f)
    
    best_params = optuna_results['best_params']
    print(f"   Optuna最佳参数:")
    for key, value in best_params.items():
        print(f"      {key}: {value}")
    
    print(f"\n   预期性能:")
    print(f"      RMSE (Val): {optuna_results['best_metrics']['rmse_val']:.2f}")
    print(f"      R² (Val): {optuna_results['best_metrics']['r2_val']:.4f}")
    print(f"      过拟合比率: {optuna_results['best_metrics']['overfit_ratio']:.3f}")
    
    # 创建模型
    print("\n[3/5] 创建优化模型...")
    model = XGBRegressor(**best_params)
    
    # 交叉验证评估
    print("\n[4/5] 交叉验证评估...")
    cv = KFold(n_splits=5, shuffle=True, random_state=42)
    
    # 详细CV评估
    cv_results = cross_validate(
        model, X, y, cv=cv,
        scoring={'r2': 'r2', 'mae': 'neg_mean_absolute_error', 
                 'rmse': 'neg_root_mean_squared_error'},
        return_train_score=True,
        n_jobs=1
    )
    
    # CV预测
    y_pred_cv = cross_val_predict(model, X, y, cv=cv, n_jobs=1)
    
    # CV指标
    r2_cv = r2_score(y, y_pred_cv)
    mae_cv = mean_absolute_error(y, y_pred_cv)
    rmse_cv = np.sqrt(mean_squared_error(y, y_pred_cv))
    
    # 训练集指标
    r2_train = cv_results['train_r2'].mean()
    mae_train = -cv_results['train_mae'].mean()
    rmse_train = -cv_results['train_rmse'].mean()
    
    overfit_ratio = r2_train / r2_cv if r2_cv > 0 else float('inf')
    
    print(f"\n   交叉验证结果:")
    print(f"      R² (CV): {r2_cv:.4f}")
    print(f"      MAE (CV): {mae_cv:.2f} HV")
    print(f"      RMSE (CV): {rmse_cv:.2f} HV")
    
    print(f"\n   训练集结果:")
    print(f"      R² (Train): {r2_train:.4f}")
    print(f"      MAE (Train): {mae_train:.2f} HV")
    print(f"      RMSE (Train): {rmse_train:.2f} HV")
    
    print(f"\n   过拟合评估:")
    print(f"      过拟合比率: {overfit_ratio:.3f}")
    
    if overfit_ratio < 1.05:
        status = "✅✅✅ 优秀"
    elif overfit_ratio < 1.10:
        status = "✅✅ 良好"
    elif overfit_ratio < 1.15:
        status = "✅ 一般"
    else:
        status = "⚠️ 需进一步优化"
    print(f"      {status}")
    
    # 训练最终模型
    print("\n[5/5] 训练最终模型...")
    model.fit(X, y)
    
    # 特征重要性
    feature_importance = pd.DataFrame({
        'feature': features,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print(f"\n   特征重要性 (Top 10):")
    for idx, row in feature_importance.head(10).iterrows():
        print(f"      {row['feature']:<40} {row['importance']:.4f}")
    
    # 保存模型
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    joblib.dump(model, output_path / 'hv_optimized_model.pkl')
    
    with open(output_path / 'hv_feature_list.json', 'w', encoding='utf-8') as f:
        json.dump(features, f, indent=2, ensure_ascii=False)
    
    # 保存训练报告
    report = {
        'timestamp': datetime.now().isoformat(),
        'model_type': 'XGBoost (Optuna Optimized)',
        'optimization_method': 'Optuna TPESampler',
        'n_trials': optuna_results['optimization_config']['n_trials'],
        'penalty_factor': optuna_results['optimization_config']['penalty_factor'],
        'sample_count': len(X),
        'feature_count': len(features),
        'best_params': best_params,
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
        'overfitting_ratio': float(overfit_ratio),
        'feature_importance': feature_importance.to_dict('records')
    }
    
    with open(output_path / 'hv_training_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n   ✅ 模型保存: {output_path / 'hv_optimized_model.pkl'}")
    print(f"   ✅ 报告保存: {output_path / 'hv_training_report.json'}")
    
    # 与目标对比
    print("\n" + "=" * 80)
    print("🎯 vs 高质量目标")
    print("=" * 80)
    
    target_r2 = 0.83
    target_mae = 125
    target_overfit = 1.08
    
    r2_status = "✅" if r2_cv >= target_r2 else "⚠️"
    mae_status = "✅" if mae_cv <= target_mae else "⚠️"
    overfit_status = "✅" if overfit_ratio <= target_overfit else "⚠️"
    
    print(f"   R² (CV): {r2_cv:.4f} {r2_status} (目标 ≥ {target_r2})")
    print(f"   MAE (CV): {mae_cv:.2f} HV {mae_status} (目标 ≤ {target_mae})")
    print(f"   过拟合比率: {overfit_ratio:.3f} {overfit_status} (目标 ≤ {target_overfit})")
    
    # 总体评估
    all_pass = (r2_cv >= target_r2) and (mae_cv <= target_mae) and (overfit_ratio <= target_overfit)
    
    print("\n" + "=" * 80)
    if all_pass:
        print("🎉 恭喜！所有目标均已达成！")
    else:
        print("📊 模型质量评估:")
        if r2_cv >= target_r2:
            print("   ✅ 预测精度达标")
        else:
            print(f"   ⚠️ 精度略低于目标 (差距: {target_r2 - r2_cv:.4f})")
        
        if mae_cv <= target_mae:
            print("   ✅ 预测误差达标")
        else:
            print(f"   ⚠️ 误差略高于目标 (差距: {mae_cv - target_mae:.2f} HV)")
        
        if overfit_ratio <= target_overfit:
            print("   ✅ 泛化能力达标")
        else:
            print(f"   ⚠️ 过拟合略高于目标 (差距: {overfit_ratio - target_overfit:.3f})")
    
    print("=" * 80)
    
    return report


def main():
    parser = argparse.ArgumentParser(description='训练Optuna优化的最终模型')
    parser.add_argument('--data', type=str,
                       default='datasets/exported_training_data_fixed.csv')
    parser.add_argument('--features', type=str,
                       default='models/selected_features_top30.json')
    parser.add_argument('--params', type=str,
                       default='models/optuna_results/xgboost/best_params_xgboost.json')
    parser.add_argument('--output', type=str,
                       default='models/high_quality')
    
    args = parser.parse_args()
    
    train_final_optimized_model(
        data_path=args.data,
        features_path=args.features,
        params_path=args.params,
        output_dir=args.output
    )


if __name__ == "__main__":
    main()
