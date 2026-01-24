"""
手动Ensemble方案 - 绕过sklearn Stacking API

策略:
1. 训练优化的XGBoost模型
2. 训练优化的CatBoost模型  
3. 手动加权平均预测结果
4. Optuna寻找最优权重

使用:
    python scripts/train_hv_manual_ensemble.py
    
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
from catboost import CatBoostRegressor
from sklearn.model_selection import cross_val_predict, KFold
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error


def train_manual_ensemble(data_path, features_path, xgb_params_path, output_dir='models/high_quality_ensemble'):
    """训练手动Ensemble模型"""
    
    print("=" * 80)
    print("🎯 手动Ensemble - XGBoost + CatBoost")
    print("=" * 80)
    print(f"📁 数据: {data_path}")
    print("=" * 80)
    
    # 加载数据
    print("\n[1/6] 加载数据...")
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
    
    # 加载XGBoost Optuna参数
    print("\n[2/6] 配置模型...")
    with open(xgb_params_path, 'r', encoding='utf-8') as f:
        xgb_optuna = json.load(f)
    xgb_params = xgb_optuna['best_params']
    
    print(f"   ✅ XGBoost: Optuna优化参数")
    print(f"   ✅ CatBoost: 默认优化参数")
    
    # 创建模型
    xgb_model = XGBRegressor(**xgb_params)
    
    cat_model = CatBoostRegressor(
        iterations=800,
        depth=6,
        learning_rate=0.05,
        l2_leaf_reg=3.0,
        verbose=0,
        random_seed=42
    )
    
    # 交叉验证获取预测
    print("\n[3/6] 交叉验证 - XGBoost...")
    cv = KFold(n_splits=5, shuffle=True, random_state=42)
    
    y_pred_xgb = cross_val_predict(xgb_model, X, y, cv=cv, n_jobs=1)
    r2_xgb = r2_score(y, y_pred_xgb)
    mae_xgb = mean_absolute_error(y, y_pred_xgb)
    
    print(f"   R² (XGB): {r2_xgb:.4f}")
    print(f"   MAE (XGB): {mae_xgb:.2f} HV")
    
    print("\n[4/6] 交叉验证 - CatBoost...")
    y_pred_cat = cross_val_predict(cat_model, X, y, cv=cv, n_jobs=1)
    r2_cat = r2_score(y, y_pred_cat)
    mae_cat = mean_absolute_error(y, y_pred_cat)
    
    print(f"   R² (CAT): {r2_cat:.4f}")
    print(f"   MAE (CAT): {mae_cat:.2f} HV")
    
    # 寻找最优权重
    print("\n[5/6] 优化Ensemble权重...")
    best_r2 = 0
    best_weight = 0.5
    best_mae = float('inf')
    
    for w in np.arange(0, 1.05, 0.05):
        y_pred_ensemble = w * y_pred_xgb + (1 - w) * y_pred_cat
        r2_ens = r2_score(y, y_pred_ensemble)
        mae_ens = mean_absolute_error(y, y_pred_ensemble)
        
        if r2_ens > best_r2:
            best_r2 = r2_ens
            best_weight = w
            best_mae = mae_ens
    
    print(f"   最优权重: XGB={best_weight:.2f}, CAT={1-best_weight:.2f}")
    print(f"   Ensemble R²: {best_r2:.4f}")
    print(f"   Ensemble MAE: {best_mae:.2f} HV")
    
    # 最终预测
    y_pred_final = best_weight * y_pred_xgb + (1 - best_weight) * y_pred_cat
    rmse_final = np.sqrt(mean_squared_error(y, y_pred_final))
    
    # 训练最终模型
    print("\n[6/6] 训练最终模型...")
    xgb_model.fit(X, y)
    cat_model.fit(X, y)
    
    # 训练集评估
    y_pred_xgb_train = xgb_model.predict(X)
    y_pred_cat_train = cat_model.predict(X)
    y_pred_train_final = best_weight * y_pred_xgb_train + (1 - best_weight) * y_pred_cat_train
    
    r2_train = r2_score(y, y_pred_train_final)
    mae_train = mean_absolute_error(y, y_pred_train_final)
    
    overfit_ratio = r2_train / best_r2 if best_r2 > 0 else float('inf')
    
    print(f"   R² (Train): {r2_train:.4f}")
    print(f"   过拟合比率: {overfit_ratio:.3f}")
    
    # 保存模型
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    joblib.dump(xgb_model, output_path / 'xgb_model.pkl')
    joblib.dump(cat_model, output_path / 'cat_model.pkl')
    
    ensemble_config = {
        'xgb_weight': float(best_weight),
        'cat_weight': float(1 - best_weight),
        'xgb_model_path': 'xgb_model.pkl',
        'cat_model_path': 'cat_model.pkl'
    }
    
    with open(output_path / 'ensemble_config.json', 'w', encoding='utf-8') as f:
        json.dump(ensemble_config, f, indent=2)
    
    with open(output_path / 'hv_feature_list.json', 'w', encoding='utf-8') as f:
        json.dump(features, f, indent=2, ensure_ascii=False)
    
    # 保存训练报告
    report = {
        'timestamp': datetime.now().isoformat(),
        'model_type': 'Manual Ensemble (XGBoost + CatBoost)',
        'ensemble_method': 'Weighted Average',
        'sample_count': len(X),
        'feature_count': len(features),
        'base_models': {
            'xgboost': {
                'r2_cv': float(r2_xgb),
                'mae_cv': float(mae_xgb),
                'weight': float(best_weight)
            },
            'catboost': {
                'r2_cv': float(r2_cat),
                'mae_cv': float(mae_cat),
                'weight': float(1 - best_weight)
            }
        },
        'ensemble_metrics': {
            'r2_cv': float(best_r2),
            'mae_cv': float(best_mae),
            'rmse_cv': float(rmse_final)
        },
        'train_metrics': {
            'r2': float(r2_train),
            'mae': float(mae_train)
        },
        'overfitting_ratio': float(overfit_ratio)
    }
    
    with open(output_path / 'hv_training_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n   ✅ 模型保存: {output_path}")
    
    # 最终总结
    print("\n" + "=" * 80)
    print("🎉 手动Ensemble训练完成！")
    print("=" * 80)
    print(f"\n📊 Ensemble性能:")
    print(f"   R² (CV): {best_r2:.4f}")
    print(f"   MAE (CV): {best_mae:.2f} HV")
    print(f"   RMSE (CV): {rmse_final:.2f} HV")
    print(f"   过拟合比率: {overfit_ratio:.3f}")
    
    # 与目标对比
    print(f"\n🎯 vs 高质量目标:")
    print(f"   R²: {best_r2:.4f} {'✅' if best_r2 >= 0.83 else '⚠️'} (目标 ≥ 0.83)")
    print(f"   MAE: {best_mae:.2f} {'✅' if best_mae <= 125 else '⚠️'} (目标 ≤ 125)")
    print(f"   过拟合: {overfit_ratio:.3f} {'✅' if overfit_ratio <= 1.08 else '⚠️'} (目标 ≤ 1.08)")
    
    print("\n💡 使用方法:")
    print(f"   pred = {best_weight:.2f} * xgb.predict(X) + {1-best_weight:.2f} * cat.predict(X)")
    print("=" * 80)
    
    return report


def main():
    parser = argparse.ArgumentParser(description='手动Ensemble训练')
    parser.add_argument('--data', type=str,
                       default='datasets/exported_training_data_fixed.csv')
    parser.add_argument('--features', type=str,
                       default='models/selected_features_top30.json')
    parser.add_argument('--xgb_params', type=str,
                       default='models/optuna_results/xgboost/best_params_xgboost.json')
    parser.add_argument('--output', type=str,
                       default='models/high_quality_ensemble')
    
    args = parser.parse_args()
    
    train_manual_ensemble(
        data_path=args.data,
        features_path=args.features,
        xgb_params_path=args.xgb_params,
        output_dir=args.output
    )


if __name__ == "__main__":
    main()
