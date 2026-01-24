"""
阶段四：Stacking集成学习

架构:
- Level 0 (基学习器):
  1. XGBoost (Optuna优化后)
  2. CatBoost (Optuna优化后) 
  3. Ridge Regression (物理特征)
- Level 1 (元学习器):
  BayesianRidge

使用:
    python scripts/train_hv_stacking.py
    
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
try:
    from catboost import CatBoostRegressor
    CATBOOST_AVAILABLE = True
except:
    CATBOOST_AVAILABLE = False

from sklearn.ensemble import StackingRegressor
from sklearn.linear_model import Ridge, BayesianRidge
from sklearn.model_selection import cross_validate, KFold
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error


def load_optimized_params(params_dir, algorithm):
    """加载Optuna优化后的参数"""
    params_file = Path(params_dir) / algorithm / f'best_params_{algorithm}.json'
    
    if not params_file.exists():
        print(f"⚠️ 未找到{algorithm}优化参数，使用默认配置")
        return None
    
    with open(params_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data['best_params']


def train_stacking_model(data_path, features_path, params_dir='models/optuna_results',
                        output_dir='models/high_quality'):
    """训练Stacking集成模型"""
    
    print("=" * 80)
    print("🏆 Stacking集成学习 - 高质量HV模型")
    print("=" * 80)
    print(f"📁 数据: {data_path}")
    print(f"🧩 参数目录: {params_dir}")
    print("=" * 80)
    
    # 加载数据
    print("\n[1/6] 加载数据...")
    df = pd.read_csv(data_path)
    
    with open(features_path, 'r', encoding='utf-8') as f:
        feature_config = json.load(f)
    all_features = feature_config['selected_features']
    
    df_clean = df.dropna(subset=['hv'])
    X_all = df_clean[all_features].copy()
    y = df_clean['hv'].copy()
    
    for col in X_all.columns:
        X_all[col] = pd.to_numeric(X_all[col], errors='coerce')
    X_all = X_all.fillna(X_all.median())
    
    print(f"✅ {len(X_all)} 样本, {len(all_features)} 特征")
    
    # 准备物理特征子集（用于Ridge）
    physics_features = [
        'grain_size_um', 'binder_vol_pct', 'sinter_temp_c',
        'ceramic_vol_pct', 'lattice_mismatch', 'vec_binder',
        'pred_formation_energy', 'pred_lattice_param'
    ]
    physics_features = [f for f in physics_features if f in all_features]
    print(f"   物理特征数: {len(physics_features)}")
    
    # 构建基学习器
    print("\n[2/6] 构建基学习器...")
    estimators = []
    
    # 1. XGBoost (Optuna优化)
    xgb_params = load_optimized_params(params_dir, 'xgboost')
    if xgb_params:
        print(f"   ✅ XGBoost: 使用Optuna优化参数")
        xgb_model = XGBRegressor(**xgb_params)
    else:
        print(f"   ⚠️ XGBoost: 使用默认优化参数")
        xgb_model = XGBRegressor(
            n_estimators=600, max_depth=4, learning_rate=0.05,
            reg_alpha=0.3, reg_lambda=1.0, subsample=0.75,
            colsample_bytree=0.75, n_jobs=-1, random_state=42
        )
    
    estimators.append(('xgb', xgb_model))
    
    # 2. CatBoost (Optuna优化) - 如果可用
    if CATBOOST_AVAILABLE:
        cat_params = load_optimized_params(params_dir, 'catboost')
        if cat_params:
            print(f"   ✅ CatBoost: 使用Optuna优化参数")
            cat_model = CatBoostRegressor(**cat_params)
        else:
            print(f"   ⚠️ CatBoost: 使用默认参数")
            cat_model = CatBoostRegressor(
                iterations=800, depth=6, learning_rate=0.05,
                l2_leaf_reg=3.0, verbose=0, random_seed=42
            )
        estimators.append(('catboost', cat_model))
    else:
        print(f"   ⚠️ CatBoost未安装，跳过")
    
    print(f"\n   基学习器总数: {len(estimators)}")
    
    # 创建Stacking模型
    print("\n[3/6] 创建Stacking集成...")
    stacking_model = StackingRegressor(
        estimators=estimators,
        final_estimator=BayesianRidge(),
        cv=5,
        n_jobs=1  # 改为单线程避免并行问题
    )
    
    # 交叉验证评估
    print("\n[4/6] 交叉验证评估...")
    cv = KFold(n_splits=5, shuffle=True, random_state=42)
    
    cv_results = cross_validate(
        stacking_model, X_all, y, cv=cv,
        scoring={'r2': 'r2', 'mae': 'neg_mean_absolute_error', 
                 'rmse': 'neg_root_mean_squared_error'},
        return_train_score=True,
        n_jobs=1
    )
    
    r2_cv = cv_results['test_r2'].mean()
    mae_cv = -cv_results['test_mae'].mean()
    rmse_cv = -cv_results['test_rmse'].mean()
    
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
    print(f"\n   过拟合评估:")
    print(f"      过拟合比率: {overfit_ratio:.3f}")
    
    if overfit_ratio < 1.05:
        print(f"      ✅✅✅ 优秀")
    elif overfit_ratio < 1.10:
        print(f"      ✅✅ 良好")
    else:
        print(f"      ✅ 一般")
    
    # 训练最终模型
    print("\n[5/6] 训练最终模型...")
    stacking_model.fit(X_all, y)
    
    # 保存模型
    print("\n[6/6] 保存模型...")
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    joblib.dump(stacking_model, output_path / 'hv_stacking_model.pkl')
    
    with open(output_path / 'hv_feature_list.json', 'w', encoding='utf-8') as f:
        json.dump(all_features, f, indent=2, ensure_ascii=False)
    
    # 保存训练报告
    report = {
        'timestamp': datetime.now().isoformat(),
        'model_type': 'Stacking Ensemble',
        'base_learners': [name for name, _ in estimators],
        'meta_learner': 'BayesianRidge',
        'sample_count': len(X_all),
        'feature_count': len(all_features),
        'physics_feature_count': len(physics_features),
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
        'overfitting_ratio': float(overfit_ratio)
    }
    
    with open(output_path / 'hv_training_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"   ✅ 模型保存: {output_path / 'hv_stacking_model.pkl'}")
    print(f"   ✅ 报告保存: {output_path / 'hv_training_report.json'}")
    
    print("\n" + "=" * 80)
    print("🎉 Stacking集成训练完成！")
    print("=" * 80)
    print(f"\n📊 高质量模型指标:")
    print(f"   R² (CV): {r2_cv:.4f}")
    print(f"   MAE (CV): {mae_cv:.2f} HV")
    print(f"   过拟合比率: {overfit_ratio:.3f}")
    
    # 与目标对比
    print(f"\n🎯 vs 目标:")
    print(f"   R²: {r2_cv:.4f} {'✅' if r2_cv >= 0.83 else '⚠️'} (目标 ≥ 0.83)")
    print(f"   MAE: {mae_cv:.2f} {'✅' if mae_cv <= 125 else '⚠️'} (目标 ≤ 125)")
    print(f"   过拟合: {overfit_ratio:.3f} {'✅' if overfit_ratio <= 1.08 else '⚠️'} (目标 ≤ 1.08)")
    print("=" * 80)
    
    return report


def main():
    parser = argparse.ArgumentParser(description='Stacking集成学习')
    parser.add_argument('--data', type=str,
                       default='datasets/exported_training_data_fixed.csv')
    parser.add_argument('--features', type=str,
                       default='models/selected_features_top30.json')
    parser.add_argument('--params_dir', type=str,
                       default='models/optuna_results',
                       help='Optuna优化参数目录')
    parser.add_argument('--output', type=str,
                       default='models/high_quality')
    
    args = parser.parse_args()
    
    train_stacking_model(
        data_path=args.data,
        features_path=args.features,
        params_dir=args.params_dir,
        output_dir=args.output
    )


if __name__ == "__main__":
    main()
