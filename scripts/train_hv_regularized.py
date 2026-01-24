"""
深度过拟合优化方案 - 正则化与模型简化

通过多种技术组合进一步降低过拟合：
1. L1/L2正则化
2. 降低模型复杂度
3. Early stopping
4. 数据增强策略

使用:
    python scripts/train_hv_regularized.py --strategy [light|medium|aggressive]
    
作者: HEAC优化流程
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from xgboost import XGBRegressor
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error


def get_regularization_params(strategy='medium'):
    """
    获取正则化参数配置
    
    Args:
        strategy: 'light', 'medium', 'aggressive'
    """
    
    strategies = {
        'light': {
            'name': '轻度正则化',
            'n_estimators': 800,
            'max_depth': 5,
            'learning_rate': 0.05,
            'min_child_weight': 2,
            'gamma': 0.1,
            'reg_alpha': 0.1,  # L1
            'reg_lambda': 0.5,  # L2
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'colsample_bylevel': 1.0,
        },
        'medium': {
            'name': '中度正则化',
            'n_estimators': 600,
            'max_depth': 4,
            'learning_rate': 0.05,
            'min_child_weight': 3,
            'gamma': 0.2,
            'reg_alpha': 0.3,  # L1
            'reg_lambda': 1.0,  # L2
            'subsample': 0.75,
            'colsample_bytree': 0.75,
            'colsample_bylevel': 0.9,
        },
        'aggressive': {
            'name': '激进正则化',
            'n_estimators': 400,
            'max_depth': 3,
            'learning_rate': 0.05,
            'min_child_weight': 5,
            'gamma': 0.5,
            'reg_alpha': 0.5,  # L1
            'reg_lambda': 2.0,  # L2
            'subsample': 0.7,
            'colsample_bytree': 0.7,
            'colsample_bylevel': 0.8,
        }
    }
    
    return strategies.get(strategy, strategies['medium'])


def train_regularized_model(data_path, features_path, strategy='medium', output_dir='models/validated_regularized'):
    """训练正则化的HV模型"""
    
    # 获取参数
    params = get_regularization_params(strategy)
    
    print("=" * 80)
    print(f"🛡️ 正则化HV模型训练 - {params['name']}")
    print("=" * 80)
    print(f"📁 数据: {data_path}")
    print(f"🌟 特征: {features_path}")
    print(f"💾 输出: {output_dir}")
    print("=" * 80)
    
    # 加载数据
    print("\n[1/6] 加载数据...")
    df = pd.read_csv(data_path)
    
    with open(features_path, 'r', encoding='utf-8') as f:
        feature_config = json.load(f)
    selected_features = feature_config['selected_features']
    
    df_clean = df.dropna(subset=['hv'])
    X = df_clean[selected_features].copy()
    y = df_clean['hv'].copy()
    
    for col in X.columns:
        X[col] = pd.to_numeric(X[col], errors='coerce')
    X = X.fillna(X.median())
    
    print(f"✅ {len(X)} 样本, {len(selected_features)} 特征")
    
    # 显示正则化参数
    print(f"\n[2/6] 正则化配置 ({params['name']}):")
    print(f"   树数量: {params['n_estimators']}")
    print(f"   最大深度: {params['max_depth']}")
    print(f"   最小子节点权重: {params['min_child_weight']}")
    print(f"   L1正则(alpha): {params['reg_alpha']}")
    print(f"   L2正则(lambda): {params['reg_lambda']}")
    print(f"   Gamma: {params['gamma']}")
    print(f"   行采样: {params['subsample']}")
    print(f"   列采样(树): {params['colsample_bytree']}")
    
    # 创建模型
    print("\n[3/6] 创建正则化模型...")
    model = XGBRegressor(
        n_estimators=params['n_estimators'],
        max_depth=params['max_depth'],
        learning_rate=params['learning_rate'],
        min_child_weight=params['min_child_weight'],
        gamma=params['gamma'],
        reg_alpha=params['reg_alpha'],
        reg_lambda=params['reg_lambda'],
        subsample=params['subsample'],
        colsample_bytree=params['colsample_bytree'],
        colsample_bylevel=params['colsample_bylevel'],
        n_jobs=-1,
        random_state=42
    )
    
    # 交叉验证
    print("\n[4/6] 交叉验证训练...")
    cv = KFold(n_splits=5, shuffle=True, random_state=42)
    y_pred_cv = cross_val_predict(model, X, y, cv=cv, n_jobs=1)
    
    r2_cv = r2_score(y, y_pred_cv)
    mae_cv = mean_absolute_error(y, y_pred_cv)
    rmse_cv = np.sqrt(mean_squared_error(y, y_pred_cv))
    
    print(f"\n   交叉验证结果:")
    print(f"      R² Score: {r2_cv:.4f}")
    print(f"      MAE: {mae_cv:.4f} HV")
    print(f"      RMSE: {rmse_cv:.4f} HV")
    
    # 训练最终模型
    print("\n[5/6] 训练最终模型...")
    model.fit(X, y)
    
    y_pred_train = model.predict(X)
    r2_train = r2_score(y, y_pred_train)
    mae_train = mean_absolute_error(y, y_pred_train)
    rmse_train = np.sqrt(mean_squared_error(y, y_pred_train))
    
    overfitting_ratio = r2_train / r2_cv if r2_cv > 0 else float('inf')
    
    print(f"\n   训练集结果:")
    print(f"      R² Score: {r2_train:.4f}")
    print(f"      MAE: {mae_train:.4f} HV")
    
    print(f"\n   📊 过拟合评估:")
    print(f"      过拟合比率: {overfitting_ratio:.3f}")
    
    if overfitting_ratio < 1.05:
        print(f"      ✅✅✅ 优秀 - 几乎无过拟合")
    elif overfitting_ratio < 1.10:
        print(f"      ✅✅ 良好 - 轻微过拟合")
    elif overfitting_ratio < 1.20:
        print(f"      ✅ 一般 - 轻度过拟合")
    else:
        print(f"      ⚠️ 仍需优化")
    
    # 保存
    print("\n[6/6] 保存模型...")
    output_path = Path(output_dir) / strategy
    output_path.mkdir(parents=True, exist_ok=True)
    
    joblib.dump(model, output_path / 'hv_regularized_model.pkl')
    
    with open(output_path / 'hv_feature_list.json', 'w', encoding='utf-8') as f:
        json.dump(selected_features, f, indent=2, ensure_ascii=False)
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'strategy': strategy,
        'strategy_name': params['name'],
        'data_path': data_path,
        'sample_count': len(X),
        'feature_count': len(selected_features),
        'target': 'hv',
        'model_params': params,
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
        'overfitting_ratio': float(overfitting_ratio)
    }
    
    with open(output_path / 'hv_training_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"   ✅ 已保存到: {output_path}")
    
    print("\n" + "=" * 80)
    print("✅ 训练完成！")
    print("=" * 80)
    
    return model, report


def main():
    parser = argparse.ArgumentParser(description='训练正则化HV模型')
    parser.add_argument('--data', type=str,
                       default='datasets/exported_training_data_fixed.csv')
    parser.add_argument('--features', type=str,
                       default='models/selected_features_top30.json')
    parser.add_argument('--strategy', type=str, 
                       choices=['light', 'medium', 'aggressive'],
                       default='medium',
                       help='正则化强度：light(轻度)/medium(中度)/aggressive(激进)')
    parser.add_argument('--output', type=str,
                       default='models/validated_regularized')
    
    args = parser.parse_args()
    
    train_regularized_model(
        data_path=args.data,
        features_path=args.features,
        strategy=args.strategy,
        output_dir=args.output
    )


if __name__ == "__main__":
    main()
