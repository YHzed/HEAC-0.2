# HEAC 0.2 安装指南

## 📋 系统要求

### 必需环境
- **Python版本**: 3.10 或 3.11（推荐3.11）
- **操作系统**: Windows, macOS, Linux
- **内存**: 至少4GB RAM（推荐8GB+）
- **磁盘空间**: 至少2GB可用空间

### 可选
- **GPU**: 不需要（仅CPU即可运行）
- **conda**: 可选（推荐使用虚拟环境）

---

## 🚀 快速开始

### 方法一: 使用pip（推荐）

#### 1. 克隆仓库
```bash
git clone https://github.com/YourUsername/HEAC-0.2.git
cd HEAC-0.2
```

#### 2. 创建虚拟环境
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

#### 3. 安装依赖
```bash
# 完整安装（所有功能）
pip install -r requirements.txt

# 或者按需安装
pip install -r requirements-core.txt    # 核心功能
pip install -r requirements-ml.txt      # 机器学习
pip install -r requirements-web.txt     # Web界面
pip install -r requirements-dev.txt     # 开发工具
```

#### 4. 配置API密钥
```bash
# 复制环境配置模板
copy .env.example .env    # Windows
cp .env.example .env      # macOS/Linux

# 编辑.env文件，添加您的Materials Project API密钥
# MP_API_KEY=your_api_key_here
```

#### 5. 验证安装
```bash
python -c "from core import *; print('✅ 核心模块导入成功')"
streamlit run app.py
```

---

### 方法二: 使用conda

#### 1. 创建conda环境
```bash
conda env create -f environment.yml
conda activate heac-0.2
```

#### 2. 验证安装
```bash
python -c "from core import *; print('✅ 核心模块导入成功')"
```

#### 3. 运行应用
```bash
streamlit run app.py
```

---

## 📦 依赖说明

### 核心依赖（requirements-core.txt）
仅包含最基本的HEA计算功能：
- `numpy`: 科学计算
- `pandas`: 数据处理
- `pymatgen`: 材料计算
- `mp-api`: Materials Project API
- `emmet-core`: Materials Project数据模型

**安装**: `pip install -r requirements-core.txt`

**适用场景**: 仅需要命令行工具,不需要Web界面或ML训练

---

### 机器学习依赖（requirements-ml.txt）
包含模型训练和预测功能：
- `scikit-learn`: 经典机器学习算法
- `xgboost`, `lightgbm`, `catboost`: 梯度提升模型
- `optuna`: 超参数优化
- `shap`:  模型可解释性分析

**安装**: `pip install -r requirements-core.txt -r requirements-ml.txt`

**适用场景**: 本地训练模型,无需Web界面

---

### Web应用依赖（requirements-web.txt）
包含Streamlit界面和可视化：
- `streamlit`: Web应用框架
- `plotly`: 交互式图表
- `matplotlib`, `seaborn`: 统计可视化
- `matminer`: 材料特征工程

**安装**: `pip install -r requirements-core.txt -r requirements-web.txt`

**适用场景**: 使用Web界面进行数据分析和可视化

---

### 完整依赖（requirements.txt）
包含所有功能：核心计算 + 机器学习 + Web界面

**安装**: `pip install -r requirements.txt`

**适用场景**: 完整体验所有功能（推荐）

---

### 开发依赖（requirements-dev.txt）
包含开发和测试工具：
- `pytest`: 测试框架
- `flake8`: 代码检查
- `black`: 代码格式化
- `sphinx`: 文档生成

**安装**: `pip install -r requirements-dev.txt`

**适用场景**: 参与项目开发

---

## 🔑 API密钥配置

### Materials Project API密钥

