# HEAC 0.2 - 高熵合金陶瓷智能设计平台

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Streamlit](https://img.shields.io/badge/streamlit-1.30%2B-red)

*一个集成数据处理、机器学习、逆向设计的高熵合金陶瓷(HEA Cermet)材料研发平台*

[快速开始](docs/QUICK_START.md) | [文档](docs/) | [故障排除](docs/TROUBLESHOOTING.md) | [示例](examples/)

</div>

---

## 📋 目录

- [项目简介](#-项目简介)
- [核心特性](#-核心特性)
- [快速开始](#-快速开始)
- [功能模块](#-功能模块)
- [使用示例](#-使用示例)
- [文档](#-文档)
- [贡献](#-贡献)
- [许可证](#-许可证)

---

## 🎯 项目简介

**HEAC 0.2** 是一个专为高熵合金陶瓷(High Entropy Alloy Cermet)材料研发设计的智能平台。项目整合了先进的机器学习算法、物理模型和材料数据库,为材料科学家和工程师提供从数据处理、特征工程、模型训练到逆向设计的全流程解决方案。

###适用领域

- 高熵合金陶瓷材料设计与优化
- 材料性能预测(硬度、断裂韧性等)
- 多目标材料优化
- 材料数据库管理与查询
- 机器学习模型训练与解释

---

## ✨ 核心特性

### 🔬 材料科学
- **物理计算引擎**: 密度、平均自由程、晶格失配等物理模型
- **Materials Project 集成**: 自动获取晶体结构、形成能、磁矩等属性
- **Proxy 模型**: 预测形成能、晶格参数、磁矩等关键物理量
- **成分解析**: 智能解析复杂的合金陶瓷成分表示

### 🤖 机器学习
- **多算法支持**: XGBoost, LightGBM, CatBoost, Random Forest
- **自动特征工程**: 基于 Matminer 的高级特征提取(50x 速度提升)
- **GBFS 特征选择**: 基于梯度提升的分层特征选择算法
- **模型可解释性**: SHAP 分析、特征重要性评估
- **超参数优化**: 集成 Optuna 进行自动调参

### 🎨 交互式界面
- **模块化设计**: 8+ 专业功能页面
- **学术风格 UI**: Crimson Pro + Atkinson Hyperlegible 字体,蓝色系配色
- **实时可视化**: Plotly 交互式图表
- **数据管理**: 完整的数据上传、预处理、标准化工作流

### 🔮 逆向设计
- **多目标优化**: 同时优化硬度(HV)和断裂韧性(KIC)
- **Pareto 前沿**: 展示非支配解集合
- **约束优化**: 支持元素、工艺、成分等多种约束
- **智能推荐**: 自动排序并推荐最佳设计方案

---

## 🚀 快速开始

> ⚡ **5 分钟上手**: 查看 **[Quick Start Guide](docs/QUICK_START.md)**  
> 🔧 **遇到问题?**: 查看 **[故障排除指南](docs/TROUBLESHOOTING.md)** - 覆盖 20+ 常见问题

### 前置要求

- **Python**: 3.10 或 3.11 (推荐 3.11)
- **操作系统**: Windows, macOS, Linux
- **内存**: 至少 4GB RAM (推荐 8GB+)

### 一键安装

**Windows**:
```bash
git clone https://github.com/YHzed/HEAC-0.2.git
cd HEAC-0.2
conda env create -f environment.yml
start.bat  # 自动启动应用
```

**macOS/Linux**:
```bash
git clone https://github.com/YHzed/HEAC-0.2.git
cd HEAC-0.2
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run Home.py
```

浏览器访问: `http://localhost:8501`

详细安装说明请参考 [INSTALLATION.md](INSTALLATION.md)

---

## 📚 功能模块

### 核心功能

| 模块 | 功能 | 文档 |
|------|------|------|
| **Proxy Models** | 形成能、晶格参数、磁矩预测 (R² > 0.95) | [README](models/proxy_models/README.md) |
| **Process Agent** | 数据处理、成分解析、特征提取 (50x 加速) | [Guide](docs/user-guides/data-processing.md) |
| **Model Training** | XGBoost/LightGBM训练、SHAP 分析 | [Guide](docs/user-guides/model-training.md) |
| **Virtual Screening** | 批量材料性能预测与筛选 | [Guide](docs/user-guides/virtual-screening.md) |
| **Database Manager** | SQLite 数据库管理与查询 | [Guide](docs/database_v2_deployment.md) |
| **Inverse Design** | 多目标优化、Pareto 前沿 | [Guide](docs/user-guides/inverse-design.md) |

### 其他功能

- **General ML Lab**: 通用机器学习实验室
- **HEA Cermet Lab**: HEA 陶瓷物理计算
- **GBFS Feature Selection**: 基于梯度提升的特征选择

完整功能列表请参考 [功能模块文档](docs/FEATURES.md)

---

## 💡 使用示例

### 单点材料性能预测

```python
from core.hea_calculator import HEACalculator
from core.proxy_models import ProxyModelPredictor

# 1. 定义材料成分
composition = "Co0.3Ni0.3Fe0.2Cr0.2"
ceramic_type = "WC"
ceramic_wt_pct = 75.0

# 2. 计算物理特征
calc = HEACalculator()
density = calc.calculate_density(ceramic_type, ceramic_wt_pct, composition)

# 3. Proxy 模型预测
predictor = ProxyModelPredictor()
properties = predictor.predict_all(composition)

print(f"形成能: {properties['formation_energy']:.3f} eV/atom")
print(f"晶格参数: {properties['lattice']:.3f} Å")
print(f"磁矩: {properties['magnetic_moment']:.2f} μB")
```

### 完整工作流

详细的端到端示例请参考:
- [单点分析理论](single_point_analysis_theory.md)
- [完整工作流教程](docs/user-guides/complete-workflow.md)
- [API 参考文档](docs/api-reference/)

---

## 📖 文档

### 入门文档

- **[Quick Start Guide](docs/QUICK_START.md)** - 5 分钟上手
- **[安装指南](INSTALLATION.md)** - 详细安装说明
- **[故障排除](docs/TROUBLESHOOTING.md)** - 常见问题解决

### 用户指南

- [数据处理指南](docs/user-guides/data-processing.md)
- [模型训练指南](docs/user-guides/model-training.md)
- [虚拟筛选指南](docs/user-guides/virtual-screening.md)
- [逆向设计指南](docs/user-guides/inverse-design.md)

### 开发文档

- [系统架构](docs/ARCHITECTURE.md)
- [API 参考](docs/api-reference/)
- [贡献指南](CONTRIBUTING.md)

---

## 🏗️ 技术栈

| 类别 | 技术 |
|------|------|
| **Web 框架** | Streamlit 1.30+ |
| **科学计算** | NumPy, Pandas, SciPy |
| **材料科学** | Pymatgen, Matminer, MP-API |
| **机器学习** | Scikit-learn, XGBoost, LightGBM, CatBoost |
| **优化** | Optuna |
| **可解释性** | SHAP |
| **可视化** | Plotly, Matplotlib |
| **数据库** | SQLite, SQLAlchemy |

---

## 🤝 贡献

欢迎贡献! 请阅读 [贡献指南](CONTRIBUTING.md) 了解如何参与项目开发。

### 开发设置

```bash
# 克隆项目
git clone https://github.com/YHzed/HEAC-0.2.git
cd HEAC-0.2

# 安装开发依赖
pip install -r requirements.txt -r requirements-dev.txt

# 运行测试
pytest tests/

# 代码格式化
black core/ pages/ tests/
```

---

## 📄 许可证

本项目采用 [MIT License](LICENSE) 许可证。

---

## 📞 支持

- **GitHub Issues**: [提交问题](https://github.com/YHzed/HEAC-0.2/issues)
- **文档**: 查看 [docs/](docs/) 目录
- **示例**: 查看 [examples/](examples/) 目录

---

## 🌟 致谢

感谢以下开源项目和社区:
- [Materials Project](https://materialsproject.org) - 材料数据
- [Matminer](https://hackingmaterials.lbl.gov/matminer/) - 特征工程
- [Streamlit](https://streamlit.io) - Web 框架
- [Plotly](https://plotly.com) - 可视化

---

<div align="center">

**HEAC 0.2** - High Entropy Alloy Cermet Design Platform  
Made with ❤️ for Materials Science

[⬆ 回到顶部](#heac-02---高熵合金陶瓷智能设计平台)

</div>
