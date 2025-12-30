# HEAC 0.2 - 高熵合金陶瓷智能设计平台

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Streamlit](https://img.shields.io/badge/streamlit-1.30%2B-red)

*一个集成数据处理、机器学习、逆向设计的高熵合金陶瓷(HEA Cermet)材料研发平台*

</div>

---

## 📋 目录

- [项目简介](#-项目简介)
- [核心特性](#-核心特性)
- [系统架构](#-系统架构)
- [快速开始](#-快速开始)
- [功能模块](#-功能模块)
- [安装指南](#-安装指南)
- [使用教程](#-使用教程)
- [API参考](#-api参考)
- [常见问题](#-常见问题)
- [贡献指南](#-贡献指南)
- [许可证](#-许可证)

---

## 🎯 项目简介

**HEAC 0.2** 是一个专为高熵合金陶瓷(High Entropy Alloy Cermet)材料研发设计的智能平台。项目整合了先进的机器学习算法、物理模型和材料数据库,为材料科学家和工程师提供从数据处理、特征工程、模型训练到逆向设计的全流程解决方案。

### 🎓 适用领域

- 高熵合金陶瓷材料设计与优化
- 材料性能预测(硬度、断裂韧性等)
- 多目标材料优化
- 材料数据库管理与查询
- 机器学习模型训练与解释

---

## ✨ 核心特性

### 🔬 材料科学
- **物理计算引擎**: 集成密度计算、平均自由程、晶格失配等物理模型
- **Materials Project集成**: 自动获取晶体结构、形成能、磁矩等材料属性
- **Proxy模型**: 预测形成能、晶格参数、磁矩等关键物理量
- **成分解析**: 智能解析复杂的合金陶瓷成分表示

### 🤖 机器学习
- **多算法支持**: XGBoost, LightGBM, CatBoost, Random Forest等
- **自动特征工程**: 基于Matminer的高级特征提取
- **GBFS特征选择**: 基于梯度提升的分层特征选择算法
- **模型可解释性**: SHAP分析、特征重要性评估
- **超参数优化**: 集成Optuna进行自动调参

### 🎨 交互式界面
- **模块化设计**: 12+专业功能页面
- **实时可视化**: Plotly交互式图表
- **数据管理**: 完整的数据上传、预处理、标准化工作流
- **模型管理**: 模型训练、保存、加载和版本控制

### 🔮 逆向设计
- **多目标优化**: 同时优化硬度(HV)和断裂韧性(KIC)
- **Pareto前沿**: 展示非支配解集合
- **约束优化**: 支持元素、工艺、成分等多种约束
- **智能推荐**: 自动排序并推荐最佳设计方案

---

## 🏗️ 系统架构

### 项目结构

```
HEAC-0.2/
├── app.py                          # Streamlit主应用入口
├── core/                           # 核心功能模块
│   ├── __init__.py
│   ├── physics_calculator.py       # 物理计算引擎
│   ├── hea_calculator.py           # HEA专用计算器
│   ├── hea_data_processor.py       # HEA数据处理器
│   ├── composition_parser.py       # 成分解析器
│   ├── feature_injector.py         # 特征注入引擎
│   ├── proxy_models.py             # Proxy模型预测
│   ├── modelx_adapter.py           # ModelX适配器(HV预测)
│   ├── materials_project_client.py # Materials Project API客户端
│   ├── data_processor.py           # 通用数据处理
│   ├── data_standardizer.py        # 数据标准化
│   ├── models.py                   # 机器学习模型工厂
│   ├── virtual_screening.py        # 虚拟筛选引擎
│   ├── db_manager.py              # 数据库管理
│   ├── db_models_v2.py            # 数据库模型(V2)
│   └── ...
├── pages/                          # Streamlit页面
│   ├── 1_General_ML_Lab.py        # 通用机器学习实验室
│   ├── 2_HEA_Cermet_Lab.py        # HEA陶瓷实验室
│   ├── 3_Cermet_Library.py        # 陶瓷材料库
│   ├── 4_Literature_Lab.py        # 文献实验室
│   ├── 5_Process_Agent.py         # 数据处理代理
│   ├── 6_GBFS_Feature_Selection.py # GBFS特征选择
│   ├── 6_Proxy_Models.py          # Proxy模型页面
│   ├── 7_Model_Training.py        # 模型训练页面
│   ├── 8_Virtual_Screening.py     # 虚拟筛选页面
│   ├── 9_HEA_Data_Preprocessing.py # HEA数据预处理
│   ├── 10_Database_Manager.py     # 数据库管理器
│   └── 11_Database_Manager_V2.py  # 数据库管理器V2
├── heac_inverse_design/            # 逆向设计系统
│   ├── core/                       # 逆向设计核心
│   └── ui/                         # 逆向设计UI
├── datasets/                       # 数据集文件
├── models/                         # 训练好的模型
├── training data/                  # 训练数据
├── scripts/                        # 辅助脚本
├── tests/                          # 测试文件
├── docs/                           # 文档
├── requirements.txt                # Python依赖
├── environment.yml                 # Conda环境配置
└── .env.example                    # 环境变量模板
```

### 技术栈

| 类别 | 技术 | 用途 |
|------|------|------|
| **Web框架** | Streamlit 1.30+ | 交互式Web应用界面 |
| **科学计算** | NumPy, Pandas, SciPy | 数值计算与数据处理 |
| **材料科学** | Pymatgen, Matminer, MP-API | 材料属性计算与特征工程 |
| **机器学习** | Scikit-learn, XGBoost, LightGBM, CatBoost | 模型训练与预测 |
| **优化算法** | Optuna | 超参数优化与逆向设计 |
| **可解释性** | SHAP | 模型解释与特征分析 |
| **可视化** | Plotly, Matplotlib, Seaborn | 数据可视化 |
| **数据库** | SQLite, SQLAlchemy | 数据存储与管理 |

---

## 🚀 快速开始

### 前置要求

- **Python**: 3.10 或 3.11 (推荐 3.11)
- **操作系统**: Windows, macOS, Linux
- **内存**: 至少 4GB RAM (推荐 8GB+)
- **磁盘空间**: 至少 2GB

### 一键启动(推荐)

#### Windows用户

1. **克隆项目**
```bash
git clone https://github.com/YHzed/HEAC-0.2.git
cd HEAC-0.2
```

2. **运行启动脚本**
```bash
# 双击 start.bat 或在PowerShell中运行:
.\start.bat
```

3. **浏览器访问**
   - 应用将自动在浏览器中打开 `http://localhost:8501`

#### macOS/Linux用户

```bash
# 1. 克隆项目
git clone https://github.com/YHzed/HEAC-0.2.git
cd HEAC-0.2

# 2. 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑.env文件,添加您的Materials Project API密钥

# 5. 启动应用
streamlit run app.py
```

### 验证安装

打开浏览器访问 `http://localhost:8501`,您应该能看到:
- 🏠 **AI Visual Lab** 主页
- 三个主要实验室入口
- 最近的活动日志

---

## 📚 功能模块

### 1️⃣ General ML Lab - 通用机器学习实验室

**主要功能:**
- 📁 数据上传与预览
- 📊 探索性数据分析(EDA)
- 🔧 数据预处理与清洗
- 🤖 模型训练与评估
- 📈 可视化分析

**适用场景:**
- 任意表格数据的机器学习任务
- 回归、分类问题
- 模型性能评估

**快速使用:**
```bash
# 1. 启动应用
streamlit run app.py

# 2. 点击"Enter General ML Lab"
# 3. 上传CSV数据文件
# 4. 选择目标变量
# 5. 开始训练模型
```

---

### 2️⃣ HEA Cermet Lab - HEA陶瓷实验室

**主要功能:**
- 🧮 密度计算
- 📏 平均自由程(Mean Free Path)计算
- ⚛️ 粘结相物理性质计算
- 🔬 晶格失配计算
- 📊 材料性能预测

**核心计算:**

1. **密度计算**
   - 基于成分和相组成的理论密度
   - 考虑陶瓷相和粘结相的密度贡献

2. **平均自由程**
   - 基于Roebuck-Almond模型
   - 考虑晶粒尺寸和相分布

3. **晶格失配**
   - 计算粘结相与陶瓷相的晶格失配度
   - 支持WC、TiC、TiN等多种陶瓷相

**使用示例:**
```python
from core.hea_calculator import HEACalculator

# 创建计算器实例
calc = HEACalculator()

# 计算密度
density = calc.calculate_density(
    ceramic_type="WC",
    ceramic_wt_pct=75.0,
    binder_composition={"Co": 0.6, "Ni": 0.3, "Cr": 0.1}
)

# 计算平均自由程
mfp = calc.calculate_mean_free_path(
    ceramic_wt_pct=75.0,
    grain_size=1.5  # μm
)
```

---

### 3️⃣ Cermet Library - 陶瓷材料库

**主要功能:**
- 📚 浏览陶瓷材料数据库
- 🔍 按属性搜索材料
- 📊 材料性能对比
- 💾 导出查询结果

**数据库内容:**
- 材料成分
- 工艺参数
- 机械性能(硬度、韧性等)
- 微观结构参数

---

### 4️⃣ Literature Lab - 文献实验室

**主要功能:**
- 📖 文献数据管理
- 📝 文献信息提取
- 🔗 关联材料数据

---

### 5️⃣ Process Agent - 数据处理代理

**主要功能:**
- 📥 批量数据导入
- 🔄 数据格式转换
- 🧹 数据清洗与验证
- 🏷️ 自动标注与分类
- 🔗 成分解析与验证

**核心流程:**
```
原始数据 → 成分解析 → 特征提取 → 数据验证 → 标准化输出
```

**成分解析能力:**
- 支持多种成分表示格式
- 自动识别陶瓷相和粘结相
- 计算元素原子分数和重量分数

**使用场景:**
- 处理文献中的陶瓷材料数据
- 统一不同来源的数据格式
- 为机器学习准备标准化数据

---

### 6️⃣ GBFS Feature Selection - GBFS特征选择

**主要功能:**
- 🎯 基于梯度提升的特征选择
- 📊 分层聚类去除冗余特征
- 🔍 特征重要性排序
- 📈 特征选择结果可视化

**GBFS算法:**

**Gradient Boosting Feature Selection** 是一种先进的特征选择方法:

1. **初始筛选**: 使用梯度提升模型评估所有特征
2. **重要性排序**: 按特征重要性降序排列
3. **层次聚类**: 对相关特征进行聚类
4. **代表选择**: 从每个簇中选择最重要的特征
5. **迭代优化**: 逐步添加特征并评估模型性能

**优势:**
- 减少过拟合风险
- 提高模型泛化能力
- 保留物理预测特征(如晶格失配、形成能等)
- 加快训练速度

**使用示例:**
```bash
# 1. 在"Process Agent"处理好数据
# 2. 进入"GBFS Feature Selection"
# 3. 选择目标变量(如HV或KIC)
# 4. 设置特征选择参数
# 5. 运行GBFS算法
# 6. 查看选中的特征并导出
```

---

### 7️⃣ Model Training - 模型训练

**主要功能:**
- 🤖 多算法模型训练
- 🎛️ 超参数调优
- 📊 交叉验证
- 🔍 SHAP可解释性分析
- 💾 模型保存与加载

**支持的算法:**
- **XGBoost**: 极端梯度提升
- **LightGBM**: 轻量级梯度提升
- **CatBoost**: 类别特征优化的梯度提升
- **Random Forest**: 随机森林
- **Extra Trees**: 极端随机树
- **Gradient Boosting**: 经典梯度提升

**模型评估指标:**

| 任务类型 | 指标 |
|---------|------|
| **回归** | MAE, RMSE, R², MAPE |
| **分类** | Accuracy, Precision, Recall, F1 |

**SHAP分析:**
- 全局特征重要性
- 单样本预测解释
- 特征依赖图
- 特征交互分析

**使用示例:**
```bash
# 1. 确保数据已通过Process Agent处理
# 2. 进入"Model Training"页面
# 3. 选择算法(推荐XGBoost)
# 4. 配置超参数或使用Optuna自动调优
# 5. 训练模型
# 6. 查看SHAP分析
# 7. 保存模型
```

---

### 8️⃣ Virtual Screening - 虚拟筛选

**主要功能:**
- 🔮 批量材料性能预测
- 🎯 基于规则的筛选
- 📊 筛选结果可视化
- 💾 导出候选材料

**筛选流程:**
```
生成候选材料 → 特征计算 → 模型预测 → 规则筛选 → 排序输出
```

**使用场景:**
- 在大规模候选材料中筛选高性能样本
- 探索成分-性能关系
- 指导实验设计

---

### 9️⃣ HEA Data Preprocessing - HEA数据预处理

**主要功能:**
- 📊 HEA专用数据清洗
- 🔧 缺失值处理
- 📈 异常值检测
- 🏷️ 特征编码

---

### 🔟 Proxy Models - Proxy模型

**主要功能:**
- 🔮 预测形成能(Formation Energy)
- 📏 预测晶格参数(Lattice Parameter)
- 🧲 预测磁矩(Magnetic Moment)
- 🎯 为主模型提供中间特征

**Proxy模型的作用:**

Proxy模型是预测主要目标(如HV、KIC)的**中间步骤模型**:
- 预测物理量(形成能、晶格参数等)
- 这些预测值作为特征输入主模型
- 提高主模型的预测精度

**模型性能:**
- 形成能: R² ≈ 0.85
- 晶格参数: R² ≈ 0.90
- 磁矩: R² ≈ 0.80

---

### 1️⃣1️⃣ Database Manager V2 - 数据库管理器V2

**主要功能:**
- 🗄️ SQLite数据库管理
- 📊 数据表查看与编辑
- 🔍 高级查询
- 📥 数据导入导出
- 🔗 关系管理

**数据库表:**
- `materials`: 材料基础信息
- `compositions`: 成分数据
- `properties`: 性能数据
- `processes`: 工艺参数
- `literature`: 文献来源

**使用示例:**
```bash
# 1. 进入"Database Manager V2"
# 2. 选择或创建数据库
# 3. 查看数据表
# 4. 执行SQL查询
# 5. 导出查询结果
```

---

### 🔮 Inverse Design System - 逆向设计系统

**位置**: `heac_inverse_design/`

**主要功能:**
- 🎯 多目标优化(HV + KIC)
- 📊 Pareto前沿展示
- 🔧 灵活约束设置
- 💡 智能方案推荐

**优化算法**: NSGA-II (通过Optuna实现)

**使用示例:**

1. **启动逆向设计应用**
```bash
cd heac_inverse_design/ui
streamlit run inverse_design_app.py
```

2. **设置目标**
   - 目标硬度范围: 1500-2000 HV
   - 目标韧性范围: 8.0-15.0 MPa·m^0.5

3. **设置约束**
   - 允许元素: Co, Ni, Fe, Cr, W
   - 陶瓷含量: 70-85 wt%
   - 烧结温度: 1300-1500°C

4. **运行优化**
   - 设置优化轮数(建议200-500)
   - 查看Pareto前沿
   - 选择推荐方案

5. **导出结果**
   - 导出候选材料成分
   - 导出预测性能
   - 导出工艺参数

**核心文件:**
- `heac_inverse_design/core/optimization/inverse_designer.py`: 优化引擎
- `heac_inverse_design/ui/inverse_design_app.py`: UI界面

---

## 📦 安装指南

详细安装说明请参考 [INSTALLATION.md](INSTALLATION.md)

### 方法一: 使用pip(推荐)

```bash
# 1. 克隆仓库
git clone https://github.com/YHzed/HEAC-0.2.git
cd HEAC-0.2

# 2. 创建虚拟环境
python -m venv .venv

# Windows激活
.venv\Scripts\activate

# macOS/Linux激活
source .venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
copy .env.example .env  # Windows
cp .env.example .env    # macOS/Linux

# 编辑.env文件,添加Materials Project API密钥

# 5. 启动应用
streamlit run app.py
```

### 方法二: 使用conda

```bash
# 1. 创建conda环境
conda env create -f environment.yml

# 2. 激活环境
conda activate heac-0.2

# 3. 启动应用
streamlit run app.py
```

### API密钥配置

**Materials Project API密钥**是必需的,用于获取材料结构和属性数据。

1. 访问 [Materials Project](https://materialsproject.org/dashboard)
2. 注册/登录账户
3. 在Dashboard中复制API密钥
4. 编辑`.env`文件:
```bash
MP_API_KEY=your_api_key_here
```

更多配置选项请参考 [ENVIRONMENT_SETUP_GUIDE.md](ENVIRONMENT_SETUP_GUIDE.md)

---

## 📖 使用教程

### 完整工作流示例

#### 场景: 预测高硬度HEA陶瓷材料

**步骤1: 数据准备**

1. 准备CSV数据文件,包含:
   - 成分信息(Ceramic_Type, Binder_Composition等)
   - 工艺参数(Sintering_Temperature, Holding_Time等)
   - 性能数据(HV, KIC等)

2. 进入 **Process Agent**
   - 上传CSV文件
   - 选择成分列
   - 执行成分解析
   - 验证解析结果
   - 导出标准化数据

**步骤2: 特征工程**

3. 进入 **HEA Cermet Lab**
   - 加载标准化数据
   - 计算物理特征(密度、平均自由程等)
   - 保存特征增强后的数据

4. 使用 **Proxy Models**
   - 预测形成能
   - 预测晶格参数
   - 预测磁矩
   - 计算晶格失配
   - 保存Proxy特征

**步骤3: 特征选择**

5. 进入 **GBFS Feature Selection**
   - 加载所有特征数据
   - 选择目标变量(HV)
   - 运行GBFS算法
   - 查看选中的特征
   - 导出特征选择后的数据

**步骤4: 模型训练**

6. 进入 **Model Training**
   - 加载特征选择后的数据
   - 选择算法(推荐XGBoost)
   - 使用Optuna自动调优
   - 训练模型
   - 查看SHAP分析
   - 保存模型(如`ModelX_HV.pkl`)

**步骤5: 虚拟筛选**

7. 进入 **Virtual Screening**
   - 加载训练好的模型
   - 生成候选材料成分
   - 批量预测性能
   - 筛选高性能候选
   - 导出结果

**步骤6: 逆向设计(可选)**

8. 使用 **Inverse Design System**
   - 设置目标性能范围
   - 设置成分和工艺约束
   - 运行多目标优化
   - 查看Pareto前沿
   - 选择推荐方案

---

### 单点分析示例

详细理论请参考 [single_point_analysis_theory.md](single_point_analysis_theory.md)

```python
from core.hea_calculator import HEACalculator
from core.proxy_models import ProxyModelEnsemble
from core.modelx_adapter import ModelXAdapter

# 1. 定义材料
material = {
    "ceramic_type": "WC",
    "ceramic_wt_pct": 75.0,
    "binder_composition": {
        "Co": 0.4,
        "Ni": 0.3,
        "Fe": 0.2,
        "Cr": 0.1
    },
    "grain_size": 1.5,  # μm
    "sintering_temp": 1400,  # °C
    "holding_time": 60  # min
}

# 2. 计算物理特征
calc = HEACalculator()
features = {}
features['density'] = calc.calculate_density(
    material['ceramic_type'],
    material['ceramic_wt_pct'],
    material['binder_composition']
)
features['mean_free_path'] = calc.calculate_mean_free_path(
    material['ceramic_wt_pct'],
    material['grain_size']
)

# 3. Proxy模型预测
proxy = ProxyModelEnsemble()
proxy_predictions = proxy.predict(material['binder_composition'])
features.update(proxy_predictions)

# 4. 主模型预测
modelx = ModelXAdapter('models/ModelX.pkl')
predicted_hv = modelx.predict(features)

print(f"预测硬度 HV: {predicted_hv:.0f}")
```

---

## 🔧 API参考

### 核心模块

#### HEACalculator

```python
from core.hea_calculator import HEACalculator

calc = HEACalculator()

# 密度计算
density = calc.calculate_density(
    ceramic_type: str,          # "WC", "TiC", "TiN"等
    ceramic_wt_pct: float,      # 陶瓷相重量百分比
    binder_composition: dict    # {"Co": 0.5, "Ni": 0.5}
) -> float

# 平均自由程计算
mfp = calc.calculate_mean_free_path(
    ceramic_wt_pct: float,
    grain_size: float
) -> float

# 晶格失配计算
mismatch = calc.calculate_lattice_mismatch(
    ceramic_type: str,
    binder_lattice_param: float
) -> float
```

#### PhysicsCalculator

```python
from core.physics_calculator import PhysicsCalculator

physics = PhysicsCalculator()

# 批量物理计算
df_with_physics = physics.calculate_all_features(
    df: pd.DataFrame,
    ceramic_col: str = "Ceramic_Type",
    ceramic_wt_col: str = "Ceramic_Wt_Pct",
    binder_comp_col: str = "Binder_Composition"
) -> pd.DataFrame
```

#### CompositionParser

```python
from core.composition_parser import CompositionParser

parser = CompositionParser()

# 解析成分字符串
result = parser.parse(
    composition_str: str  # "WC-10Co" 或 "75WC-15Co-10Ni"
) -> dict
# 返回:
# {
#     "ceramic_type": "WC",
#     "ceramic_wt_pct": 75.0,
#     "binder_composition": {"Co": 0.6, "Ni": 0.4},
#     ...
# }
```

#### FeatureInjector

```python
from core.feature_injector import FeatureInjector

injector = FeatureInjector(
    mp_api_key: str = None  # 自动从.env读取
)

# 批量特征注入
df_enhanced = injector.inject_features(
    df: pd.DataFrame,
    include_proxy: bool = True,
    include_matminer: bool = True
) -> pd.DataFrame
```

#### ProxyModelPredictor

```python
from core.proxy_model_predictor import ProxyModelPredictor

proxy = ProxyModelPredictor()

# 加载模型
proxy.load_models(
    formation_energy_model: str = "models/proxy_formation_energy.pkl",
    lattice_param_model: str = "models/proxy_lattice_param.pkl",
    magnetic_moment_model: str = "models/proxy_magnetic_moment.pkl"
)

# 批量预测
predictions = proxy.predict_batch(
    df: pd.DataFrame
) -> pd.DataFrame
# 添加列: pred_formation_energy, pred_lattice_param, pred_magnetic_moment
```

#### ModelXAdapter

```python
from core.modelx_adapter import ModelXAdapter

modelx = ModelXAdapter(
    model_path: str = "models/ModelX.pkl"
)

# 单点预测
hv = modelx.predict(
    features: dict  # 包含所有18个必需特征
) -> float

# 批量预测
df['predicted_hv'] = modelx.predict_batch(
    df: pd.DataFrame
)
```

#### VirtualScreening

```python
from core.virtual_screening import VirtualScreener

screener = VirtualScreener(
    model=trained_model,
    feature_extractor=injector
)

# 筛选候选材料
candidates = screener.screen(
    composition_space: dict,      # 定义搜索空间
    target_min: float = 1500,     # 最小目标值
    target_max: float = 2000,     # 最大目标值
    n_samples: int = 10000        # 候选数量
) -> pd.DataFrame
```

---

### 数据库模型

#### DatabaseManager (V2)

```python
from core.db_manager import DatabaseManager

db = DatabaseManager(
    db_path: str = "cermet_master_v2.db"
)

# 查询材料
materials = db.query_materials(
    filters: dict = {"HV_min": 1500}
) -> pd.DataFrame

# 添加材料
db.add_material(
    material_data: dict
)

# 更新材料
db.update_material(
    material_id: int,
    updates: dict
)
```

---

## ❓ 常见问题

### Q1: Materials Project API密钥在哪里获取?

**A**: 访问 [materialsproject.org](https://materialsproject.org/dashboard),注册账户后在Dashboard中可以看到您的API密钥。

### Q2: 为什么Proxy模型预测返回NaN?

**A**: 可能原因:
1. 输入特征缺失或格式错误
2. Proxy模型文件损坏或路径错误
3. 成分解析失败

**解决方法**:
- 检查输入数据是否包含所有必需列
- 确认模型文件路径正确
- 在Process Agent中重新解析成分

### Q3: GBFS特征选择要运行多久?

**A**: 取决于数据集大小和特征数量:
- 小数据集(<1000行, <50特征): 1-5分钟
- 中等数据集(1000-5000行, 50-200特征): 5-20分钟
- 大数据集(>5000行, >200特征): 20分钟-1小时

可以通过减少初始特征数量来加速。

### Q4: 模型训练时内存不足怎么办?

**A**: 
1. 减少数据集大小(采样)
2. 减少特征数量(使用GBFS)
3. 调整模型参数(减少`max_depth`, `n_estimators`)
4. 使用增量学习算法

### Q5: 如何选择合适的机器学习算法?

**A**: 推荐顺序:
1. **XGBoost**: 性能最佳,适合大多数场景
2. **LightGBM**: 速度快,适合大数据集
3. **CatBoost**: 对类别特征友好
4. **Random Forest**: 稳定,不易过拟合

建议都尝试并对比。

### Q6: Streamlit应用启动失败?

**A**: 常见解决方法:
```bash
# 1. 确认环境已激活
conda activate heac-0.2

# 2. 使用Python模块方式启动
python -m streamlit run app.py

# 3. 更换端口
streamlit run app.py --server.port 8502

# 4. 检查依赖
pip install -r requirements.txt --upgrade
```

### Q7: 如何理解SHAP分析结果?

**A**: 
- **SHAP值正**: 特征增加了预测值
- **SHAP值负**: 特征降低了预测值
- **SHAP值绝对值大**: 特征影响大
- **红色**: 特征值高
- **蓝色**: 特征值低

例如: 如果"Ceramic_Wt_Pct"的SHAP值为正且为红色,说明高陶瓷含量增加了硬度预测值。

### Q8: 逆向设计优化速度慢怎么办?

**A**:
1. 减少优化轮数(trials)
2. 简化约束条件
3. 减小搜索空间
4. 使用更快的Proxy模型

### Q9: 如何导出预测结果?

**A**: 所有页面都支持导出:
- 点击数据表右上角的"Download"按钮
- 或使用`df.to_csv()`手动导出

### Q10: 项目可以用于商业用途吗?

**A**: 项目采用MIT许可证,可用于商业用途,但请保留原作者信息。

---

## 🤝 贡献指南

我们欢迎任何形式的贡献!

### 如何贡献

1. **Fork项目**
2. **创建特性分支** (`git checkout -b feature/AmazingFeature`)
3. **提交更改** (`git commit -m 'Add some AmazingFeature'`)
4. **推送到分支** (`git push origin feature/AmazingFeature`)
5. **开启Pull Request**

### 开发设置

```bash
# 1. 克隆您fork的仓库
git clone https://github.com/YOUR_USERNAME/HEAC-0.2.git
cd HEAC-0.2

# 2. 安装开发依赖
pip install -r requirements.txt -r requirements-dev.txt

# 3. 运行测试
pytest tests/

# 4. 代码格式化
black core/ pages/ tests/

# 5. 代码检查
flake8 core/ pages/
```

### 提交规范

- ✨ `feat`: 新功能
- 🐛 `fix`: Bug修复
- 📝 `docs`: 文档更新
- 🎨 `style`: 代码格式
- ♻️ `refactor`: 重构
- ✅ `test`: 测试
- 🔧 `chore`: 构建/工具

示例: `feat: 添加ModelY(KIC预测)支持`

---

## 📄 许可证

本项目采用 [MIT License](LICENSE)

---

## 📞 联系方式

- **项目主页**: [https://github.com/YHzed/HEAC-0.2](https://github.com/YHzed/HEAC-0.2)
- **问题反馈**: [GitHub Issues](https://github.com/YHzed/HEAC-0.2/issues)
- **邮箱**: your.email@example.com

---

## 🙏 致谢

- [Materials Project](https://materialsproject.org/) - 材料数据库
- [Matminer](https://github.com/hackingmaterials/matminer) - 特征工程
- [Streamlit](https://streamlit.io/) - Web框架
- [XGBoost](https://xgboost.ai/) - 机器学习算法
- [SHAP](https://github.com/slundberg/shap) - 模型解释

---

## 📚 相关文档

- [安装指南 (INSTALLATION.md)](INSTALLATION.md)
- [环境设置指南 (ENVIRONMENT_SETUP_GUIDE.md)](ENVIRONMENT_SETUP_GUIDE.md)
- [Materials Project API参考 (MP_API_REFERENCE.md)](MP_API_REFERENCE.md)
- [数据库V2使用说明 (README_DB_V2.md)](README_DB_V2.md)
- [单点分析理论 (single_point_analysis_theory.md)](single_point_analysis_theory.md)
- [陶瓷分析报告 (cermet_analysis_report.md)](cermet_analysis_report.md)

---

<div align="center">

**⭐ 如果这个项目对您有帮助,请给我们一个星标! ⭐**

Made with ❤️ by HEA Cermet Research Team

</div>
