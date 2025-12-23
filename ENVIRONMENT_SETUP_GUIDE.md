# HEAC 0.2 环境设置和使用指南

## ✅ 环境已创建

专用的 `heac-0.2` conda 环境已成功创建，包含：
- Python 3.11
- 所有核心科学计算、机器学习、材料科学和 Web 应用依赖

---

## 🔧 验证环境

请在 PowerShell 中按顺序执行以下命令：

### 1. 激活环境并检查 Python 版本

```powershell
conda activate heac-0.2
python --version
```

**预期输出**：`Python 3.11.x`

### 2. 验证核心依赖

```powershell
python -c "import numpy, pandas, scipy; print('✓ 科学计算库正常')"
```

### 3. 验证机器学习库

```powershell
python -c "import sklearn, xgboost, lightgbm, catboost, optuna; print('✓ 机器学习库正常')"
```

### 4. 验证材料科学库

```powershell
python -c "import pymatgen, matminer; print('✓ 材料科学库正常')"
```

### 5. 验证 Streamlit

```powershell
streamlit --version
```

**预期输出**：`Streamlit, version 1.x.x`

### 6. 测试启动应用

```powershell
cd "d:\ML\HEAC 0.2"
streamlit run app.py
```

**预期结果**：Streamlit 应用成功启动，浏览器自动打开 `http://localhost:8501`

---

## 📋 日常使用流程

### 每次启动项目

```powershell
# 1. 进入项目目录
cd "d:\ML\HEAC 0.2"

# 2. 激活专用环境
conda activate heac-0.2

# 3. 启动应用
streamlit run app.py
```

### 使用 Python 模块方式启动（备用方案）

如果 `streamlit run` 有问题，可以使用：

```powershell
python -m streamlit run app.py
```

---

## 📦 管理依赖

### 查看已安装的包

```powershell
conda activate heac-0.2
conda list           # 查看所有包
pip list             # 查看 pip 安装的包
```

### 添加新依赖

#### 方法 1：通过 conda 安装（推荐）

```powershell
conda activate heac-0.2
conda install -c conda-forge <package-name>
```

#### 方法 2：通过 pip 安装

```powershell
conda activate heac-0.2
pip install <package-name>
```

#### 方法 3：更新 requirements.txt 后批量安装

1. 编辑 `requirements.txt` 添加新包
2. 执行：
```powershell
conda activate heac-0.2
pip install -r requirements.txt
```

### 导出环境配置

如需分享或备份当前环境：

```powershell
conda activate heac-0.2

# 导出完整 conda 环境（推荐）
conda env export > environment-full.yml

# 导出 pip 包列表
pip freeze > requirements-freeze.txt
```

---

## 🔄 重建环境

如果需要完全重建环境：

### 删除现有环境

```powershell
conda deactivate
conda env remove -n heac-0.2
```

### 从配置文件重建

```powershell
cd "d:\ML\HEAC 0.2"
conda env create -f environment.yml
```

---

## 🧹 清理旧环境（可选）

如果确认不再需要 base 环境或全局 Python 3.13 中的项目特定包：

### 清理 base 环境中的项目包

```powershell
conda activate base
pip uninstall streamlit pymatgen mp-api matminer catboost xgboost lightgbm -y
```

> ⚠️ **警告**：仅在确认不影响其他项目的情况下执行！

---

## 🎯 环境规则（重要！）

根据您的要求，**以后所有依赖都必须安装在 `heac-0.2` conda 环境中**：

### ✅ 正确做法

```powershell
# 1. 总是先激活环境
conda activate heac-0.2

# 2. 然后安装包
conda install <package>  # 或
pip install <package>
```

### ❌ 错误做法

```powershell
# 不要在 base 环境安装项目依赖
conda activate base
pip install <project-package>  # ❌ 错误！

# 不要在全局 Python 安装
pip install <package>  # ❌ 错误！
```

### 检查当前环境

随时可以检查当前激活的环境：

```powershell
conda info --envs
```

当前环境会有 `*` 标记。确保看到：
```
heac-0.2              *  D:\conda_envs\heac-0.2
```

---

## 🛠️ 常见问题排查

### 问题 1：`streamlit: command not found`

**解决方案**：
```powershell
conda activate heac-0.2
python -m streamlit run app.py
```

### 问题 2：导入错误（ImportError）

**解决方案**：确认环境已激活
```powershell
conda info --envs  # 检查环境
conda activate heac-0.2  # 激活环境
```

### 问题 3：包版本冲突

**解决方案**：重建环境
```powershell
conda env remove -n heac-0.2
conda env create -f environment.yml
```

### 问题 4：Streamlit 启动失败

**解决方案 A**：使用 Python 模块方式
```powershell
python -m streamlit run app.py
```

**解决方案 B**：检查端口占用
```powershell
# 使用不同端口
streamlit run app.py --server.port 8502
```

---

## 📊 环境信息

### 当前配置

- **环境名称**：`heac-0.2`
- **Python 版本**：3.11
- **配置文件**：`environment.yml`
- **依赖列表**：`requirements.txt`

### 已安装的主要包

| 类别 | 包名 | 用途 |
|------|------|------|
| 科学计算 | numpy, pandas, scipy | 数值计算、数据处理 |
| 可视化 | matplotlib, seaborn, plotly | 数据可视化 |
| 机器学习 | scikit-learn, xgboost, lightgbm, catboost | 模型训练 |
| 材料科学 | pymatgen, matminer, mp-api | 材料属性计算 |
| Web 应用 | streamlit | 交互式界面 |
| 优化 | optuna | 超参数优化 |
| 解释性 | shap | 模型解释 |

---

## 🚀 快速启动命令

将以下命令保存为快捷方式：

```powershell
cd "d:\ML\HEAC 0.2" ; conda activate heac-0.2 ; streamlit run app.py
```

或者创建一个 `start.bat` 文件：

```batch
@echo off
call conda activate heac-0.2
cd /d "d:\ML\HEAC 0.2"
streamlit run app.py
pause
```

双击 `start.bat` 即可启动项目！

---

## 📝 更新日志

- **2025-12-23**：创建专用 `heac-0.2` conda 环境
- 优化 `environment.yml`，明确 conda 和 pip 依赖分离
- 制定环境管理规范：所有依赖必须安装在 conda 环境中

---

## 📞 获取帮助

如遇到问题：

1. 检查环境是否激活：`conda info --envs`
2. 查看错误日志
3. 参考本文档的"常见问题排查"部分
4. 必要时重建环境

---

**祝使用愉快！** 🎉
