# 环境整顿与Stacking方案执行指南

## 当前状况

**方案A完成**: Optuna优化XGBoost
- R² (CV): 0.8156 ⚠️ (目标: 0.83)
- MAE (CV): 122.47 ✅ (目标: ≤125)
- 过拟合比率: 1.065 ✅ (目标: ≤1.08)

**问题**: sklearn与CatBoost兼容性冲突，导致Stacking失败

## 方案B：环境整顿

### 步骤1：检查当前版本

```bash
python -c "import sklearn; import catboost; print(f'sklearn: {sklearn.__version__}'); print(f'catboost: {catboost.__version__}')"
```

### 步骤2：推荐版本组合

**方案B-1: 升级CatBoost（推荐）**
```bash
pip install --upgrade catboost
```

**方案B-2: 使用兼容版本组合**
```bash
pip install scikit-learn==1.3.2 catboost==1.2.2
```

### 步骤3：验证兼容性

```bash
python -c "from catboost import CatBoostRegressor; from sklearn.ensemble import StackingRegressor; from sklearn.linear_model import BayesianRidge; print('✅ 兼容性正常')"
```

### 步骤4：重新训练Stacking

```bash
python scripts/train_hv_stacking.py
```

## 预期提升

**Stacking架构**: XGBoost + CatBoost + BayesianRidge元学习器

**预期性能**:
- R² (CV): 0.825 - 0.835 （Ensemble优势）
- MAE (CV): 118 - 123
- 过拟合比率: 1.03 - 1.07 （更稳健）

## 备选方案

如果环境问题难以解决，可采用：

**方案C备用**: 手动Ensemble（无需Stacking API）
- 训练多个独立模型
- 手动加权平均预测结果
- 绕过sklearn Stacking兼容性问题

```python
# 简单加权平均
pred_final = 0.6 * pred_xgb_optuna + 0.4 * pred_catboost
```

---

**下一步**: 
1. 升级CatBoost
2. 重新运行Stacking训练
3. 对比最终性能
