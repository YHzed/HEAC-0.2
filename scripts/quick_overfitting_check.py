"""
简化的模型过拟合验证

快速检查过拟合的关键指标：
1. 交叉验证分数的一致性
2. 训练-测试集性能差异
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
import pickle
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import r2_score, mean_absolute_error

print("=" * 80)
print("模型过拟合验证（快速版）")
print("=" * 80)

# 加载数据
print("\n1. 加载训练数据...")
data_file = "training data/zenodo/structure_featurized.dat_all.csv"
df = pd.read_csv(data_file, index_col=0)
print(f"   数据形状: {df.shape}")

# 数据清洗（与训练时一致）
print("\n2. 数据清洗...")
df = df[df['Ef_per_atom'] < 0.5]
print(f"   清洗后: {df.shape}")

# 准备特征（与训练时一致）
print("\n3. 准备特征...")
nfeatures = 273
cols_feat = df.columns[-nfeatures:]
X = df[cols_feat]
X = X.loc[:, X.var() != 0]
print(f"   特征数: {X.shape[1]}")

# 准备目标
y_formation = df['Ef_per_atom']
y_lattice = df['volume_per_atom']

# 磁矩处理
magmom_series = df['magmom'].apply(lambda x: eval(x)[0] if isinstance(x, str) else x)
is_magnetic = (magmom_series.abs() > 0.01)
y_magnetic = magmom_series
X_magnetic = X[is_magnetic]
y_magnetic = y_magnetic[is_magnetic]

print(f"   Formation样本: {len(y_formation)}")
print(f"   Lattice样本: {len(y_lattice)}")
print(f"   Magnetic样本: {len(y_magnetic)} ({is_magnetic.sum()/len(is_magnetic)*100:.1f}%)")

# 加载模型
model_dir = Path("saved_models/proxy")
models = {
    'formation_energy': (X, y_formation),
    'lattice': (X, y_lattice),
    'magnetic_moment': (X_magnetic, y_magnetic)
}

print("\n" + "=" * 80)
print("过拟合检查结果")
print("=" * 80)

for model_name, (X_data, y_data) in models.items():
    model_file = model_dir / f"{model_name}_model.pkl"
    
    if not model_file.exists():
        print(f"\n跳过 {model_name}: 模型文件不存在")
        continue
    
    with open(model_file, 'rb') as f:
        model = pickle.load(f)
    
    print(f"\n{'='*80}")
    print(f"模型: {model_name}")
    print(f"{'='*80}")
    
    # 检查1: 5-Fold交叉验证
    print("\n[检查1] 5-Fold交叉验证稳定性:")
    cv_scores = cross_val_score(model, X_data, y_data, cv=5, scoring='r2', n_jobs=-1)
    
    print(f"  Fold 1-5 R²: {cv_scores}")
    print(f"  均值: {cv_scores.mean():.4f}")
    print(f"  标准差: {cv_scores.std():.4f}")
    
    # 判断
    if cv_scores.std() < 0.03:
        print(f"  ✅ 稳定性优秀 (std={cv_scores.std():.4f} < 0.03)")
    elif cv_scores.std() < 0.05:
        print(f"  ✅ 稳定性良好 (std={cv_scores.std():.4f} < 0.05)")
    elif cv_scores.std() < 0.10:
        print(f"  ⚠️  稳定性一般 (std={cv_scores.std():.4f} < 0.10)")
    else:
        print(f"  ❌ 稳定性较差 (std={cv_scores.std():.4f} > 0.10)")
    
    # 检查2: 训练-测试分割
    print("\n[检查2] 训练集 vs 测试集性能:")
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
    
    # 差异
    r2_diff = r2_train - r2_test
    mae_diff_pct = (mae_test - mae_train) / mae_train * 100
    
    print(f"  训练集: R²={r2_train:.4f}, MAE={mae_train:.4f}")
    print(f"  测试集: R²={r2_test:.4f}, MAE={mae_test:.4f}")
    print(f"  差异:   ΔR²={r2_diff:.4f}, ΔMAE={mae_diff_pct:.1f}%")
    
    # 判断过拟合
    if r2_diff < 0.02:
        print(f"  ✅ 无过拟合迹象 (ΔR²={r2_diff:.4f} < 0.02)")
    elif r2_diff < 0.03:
        print(f"  ✅ 泛化良好 (ΔR²={r2_diff:.4f} < 0.03)")
    elif r2_diff < 0.05:
        print(f"  ⚠️  轻微过拟合 (ΔR²={r2_diff:.4f} < 0.05)")
    else:
        print(f"  ❌ 可能过拟合 (ΔR²={r2_diff:.4f} > 0.05)")
    
    # 检查3: 模型复杂度
    print("\n[检查3] 模型复杂度:")
    if hasattr(model, 'named_steps') and 'regressor' in model.named_steps:
        xgb = model.named_steps['regressor']
        
        print(f"  n_estimators: {xgb.n_estimators}")
        print(f"  max_depth: {xgb.max_depth}")
        print(f"  learning_rate: {xgb.learning_rate}")
        print(f"  reg_lambda: {xgb.reg_lambda:.3f}")
        print(f"  reg_alpha: {xgb.reg_alpha:.3f}")
        
        # 判断
        if xgb.max_depth <= 8 and xgb.reg_lambda >= 0.01:
            print(f"  ✅ 正则化充分 (λ={xgb.reg_lambda:.3f}, depth={xgb.max_depth})")
        elif xgb.max_depth <= 10:
            print(f"  ✅ 复杂度适中")
        else:
            print(f"  ⚠️  模型较为复杂")

# 总结
print("\n" + "=" * 80)
print("验证总结")
print("=" * 80)

print("\n判断标准:")
print("  • CV标准差 < 0.05: 稳定性良好 ✅")
print("  • ΔR² < 0.03: 泛化优秀 ✅")
print("  • ΔR² < 0.05: 轻微过拟合 ⚠️")
print("  • ΔR² > 0.05: 可能过拟合 ❌")

print("\n结论:")
print("  如果所有模型都通过检查1和2，则无过拟合问题。")
print("  如果有警告，考虑增加正则化或减少模型复杂度。")
