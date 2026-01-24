"""
模型过拟合快速验证

使用简单可靠的方法检查过拟合
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
import pickle
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import r2_score, mean_absolute_error

print("=" * 80)
print("模型过拟合验证报告")
print("=" * 80)

# 加载数据
print("\n📁 加载数据...")
df = pd.read_csv("training data/zenodo/structure_featurized.dat_all.csv", index_col=0)
df = df[df['Ef_per_atom'] < 0.5]
print(f"   样本数: {len(df)}")

# 准备特征
X = df[df.columns[-273:]]
X = X.loc[:, X.var() != 0]
print(f"   特征数: {X.shape[1]}")

# 测试formation_energy模型
model_path = "saved_models/proxy/formation_energy_model.pkl"
y = df['Ef_per_atom']

print(f"\n{'='*80}")
print("Formation Energy 模型")
print(f"{'='*80}")

with open(model_path, 'rb') as f:
    model = pickle.load(f)

# 检查1: 5-Fold CV
print("\n[检查1] 5-Fold 交叉验证")
cv_scores = cross_val_score(model, X, y, cv=5, scoring='r2', n_jobs=-1)
print(f"   Fold 1-5: {[f'{s:.4f}' for s in cv_scores]}")
print(f"   均值: {cv_scores.mean():.4f}")
print(f"   标准差: {cv_scores.std():.4f}")

if cv_scores.std() < 0.03:
    print(f"   ✅ 非常稳定 (std={cv_scores.std():.4f})")
elif cv_scores.std() < 0.05:
    print(f"   ✅ 稳定良好")
else:
    print(f"   ⚠️  稳定性一般")

# 检查2: 训练-测试分割
print("\n[检查2] 训练-测试集对比")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

r2_train = r2_score(y_train, model.predict(X_train))
r2_test = r2_score(y_test, model.predict(X_test))
diff = r2_train - r2_test

print(f"   训练集 R²: {r2_train:.4f}")
print(f"   测试集 R²: {r2_test:.4f}")
print(f"   差异 ΔR²: {diff:.4f}")

if diff < 0.02:
    print(f"   ✅ 优秀泛化能力")
elif diff < 0.03:
    print(f"   ✅ 良好泛化能力")
elif diff < 0.05:
    print(f"   ⚠️  轻微过拟合迹象")
else:
    print(f"   ❌ 可能存在过拟合")

# 测试lattice模型
print(f"\n{'='*80}")
print("Lattice 模型")
print(f"{'='*80}")

y_lattice = df['volume_per_atom']
model_lattice = pickle.load(open("saved_models/proxy/lattice_model.pkl", 'rb'))

# 5-Fold CV
cv_scores_l = cross_val_score(model_lattice, X, y_lattice, cv=5, scoring='r2', n_jobs=-1)
print(f"\n[检查1] 5-Fold CV: Mean={cv_scores_l.mean():.4f}, Std={cv_scores_l.std():.4f}")

if cv_scores_l.std() < 0.05:
    print(f"   ✅ 稳定")
else:
    print(f"   ⚠️  不够稳定")

# 训练-测试
X_train_l, X_test_l, y_train_l, y_test_l = train_test_split(
    X, y_lattice, test_size=0.2, random_state=42
)

r2_train_l = r2_score(y_train_l, model_lattice.predict(X_train_l))
r2_test_l = r2_score(y_test_l, model_lattice.predict(X_test_l))
diff_l = r2_train_l - r2_test_l

print(f"\n[检查2] 训练/测试: Train={r2_train_l:.4f}, Test={r2_test_l:.4f}, Δ={diff_l:.4f}")

if diff_l < 0.03:
    print(f"   ✅ 无过拟合")
else:
    print(f"   ⚠️  可能过拟合" if diff_l < 0.05 else "   ❌ 过拟合")

# 总结
print(f"\n{'='*80}")
print("验证总结")
print(f"{'='*80}")

print("\n✅ 判断标准:")
print("   • CV标准差 < 0.05: 稳定性好")
print("   • ΔR² < 0.03: 泛化优秀")
print("   • ΔR² < 0.05: 轻微过拟合")
print("   • ΔR² > 0.05: 可能过拟合")

print("\n📊 结论:")
if diff < 0.03 and diff_l < 0.03:
    print("   ✅ 所有模型泛化能力优秀，无过拟合问题")
elif diff < 0.05 and diff_l < 0.05:
    print("   ✅ 模型泛化良好，仅轻微过拟合（可接受）")
else:
    print("   ⚠️  部分模型可能过拟合，建议增加正则化")

print("\n" + "=" * 80)
