"""
完全手动实现的Ensemble - 无sklearn交叉验证依赖

完全绕过sklearn的cross_val_predict，手动实现K-Fold

使用: python scripts\train_hv_pure_manual_ensemble.py
"""

import pandas as pd
import numpy as np
import json
import joblib
from pathlib import Path
from datetime import datetime
from xgboost import XGBRegressor
from catboost import CatBoostRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

print("=" * 80)
print("🎯 纯手动Ensemble - 完全绕过sklearn CV")
print("=" * 80)

# 加载数据
print("\n[1/7] 加载数据...")
df = pd.read_csv('datasets/exported_training_data_fixed.csv')
with open('models/selected_features_top30.json') as f:
    features = json.load(f)['selected_features']

df_clean = df.dropna(subset=['hv'])
X = df_clean[features].copy()
y = df_clean['hv'].copy()

for col in X.columns:
    X[col] = pd.to_numeric(X[col], errors='coerce')
X = X.fillna(X.median())

print(f"✅ {len(X)} 样本, {len(features)} 特征")

# 加载XGBoost Optuna参数
print("\n[2/7] 加载模型参数...")
with open('models/optuna_results/xgboost/best_params_xgboost.json') as f:
    xgb_params = json.load(f)['best_params']
print("   ✅ XGBoost: Optuna优化参数")
print("   ✅ CatBoost: 默认优化参数")

# 手动实现5-Fold交叉验证
print("\n[3/7] 手动5-Fold交叉验证 - XGBoost...")
n_splits = 5
indices = np.arange(len(X))
np.random.seed(42)
np.random.shuffle(indices)
fold_size = len(X) // n_splits

y_pred_xgb_cv = np.zeros(len(y))

for fold in range(n_splits):
    print(f"   Fold {fold + 1}/5...", end='')
    
    # 分割数据
    val_start = fold * fold_size
    val_end = (fold + 1) * fold_size if fold < n_splits - 1 else len(X)
    val_idx = indices[val_start:val_end]
    train_idx = np.concatenate([indices[:val_start], indices[val_end:]])
    
    X_train = X.iloc[train_idx]
    y_train = y.iloc[train_idx]
    X_val = X.iloc[val_idx]
    
    # 训练并预测
    model = XGBRegressor(**xgb_params)
    model.fit(X_train, y_train, verbose=False)
    y_pred_xgb_cv[val_idx] = model.predict(X_val)
    print(" OK")

r2_xgb = r2_score(y, y_pred_xgb_cv)
mae_xgb = mean_absolute_error(y, y_pred_xgb_cv)
print(f"   R² (XGB): {r2_xgb:.4f}")
print(f"   MAE (XGB): {mae_xgb:.2f} HV")

# CatBoost交叉验证
print("\n[4/7] 手动5-Fold交叉验证 - CatBoost...")
y_pred_cat_cv = np.zeros(len(y))

for fold in range(n_splits):
    print(f"   Fold {fold + 1}/5...", end='')
    
    val_start = fold * fold_size
    val_end = (fold + 1) * fold_size if fold < n_splits - 1 else len(X)
    val_idx = indices[val_start:val_end]
    train_idx = np.concatenate([indices[:val_start], indices[val_end:]])
    
    X_train = X.iloc[train_idx]
    y_train = y.iloc[train_idx]
    X_val = X.iloc[val_idx]
    
    model = CatBoostRegressor(
        iterations=800, depth=6, learning_rate=0.05,
        l2_leaf_reg=3.0, verbose=0, random_seed=42
    )
    model.fit(X_train, y_train, verbose=False)
    y_pred_cat_cv[val_idx] = model.predict(X_val)
    print(" OK")

r2_cat = r2_score(y, y_pred_cat_cv)
mae_cat = mean_absolute_error(y, y_pred_cat_cv)
print(f"   R² (CAT): {r2_cat:.4f}")
print(f"   MAE (CAT): {mae_cat:.2f} HV")

# 优化Ensemble权重
print("\n[5/7] 优化Ensemble权重...")
best_r2 = 0
best_weight = 0.5
best_mae = 999

for w in np.arange(0, 1.05, 0.05):
    y_pred_ens = w * y_pred_xgb_cv + (1 - w) * y_pred_cat_cv
    r2_ens = r2_score(y, y_pred_ens)
    mae_ens = mean_absolute_error(y, y_pred_ens)
    
    if r2_ens > best_r2:
        best_r2 = r2_ens
        best_weight = w
        best_mae = mae_ens

