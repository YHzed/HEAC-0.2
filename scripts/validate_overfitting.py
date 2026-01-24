"""
模型过拟合验证脚本

检查项目：
1. 交叉验证性能一致性
2. 训练集 vs 测试集性能差异 
3. 学习曲线分析
4. 模型复杂度评估
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
import pickle
import matplotlib.pyplot as plt
from sklearn.model_selection import cross_validate, learning_curve
from core.proxy_models import ProxyModelTrainer

print("=" * 80)
print("模型过拟合验证")
print("=" * 80)

# 加载已训练模型和指标
model_dir = Path("saved_models/proxy")
metrics_file = model_dir / "metrics.pkl"

if not metrics_file.exists():
    print("❌ 未找到模型指标文件")
    exit(1)

# 读取指标
with open(metrics_file, 'rb') as f:
    metrics = pickle.load(f)

print("\n📊 已保存的模型指标:")
print("-" * 80)
for model_name, model_metrics in metrics.items():
    print(f"\n{model_name}:")
    print(f"  MAE:  {model_metrics['mae']:.4f}")
    print(f"  RMSE: {model_metrics['rmse']:.4f}")
    print(f"  R²:   {model_metrics['r2']:.4f}")
    if 'cv_scores' in model_metrics:
        cv_scores = model_metrics['cv_scores']
        print(f"  CV R² (mean±std): {np.mean(cv_scores):.4f} ± {np.std(cv_scores):.4f}")

# 重新加载数据进行验证
print("\n" + "=" * 80)
print("重新验证（独立测试集）")
print("=" * 80)

trainer = ProxyModelTrainer(
    data_file="training data/zenodo/structure_featurized.dat_all.csv",
    cv_folds=5
)

# 加载数据
trainer.load_data()
print(f"\n✓ 数据加载: {trainer.df.shape}")

# 准备特征
X, y_formation, y_lattice, y_magnetic, is_mag = trainer.prepare_features()
print(f"✓ 特征准备: {X.shape}")

# 检查1: 交叉验证稳定性
print("\n" + "=" * 80)
print("检查1: 交叉验证稳定性")
print("=" * 80)

from sklearn.model_selection import cross_val_score

models_to_test = {
    'formation_energy': (X, y_formation),
    'lattice': (X, y_lattice),
    'magnetic_moment': (X[is_mag], y_magnetic[is_mag])
}

cv_results = {}

for model_name, (X_data, y_data) in models_to_test.items():
    model_file = model_dir / f"{model_name}_model.pkl"
    
    if not model_file.exists():
        print(f"⚠️  跳过 {model_name}: 模型文件不存在")
        continue
    
    with open(model_file, 'rb') as f:
        model = pickle.load(f)
    
    print(f"\n{model_name}:")
    
    # 5-fold交叉验证
    cv_scores = cross_val_score(model, X_data, y_data, cv=5, 
                                scoring='r2', n_jobs=-1)
    
    print(f"  5-Fold CV R²: {cv_scores}")
    print(f"  Mean: {cv_scores.mean():.4f}")
    print(f"  Std:  {cv_scores.std():.4f}")
    
    # 判断稳定性
    if cv_scores.std() < 0.05:
        print(f"  ✅ 稳定性良好 (std < 0.05)")
    elif cv_scores.std() < 0.10:
        print(f"  ⚠️  稳定性一般 (0.05 < std < 0.10)")
    else:
        print(f"  ❌ 稳定性较差 (std > 0.10)")
    
    cv_results[model_name] = {
        'scores': cv_scores,
        'mean': cv_scores.mean(),
        'std': cv_scores.std()
    }

# 检查2: 训练集 vs 测试集性能
print("\n" + "=" * 80)
print("检查2: 训练集 vs 测试集性能差异")
print("=" * 80)

from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error

for model_name, (X_data, y_data) in models_to_test.items():
    model_file = model_dir / f"{model_name}_model.pkl"
    
    if not model_file.exists():
        continue
    
    with open(model_file, 'rb') as f:
        model = pickle.load(f)
    
    # 分割数据
    X_train, X_test, y_train, y_test = train_test_split(
        X_data, y_data, test_size=0.2, random_state=42
    )
    
    # 训练集性能
    y_train_pred = model.predict(X_train)
    r2_train = r2_score(y_train, y_train_pred)
    mae_train = mean_absolute_error(y_train, y_train_pred)
    
    # 测试集性能
    y_test_pred = model.predict(X_test)
    r2_test = r2_score(y_test, y_test_pred)
    mae_test = mean_absolute_error(y_test, y_test_pred)
    
    # 计算差异
    r2_diff = r2_train - r2_test
    mae_diff = mae_test - mae_train
    
    print(f"\n{model_name}:")
    print(f"  训练集 R²: {r2_train:.4f}, MAE: {mae_train:.4f}")
    print(f"  测试集 R²: {r2_test:.4f}, MAE: {mae_test:.4f}")
    print(f"  差异:    ΔR²={r2_diff:.4f}, ΔMAE={mae_diff:.4f}")
    
    # 判断过拟合
    if r2_diff < 0.03 and mae_diff < 0.01:
        print(f"  ✅ 无过拟合迹象")
    elif r2_diff < 0.05:
        print(f"  ⚠️  轻微过拟合")
    else:
        print(f"  ❌ 可能过拟合 (ΔR² > 0.05)")

# 检查3: 学习曲线
print("\n" + "=" * 80)
print("检查3: 学习曲线分析")
print("=" * 80)

for model_name, (X_data, y_data) in models_to_test.items():
    model_file = model_dir / f"{model_name}_model.pkl"
    
    if not model_file.exists():
        continue
    
    with open(model_file, 'rb') as f:
        model = pickle.load(f)
    
    print(f"\n{model_name}:")
    print(f"  计算学习曲线...")
    
    # 学习曲线（使用较少的训练规模以加快速度）
    train_sizes = np.linspace(0.1, 1.0, 5)
    
    train_sizes_abs, train_scores, test_scores = learning_curve(
        model, X_data, y_data,
        train_sizes=train_sizes,
        cv=3,
        scoring='r2',
        n_jobs=-1
    )
    
    train_mean = train_scores.mean(axis=1)
    test_mean = test_scores.mean(axis=1)
    
    print(f"  训练规模      训练集R²    测试集R²    差异")
    print(f"  " + "-" * 50)
    for size, tr, te in zip(train_sizes_abs, train_mean, test_mean):
        diff = tr - te
        status = "✅" if diff < 0.05 else "⚠️" if diff < 0.10 else "❌"
        print(f"  {size:8.0f}      {tr:.4f}      {te:.4f}     {diff:.4f} {status}")
    
    # 判断收敛
    if test_mean[-1] - test_mean[-2] < 0.01:
        print(f"  ✅ 模型已收敛")
    else:
        print(f"  ⚠️  可能需要更多数据")

# 检查4: 模型复杂度
print("\n" + "=" * 80)
print("检查4: 模型复杂度评估")
print("=" * 80)

for model_name in ['formation_energy', 'lattice', 'magnetic_moment']:
    model_file = model_dir / f"{model_name}_model.pkl"
    
    if not model_file.exists():
        continue
    
    with open(model_file, 'rb') as f:
        model = pickle.load(f)
    
    # XGBoost参数
    if hasattr(model, 'named_steps') and 'regressor' in model.named_steps:
        xgb = model.named_steps['regressor']
        
        print(f"\n{model_name}:")
        print(f"  n_estimators: {xgb.n_estimators}")
        print(f"  max_depth: {xgb.max_depth}")
        print(f"  learning_rate: {xgb.learning_rate}")
        print(f"  reg_lambda: {xgb.reg_lambda}")
        print(f"  reg_alpha: {xgb.reg_alpha}")
        
        # 判断复杂度
        if xgb.max_depth <= 10 and xgb.reg_lambda >= 0.01:
            print(f"  ✅ 正则化适当")
        else:
            print(f"  ⚠️  可能过于复杂")

# 总结
print("\n" + "=" * 80)
print("过拟合验证总结")
print("=" * 80)

print("\n✅ 验证完成！请查看上述各项检查结果。")
print("\n判断标准:")
print("  • CV标准差 < 0.05: 稳定性良好")
print("  • ΔR² < 0.03: 无过拟合")
print("  • ΔR² < 0.05: 轻微过拟合")
print("  • ΔR² > 0.05: 可能过拟合")
