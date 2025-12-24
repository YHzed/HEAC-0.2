# HEA Cermet 逆向设计系统

一个专注于基于ModelX、ModelY和Proxy模型的智能材料逆向设计系统。

## 特性

- 🎯 **多目标优化**: 同时优化硬度(HV)和断裂韧性(KIC)
- 📊 **Pareto前沿**: 展示所有非支配解
- 🔧 **灵活约束**: 支持元素、工艺等多种约束条件
- 💡 **智能推荐**: 自动排序并推荐最佳设计方案

## 快速开始

### 安装依赖

```bash
pip install streamlit optuna plotly pandas numpy joblib
pip install matminer pymatgen  # 可选，用于Matminer特征
```

### 运行应用

```bash
cd heac_inverse_design/ui
streamlit run inverse_design_app.py
```

## 系统架构

```
heac_inverse_design/
├── core/
│   ├── models/              # 模型封装
│   │   ├── modelx.py        # HV预测
│   │   ├── modely.py        # KIC预测
│   │   └── proxy_models.py  # Proxy模型
│   ├── features/            # 特征提取
│   ├── optimization/        # 优化引擎
│   └── validation/          # 验证模块
└── ui/                      # 用户界面
    └── inverse_design_app.py
```

## 使用示例

```python
from heac_inverse_design import ModelX, ModelY, ProxyModelEnsemble
from heac_inverse_design import FeatureExtractor, InverseDesigner

# 加载模型
modelx = ModelX('models/ModelX.pkl')
modely = ModelY('models/ModelY.pkl')
proxy = ProxyModelEnsemble('models/proxy_models')
extractor = FeatureExtractor()

# 创建逆向设计器
designer = InverseDesigner(modelx, modely, proxy, extractor)

# 执行逆向设计
solutions = designer.design(
    target_hv_range=(1500, 2000),
    target_kic_range=(8.0, 15.0),
    allowed_elements=['Co', 'Ni', 'Fe', 'Cr'],
    n_trials=200
)

# 查看结果
for sol in solutions[:5]:
    print(f"HV: {sol.predicted_hv:.0f}, KIC: {sol.predicted_kic:.2f}")
    print(f"成分: {sol.composition}")
```

## 技术栈

- **ModelX**: XGBoost, R²=0.91 (HV预测)
- **ModelY**: XGBoost, R²=0.76 (KIC预测)
- **Proxy Models**: 形成能、晶格参数、磁矩
- **优化算法**: NSGA-II (via Optuna)
- **UI框架**: Streamlit

## License

MIT