rmse_final = np.sqrt(mean_squared_error(y, best_weight * y_pred_xgb_cv + (1-best_weight) * y_pred_cat_cv))

print(f"   最优权重: XGB={best_weight:.2f}, CAT={1-best_weight:.2f}")
print(f"   Ensemble R²: {best_r2:.4f}")
print(f"   Ensemble MAE: {best_mae:.2f} HV")
print(f"   Ensemble RMSE: {rmse_final:.2f} HV")

# 训练最终模型
print("\n[6/7] 训练最终完整模型...")
xgb_final = XGBRegressor(**xgb_params)
cat_final = CatBoostRegressor(iterations=800, depth=6, learning_rate=0.05, l2_leaf_reg=3.0, verbose=0, random_seed=42)

xgb_final.fit(X, y, verbose=False)
cat_final.fit(X, y, verbose=False)

# 训练集评估
y_pred_xgb_train = xgb_final.predict(X)
y_pred_cat_train = cat_final.predict(X)
y_pred_train_ens = best_weight * y_pred_xgb_train + (1-best_weight) * y_pred_cat_train

r2_train = r2_score(y, y_pred_train_ens)
mae_train = mean_absolute_error(y, y_pred_train_ens)
overfit_ratio = r2_train / best_r2 if best_r2 > 0 else 999

print(f"   R² (Train): {r2_train:.4f}")
print(f"   MAE (Train): {mae_train:.2f} HV")
print(f"   过拟合比率: {overfit_ratio:.3f}")

# 保存模型
print("\n[7/7] 保存模型...")
output_path = Path('models/high_quality_ensemble')
output_path.mkdir(parents=True, exist_ok=True)

joblib.dump(xgb_final, output_path / 'xgb_model.pkl')
joblib.dump(cat_final, output_path / 'cat_model.pkl')

config = {
    'xgb_weight': float(best_weight),
    'cat_weight': float(1 - best_weight),
    'usage': f'pred = {best_weight:.3f} * xgb.predict(X) + {1-best_weight:.3f} * cat.predict(X)'
}

with open(output_path / 'ensemble_config.json', 'w') as f:
    json.dump(config, f, indent=2)

with open(output_path / 'hv_feature_list.json', 'w') as f:
    json.dump(features, f, indent=2, ensure_ascii=False)

report = {
    'timestamp': datetime.now().isoformat(),
    'model_type': 'Manual Ensemble (XGBoost + CatBoost)',
    'ensemble_method': 'Weighted Average - Pure Manual CV',
    'sample_count': len(X),
    'feature_count': len(features),
    'base_models': {
        'xgboost': {'r2_cv': float(r2_xgb), 'mae_cv': float(mae_xgb), 'weight': float(best_weight)},
        'catboost': {'r2_cv': float(r2_cat), 'mae_cv': float(mae_cat), 'weight': float(1-best_weight)}
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

with open(output_path / 'hv_training_report.json', 'w') as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print(f"   ✅ 模型保存: {output_path}")

# 最终总结
print("\n" + "=" * 80)
print("🎉 手动Ensemble训练完成！")
print("=" * 80)
print(f"\n📊 最终性能:")
print(f"   R² (CV): {best_r2:.4f}")
print(f"   MAE (CV): {best_mae:.2f} HV")
print(f"   RMSE (CV): {rmse_final:.2f} HV")
print(f"   过拟合比率: {overfit_ratio:.3f}")

print(f"\n🎯 vs 高质量目标:")
target_r2, target_mae, target_overfit = 0.83, 125, 1.08
print(f"   R²: {best_r2:.4f} {'✅' if best_r2 >= target_r2 else '⚠️'} (目标 ≥ {target_r2})")
print(f"   MAE: {best_mae:.2f} {'✅' if best_mae <= target_mae else '⚠️'} (目标 ≤ {target_mae})")
print(f"   过拟合: {overfit_ratio:.3f} {'✅' if overfit_ratio <= target_overfit else '⚠️'} (目标 ≤ {target_overfit})")

print("\n💡 使用Ensemble模型:")
print(f"   xgb = joblib.load('models/high_quality_ensemble/xgb_model.pkl')")
print(f"   cat = joblib.load('models/high_quality_ensemble/cat_model.pkl')")
print(f"   pred = {best_weight:.3f} * xgb.predict(X) + {1-best_weight:.3f} * cat.predict(X)")
print("=" * 80)
