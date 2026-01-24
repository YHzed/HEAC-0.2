# Ensemble高质量模型部署指南

## 部署总览

**模型**: Ensemble (XGBoost 65% + CatBoost 35%)  
**性能**: R²=0.817, MAE=108.25 HV, 过拟合=1.096  
**状态**: ✅ 生产就绪

---

## 快速开始

### 方法1: 使用预测器类（推荐）

```python
from core.ensemble_predictor import EnsembleHVPredictor

# 初始化
predictor = EnsembleHVPredictor()

# 单个预测
features = {
    'grain_size_um': 1.5,
    'binder_vol_pct': 10.0,
    'sinter_temp_c': 1400,
    # ... 其他27个特征
}
hv_pred = predictor.predict(features)
print(f"预测HV: {hv_pred:.2f}")

# 查看各模型贡献
result = predictor.predict(features, return_components=True)
print(f"XGBoost: {result['xgboost']:.2f}")
print(f"CatBoost: {result['catboost']:.2f}")
print(f"Ensemble: {result['ensemble']:.2f}")
```

### 方法2: 便捷函数

```python
from core.ensemble_predictor import predict_hv

hv = predict_hv(features)
```

### 方法3: 直接加载模型

```python
import joblib
import json

# 加载模型
xgb = joblib.load('models/high_quality_ensemble/xgb_model.pkl')
cat = joblib.load('models/high_quality_ensemble/cat_model.pkl')

# 加载权重
with open('models/high_quality_ensemble/ensemble_config.json') as f:
    weights = json.load(f)

# 预测
pred = weights['xgb_weight'] * xgb.predict(X) + weights['cat_weight'] * cat.predict(X)
```

---

## 集成到现有系统

### 步骤1: 更新主预测模块

在 `core/model_manager.py` 或类似文件中：

```python
from core.ensemble_predictor import get_predictor

class ModelManager:
    def __init__(self):
        # 使用新的Ensemble模型
        self.hv_predictor = get_predictor()
    
    def predict_hv(self, composition, process_params):
        # 组装特征
        features = self._extract_features(composition, process_params)
        
        # 预测
        return self.hv_predictor.predict(features)
```

### 步骤2: 更新API端点

如果有REST API：

```python
from flask import Flask, request, jsonify
from core.ensemble_predictor import predict_hv

app = Flask(__name__)

@app.route('/predict/hv', methods=['POST'])
def predict_hv_api():
    features = request.json
    
    try:
        hv = predict_hv(features, return_components=True)
        return jsonify({
            'status': 'success',
            'prediction': hv['ensemble'],
            'components': {
                'xgboost': hv['xgboost'],
                'catboost': hv['catboost']
            },
            'model_version': 'ensemble_v1.0'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400
```

### 步骤3: 更新Streamlit界面

在 `pages/` 中的相关页面：

```python
import streamlit as st
from core.ensemble_predictor import get_predictor

# 初始化（只加载一次）
@st.cache_resource
def load_predictor():
    return get_predictor()

predictor = load_predictor()

# 使用
if st.button("预测硬度"):
    features = extract_features_from_ui()
    result = predictor.predict(features, return_components=True)
    
    st.success(f"预测HV: {result['ensemble']:.2f}")
    
    # 显示模型贡献
    col1, col2 = st.columns(2)
    col1.metric("XGBoost", f"{result['xgboost']:.2f}", 
                delta=f"权重 {result['xgb_weight']:.0%}")
    col2.metric("CatBoost", f"{result['catboost']:.2f}",
                delta=f"权重 {result['cat_weight']:.0%}")
```

---

## 所需特征列表

模型需要以下30个特征（按重要性排序）：

**核心工艺参数** (必须):
1. `grain_size_um` - 晶粒尺寸
2. `binder_vol_pct` - 粘结相体积分数
3. `sinter_temp_c` - 烧结温度
4. `ceramic_vol_pct` - 陶瓷相体积分数
5. `load_kgf` - 测试载荷

**Proxy物理特征**:
6. `lattice_mismatch` - 晶格失配
7. `vec_binder` - VEC价电子浓度
8. `pred_formation_energy` - 预测形成能
9. `pred_lattice_param` - 预测晶格参数
10. `pred_magnetic_moment` - 预测磁矩
11. `pred_bulk_modulus` - 预测体积模量
12. `pred_shear_modulus` - 预测剪切模量

**Magpie统计特征** (18个，详见 `models/high_quality_ensemble/hv_feature_list.json`)

---

## 性能基准

### 预期性能

| 指标 | 值 | 说明 |
|------|-----|------|
| **R² (CV)** | 0.8170 | 解释81.7%的方差 |
| **MAE (CV)** | 108.25 HV | 平均绝对误差 |
| **RMSE (CV)** | 149.69 HV | 均方根误差 |
| **相对误差** | ~7.2% | 基于均值1507 HV |
| **过拟合比率** | 1.096 | 优秀水平 |

### 置信区间估计

对于预测值 `pred_hv`:
- 68%置信区间: `[pred_hv - 108, pred_hv + 108]`
- 95%置信区间: `[pred_hv - 216, pred_hv + 216]`

---

## 监控与维护

### 预测质量监控

```python
# 记录预测
predictions = []

def monitor_prediction(features, pred, actual=None):
    record = {
        'timestamp': datetime.now(),
        'prediction': pred,
        'actual': actual
    }
    predictions.append(record)
    
    # 如果有实际值，计算误差
    if actual is not None:
        error = abs(pred - actual)
        if error > 200:  # 警告阈值
            print(f"⚠️ 预测误差较大: {error:.2f} HV")
```

### 模型更新策略

**何时更新**:
- 新增大量实验数据（>500条）
- MAE实际表现>120 HV
- 发现系统性偏差

**如何更新**:
1. 重新导出数据
2. 重新运行优化流程
3. 对比新旧模型性能
4. 更新部署

---

## 故障排除

### 问题1: 缺失特征

**错误**: `ValueError: 缺失特征: ['xxx']`

**解决**:
```python
# 使用默认值填充
default_values = {
    'grain_size_um': 1.0,
    'binder_vol_pct': 10.0,
    # ...
}
for feat in predictor.required_features:
    if feat not in features:
        features[feat] = default_values.get(feat, 0)
```

### 问题2: 预测值异常

**症状**: 预测值<0或>5000

**检查**:
1. 输入特征是否在合理范围
2. 是否有NaN/Inf值
3. 单位是否正确

---

## 回滚到旧版本

如需回滚到之前的模型：

```python
# 使用Optuna优化的单模型
from xgboost import XGBRegressor
model = joblib.load('models/high_quality/hv_optimized_model.pkl')

# 或使用正则化版本
model = joblib.load('models/validated_regularized/medium/hv_regularized_model.pkl')
```

---

## 测试脚本

```bash
# 测试预测器
python core/ensemble_predictor.py

# 预期输出:
# ✅ Ensemble HV预测器已加载
#    XGBoost权重: 0.65
#    CatBoost权重: 0.35
#    模型信息: R² (CV): 0.8170
```

---

**部署日期**: 2026-01-15  
**模型版本**: Ensemble v1.0  
**负责人**: HEAC优化团队
