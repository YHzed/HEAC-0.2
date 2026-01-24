"""
阶段三：基于Optuna的自动超参数优化

核心创新：优化目标包含"泛化约束"
- 不单纯追求最小RMSE
- 同时惩罚过拟合(train-val gap)

使用:
    python scripts/optimize_hv_optuna.py --n_trials 100 --algorithm xgboost
    python scripts/optimize_hv_optuna.py --n_trials 100 --algorithm catboost
    
作者: HEAC高质量优化
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import optuna
    from optuna.visualization import plot_optimization_history, plot_param_importances
    OPTUNA_AVAILABLE = True
except ImportError:
    print("⚠️ Optuna未安装，请先安装: pip install optuna")
    OPTUNA_AVAILABLE = False

from xgboost import XGBRegressor
try:
    from catboost import CatBoostRegressor
    CATBOOST_AVAILABLE = True
except ImportError:
    print("⚠️ CatBoost未安装，仅使用XGBoost")
    CATBOOST_AVAILABLE = False

try:
    from lightgbm import LGBMRegressor
    LIGHTGBM_AVAILABLE = True
except ImportError:
    print("⚠️ LightGBM未安装")
    LIGHTGBM_AVAILABLE = False

from sklearn.model_selection import cross_validate, KFold
from sklearn.metrics import mean_squared_error, r2_score


def create_objective(X, y, algorithm='xgboost', penalty_factor=0.5):
    """
    创建带泛化约束的优化目标函数
    
    Args:
        penalty_factor: 过拟合惩罚权重(0-1)
            - 0: 不惩罚过拟合，单纯优化验证集RMSE
            - 0.5: 平衡性能与泛化
            - 1.0: 激进惩罚过拟合
    """
    
    def objective_xgboost(trial):
        params = {
            'n_estimators': trial.suggest_int('n_estimators', 300, 1200),
            'max_depth': trial.suggest_int('max_depth', 3, 8),
            'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.15, log=True),
            'min_child_weight': trial.suggest_int('min_child_weight', 1, 7),
            'gamma': trial.suggest_float('gamma', 0.0, 1.0),
            'reg_alpha': trial.suggest_float('reg_alpha', 0.01, 10.0, log=True),  # L1
            'reg_lambda': trial.suggest_float('reg_lambda', 0.01, 10.0, log=True), # L2
            'subsample': trial.suggest_float('subsample', 0.6, 0.95),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 0.95),
            'colsample_bylevel': trial.suggest_float('colsample_bylevel', 0.7, 1.0),
            'n_jobs': -1,
            'random_state': 42
        }
        
        model = XGBRegressor(**params)
        
        # 5-Fold CV with train score
        cv = KFold(n_splits=5, shuffle=True, random_state=42)
        cv_results = cross_validate(
            model, X, y, cv=cv,
            scoring={'rmse': 'neg_root_mean_squared_error', 'r2': 'r2'},
            return_train_score=True,
            n_jobs=1
        )
        
        rmse_val = -cv_results['test_rmse'].mean()
        rmse_train = -cv_results['train_rmse'].mean()
        
        # 关键：泛化约束Loss
        overfit_gap = rmse_val - rmse_train
        
        # 最终目标 = 验证集RMSE + 惩罚项
        final_loss = rmse_val + (penalty_factor * max(0, overfit_gap))
        
        # 记录额外指标
        trial.set_user_attr('rmse_val', rmse_val)
        trial.set_user_attr('rmse_train', rmse_train)
        trial.set_user_attr('overfit_gap', overfit_gap)
        trial.set_user_attr('overfit_ratio', rmse_train / rmse_val if rmse_val > 0 else 0)
        trial.set_user_attr('r2_val', cv_results['test_r2'].mean())
        
        return final_loss
    
    def objective_catboost(trial):
        params = {
            'iterations': trial.suggest_int('iterations', 300, 1500),
            'depth': trial.suggest_int('depth', 4, 10),
            'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.15, log=True),
            'l2_leaf_reg': trial.suggest_float('l2_leaf_reg', 1.0, 10.0),
            'bagging_temperature': trial.suggest_float('bagging_temperature', 0.0, 1.0),
            'random_strength': trial.suggest_float('random_strength', 0.0, 2.0),
            'border_count': trial.suggest_int('border_count', 32, 255),
            'verbose': 0,
            'random_seed': 42
        }
        
        model = CatBoostRegressor(**params)
        
        cv = KFold(n_splits=5, shuffle=True, random_state=42)
        cv_results = cross_validate(
            model, X, y, cv=cv,
            scoring={'rmse': 'neg_root_mean_squared_error', 'r2': 'r2'},
            return_train_score=True,
            n_jobs=1
        )
        
        rmse_val = -cv_results['test_rmse'].mean()
        rmse_train = -cv_results['train_rmse'].mean()
        overfit_gap = rmse_val - rmse_train
        
        final_loss = rmse_val + (penalty_factor * max(0, overfit_gap))
        
        trial.set_user_attr('rmse_val', rmse_val)
        trial.set_user_attr('rmse_train', rmse_train)
        trial.set_user_attr('overfit_gap', overfit_gap)
        trial.set_user_attr('overfit_ratio', rmse_train / rmse_val if rmse_val > 0 else 0)
        trial.set_user_attr('r2_val', cv_results['test_r2'].mean())
        
        return final_loss
    
    if algorithm == 'xgboost':
        return objective_xgboost
    elif algorithm == 'catboost':
        if not CATBOOST_AVAILABLE:
            raise ValueError("CatBoost未安装")
        return objective_catboost
    else:
        raise ValueError(f"不支持的算法: {algorithm}")


def optimize_hyperparameters(data_path, features_path, algorithm='xgboost', 
                            n_trials=100, penalty_factor=0.5, output_dir='models/optuna_results'):
    """执行Optuna优化"""
    
    if not OPTUNA_AVAILABLE:
        print("❌ Optuna未安装，无法执行优化")
        return
    
    print("=" * 80)
    print(f"🎯 Optuna超参数优化 - {algorithm.upper()}")
    print("=" * 80)
    print(f"📁 数据: {data_path}")
    print(f"🔢 Trial数: {n_trials}")
    print(f"⚖️ 过拟合惩罚系数: {penalty_factor}")
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
    
    # 创建优化目标
    print(f"\n[2/5] 创建优化目标 (算法: {algorithm})...")
    objective = create_objective(X, y, algorithm=algorithm, penalty_factor=penalty_factor)
    
    # 创建Study
    print(f"\n[3/5] 开始优化 ({n_trials} trials)...")
    study = optuna.create_study(
        direction='minimize',
        study_name=f'hv_{algorithm}_optimization',
        sampler=optuna.samplers.TPESampler(seed=42)
    )
    
    # 执行优化
    study.optimize(objective, n_trials=n_trials, show_progress_bar=True)
    
    # 获取最佳参数
    print(f"\n[4/5] 优化完成！")
    best_trial = study.best_trial
    
    print(f"\n   最佳Trial #{best_trial.number}:")
    print(f"      Final Loss: {best_trial.value:.4f}")
    print(f"      RMSE (Val): {best_trial.user_attrs['rmse_val']:.4f}")
    print(f"      RMSE (Train): {best_trial.user_attrs['rmse_train']:.4f}")
    print(f"      Overfit Gap: {best_trial.user_attrs['overfit_gap']:.4f}")
    print(f"      Overfit Ratio: {best_trial.user_attrs['overfit_ratio']:.4f}")
    print(f"      R² (Val): {best_trial.user_attrs['r2_val']:.4f}")
    
    print(f"\n   最佳参数:")
    for key, value in best_trial.params.items():
        print(f"      {key}: {value}")
    
    # 保存结果
    print(f"\n[5/5] 保存结果...")
    output_path = Path(output_dir) / algorithm
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 保存最佳参数
    best_params = {
        'algorithm': algorithm,
        'best_params': best_trial.params,
        'best_metrics': {
            'final_loss': float(best_trial.value),
            'rmse_val': float(best_trial.user_attrs['rmse_val']),
            'rmse_train': float(best_trial.user_attrs['rmse_train']),
            'overfit_gap': float(best_trial.user_attrs['overfit_gap']),
            'overfit_ratio': float(best_trial.user_attrs['overfit_ratio']),
            'r2_val': float(best_trial.user_attrs['r2_val'])
        },
        'optimization_config': {
            'n_trials': n_trials,
            'penalty_factor': penalty_factor
        },
        'timestamp': datetime.now().isoformat()
    }
    
    with open(output_path / f'best_params_{algorithm}.json', 'w', encoding='utf-8') as f:
        json.dump(best_params, f, indent=2, ensure_ascii=False)
    
    print(f"   ✅ 参数保存: {output_path / f'best_params_{algorithm}.json'}")
    
    # 保存Study对象
    import joblib
    joblib.dump(study, output_path / f'optuna_study_{algorithm}.pkl')
    print(f"   ✅ Study保存: {output_path / f'optuna_study_{algorithm}.pkl'}")
    
    print("\n" + "=" * 80)
    print("✅ 优化完成！")
    print("=" * 80)
    print(f"\n📈 性能提升预期:")
    print(f"   当前基准 R²: ~0.816")
    print(f"   优化后 R²: ~{best_trial.user_attrs['r2_val']:.3f}")
    print(f"   过拟合比率: {best_trial.user_attrs['overfit_ratio']:.3f}")
    print("=" * 80)
    
    return best_params


def main():
    parser = argparse.ArgumentParser(description='Optuna超参数优化')
    parser.add_argument('--data', type=str,
                       default='datasets/exported_training_data_fixed.csv')
    parser.add_argument('--features', type=str,
                       default='models/selected_features_top30.json')
    parser.add_argument('--algorithm', type=str, 
                       choices=['xgboost', 'catboost', 'lightgbm'],
                       default='xgboost')
    parser.add_argument('--n_trials', type=int, default=100,
                       help='Optuna试验次数')
    parser.add_argument('--penalty', type=float, default=0.5,
                       help='过拟合惩罚系数(0-1)')
    parser.add_argument('--output', type=str,
                       default='models/optuna_results')
    
    args = parser.parse_args()
    
    optimize_hyperparameters(
        data_path=args.data,
        features_path=args.features,
        algorithm=args.algorithm,
        n_trials=args.n_trials,
        penalty_factor=args.penalty,
        output_dir=args.output
    )


if __name__ == "__main__":
    main()
