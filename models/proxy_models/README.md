# 辅助模型文件夹

此文件夹存储训练好的辅助模型（Proxy Models），用于预测HEA粘结相的深层物理属性。

## 文件夹结构

```
models/
└── proxy_models/           # 辅助模型存储
    ├── formation_energy_model.pkl      # 形成能预测器
    ├── lattice_model.pkl               # 晶格常数预测器
    ├── magnetic_moment_model.pkl       # 磁矩预测器
    ├── bulk_modulus_model.pkl          # 体模量预测器
    ├── shear_modulus_model.pkl         # 剪切模量预测器
    ├── brittleness_model.pkl           # 脆性指数预测器
    ├── feature_names.pkl               # 特征名称列表
    ├── metrics.pkl                     # 模型评估指标
    └── README.md                       # 本文件
```

## 模型信息

### 训练数据
- **数据源**: Zenodo HEA数据集
- **样本数**: 84,237条
- **特征数**: 250个（Matminer特征化）
- **训练方法**: XGBoost + 5-fold交叉验证

### 模型列表

| 模型文件 | 预测目标 | 单位 | 用途 |
|---------|---------|------|------|
| `formation_energy_model.pkl` | 形成能 | eV/atom | 评估合金稳定性 |
| `lattice_model.pkl` | 晶格常数 | Å | 计算晶格失配 |
| `magnetic_moment_model.pkl` | 磁矩 | μB | 表征电子结构 |
| `bulk_modulus_model.pkl` | 体模量 | GPa | 抗压缩能力 |
| `shear_modulus_model.pkl` | 剪切模量 | GPa | 抗剪切能力 |
| `brittleness_model.pkl` | Pugh比 | B/G | 脆性/韧性指标 |

## 使用方法

### 1. 训练模型

```bash
# 训练所有模型
python scripts/train_proxy_models.py

# 只训练特定模型
python scripts/train_proxy_models.py --models formation lattice magnetic

# 自定义输出目录
python scripts/train_proxy_models.py --output models/proxy_models_v2
```

### 2. 加载和使用模型

```python
from core.feature_injector import FeatureInjector

# 初始化注入器（自动加载模型）
injector = FeatureInjector(model_dir='models/proxy_models')

# 为实验数据注入特征
df_enhanced = injector.inject_features(df, comp_col='binder_composition')
```

### 3. 单独加载模型

```python
import joblib

# 加载单个模型
model = joblib.load('models/proxy_models/formation_energy_model.pkl')

# 预测
predictions = model.predict(X_features)
```

## 模型性能

训练完成后，`metrics.pkl`文件包含每个模型的详细评估指标：
- MAE (Mean Absolute Error)
- RMSE (Root Mean Squared Error)
- R² (R-squared Score)
- MAD (Mean Absolute Deviation)

查看指标：

```python
import joblib
metrics = joblib.load('models/proxy_models/metrics.pkl')
print(metrics)
```

## 更新日志

- **2025-12-18**: 初始版本，训练框架就绪
  - 模型A、B、C使用真实Zenodo数据
  - 模型D、E使用模拟数据（待更新）

## 注意事项

⚠️ **弹性模量和脆性指数模型（D、E）**当前使用模拟数据进行框架测试。真实数据集成计划：
1. Materials Project API查询
2. 经验公式估算
3. 混合策略训练

## 相关文件

- 训练脚本: `scripts/train_proxy_models.py`
- 训练器源码: `core/proxy_models.py`
- 特征注入器: `core/feature_injector.py`
- 实施计划: `.gemini/antigravity/brain/*/implementation_plan.md`