#### 1. 获取API密钥
访问[Materials Project Dashboard](https://materialsproject.org/dashboard)并登录/注册，在"API"部分复制您的密钥。

#### 2. 配置环境变量
编辑`.env`文件：
```bash
# Materials Project API Configuration
MP_API_KEY=your_actual_api_key_here  # 替换为您的真实密钥

# Cache settings
MP_CACHE_ENABLED=true
MP_CACHE_DIR=core/data/mp_cache
MP_CACHE_TTL_DAYS=30

# Rate limiting (requests per second)
MP_RATE_LIMIT=10
```

#### 3. 验证API密钥
```python
from core.materials_project_client import MaterialsProjectClient

client = MaterialsProjectClient()
# 如果没有报错，说明API密钥配置成功
```

---

## ✅ 验证安装

### 测试核心模块
```bash
python -c "from core import HEACalculator, MaterialDatabase; print('✅ 核心模块OK')"
```

### 测试机器学习模块
```bash
python -c "from core import ModelFactory, ModelTrainer; print('✅ ML模块OK')"
```

### 测试Web应用
```bash
streamlit run app.py
# 浏览器应该自动打开 http://localhost:8501
```

### 运行测试套件
```bash
pytest tests/
```

---

## 🐛 故障排除

### 问题1: "找不到模块'pymatgen'"
**解决方案**:
```bash
pip install pymatgen
# 或者
pip install -r requirements-core.txt
```

---

### 问题2: "Materials Project API Error"
**可能原因**:
1. API密钥未配置或配置错误
2. 网络连接问题
3. API配额用尽

**解决方案**:
1. 检查`.env`文件中的`MP_API_KEY`
2. 测试网络连接: `ping materialsproject.org`
3. 检查[MP Dashboard](https://materialsproject.org/dashboard)中的API使用情况

---

### 问题3: "Streamlit import error"
**解决方案**:
```bash
pip install streamlit>=1.30.0
```

---

### 问题4: XGBoost/LightGBM编译错误（Windows）
**解决方案**:
1. 安装Microsoft Visual C++ Build Tools
2. 或使用预编译的wheel文件:
   ```bash
   pip install xgboost lightgbm --prefer-binary
   ```

---

### 问题5: "ImportError: DLL load failed"（Windows）
**解决方案**:
```bash
# 安装VC++ Redistributable
# 下载链接: https://aka.ms/vs/17/release/vc_redist.x64.exe

# 或重新安装numpy/scipy
pip uninstall numpy scipy
pip install numpy scipy --no-cache-dir
```

---

## 📁 项目结构

```
HEAC-0.2/
├── app.py                  # Streamlit应用入口
├── core/                   # 核心模块
│   ├── __init__.py
│   ├── hea_calculator.py   # HEA计算器
│   ├── hea_data_processor.py  # 数据处理
│   ├── imports/            # 统一导入
│   ├── ...
├── pages/                  # Streamlit页面
│   ├── 1_General_ML_Lab.py
│   ├── ...
├── scripts/                # 辅助脚本
├── tests/                  # 测试文件
│   ├── temp/               # 临时测试
│   ├── debug/              # 调试脚本
├── training data/          # 训练数据
├── requirements.txt        # 完整依赖
├── requirements-*.txt      # 分类依赖
├── environment.yml         # Conda配置
├── .env.example            # 环境配置模板
└── README.md
```

---

## 🎯 下一步

成功安装后，您可以：

1. **探索Web界面**: 
   ```bash
   streamlit run app.py
   ```
   访问 http://localhost:8501

2. **运行教程笔记本**:
   ```bash
   jupyter notebook notebooks/
   ```

3. **查看文档**:
   - [API参考](docs/api_reference.md)
   - [用户指南](docs/user_guide.md)

4. **运行示例**:
   ```bash
   python examples/example_hea_calculation.py
   ```

---

## 📞 获取帮助

- **GitHub Issues**: [提交问题](https://github.com/YourUsername/HEAC-0.2/issues)
- **文档**: 查看 `docs/` 目录
- **示例**: 查看 `examples/` 目录

---

## 🛠️ 开发模式安装

如果您想参与项目开发:

```bash
# 安装开发依赖
pip install -r requirements.txt -r requirements-dev.txt

# 运行测试
pytest tests/

# 代码格式化
black core/ pages/ tests/

# 代码检查
flake8 core/ pages/
```

---

## 📝 更新日志

### v0.2.0
- 重构项目结构
- 统一依赖管理
- 添加HEADataProcessor到core模块
- 创建统一导入系统
- 优化测试文件组织

---

祝您使用愉快！🎉
