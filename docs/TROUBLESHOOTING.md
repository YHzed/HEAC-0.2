# HEAC 0.2 故障排除指南

快速解决常见问题,让您的 HEAC 0.2 平稳运行。

---

## 📋 目录

- [安装问题](#-安装问题)
- [运行时错误](#-运行时错误)
- [性能问题](#-性能问题)
- [数据问题](#-数据问题)
- [错误信息索引](#-错误信息索引)
- [获取更多帮助](#-获取更多帮助)

---

## 🔧 安装问题

### ❌ "找不到模块 'pymatgen'" / "ModuleNotFoundError"

**症状**: 运行时提示缺少模块

**原因**: 依赖未安装或虚拟环境未激活

**解决方案**:

```bash
# 1. 确保在正确的环境中
conda activate heac-0.2  # 或 source .venv/bin/activate

# 2. 安装缺失的模块
pip install pymatgen

# 3. 或重新安装所有依赖
pip install -r requirements.txt
```

---

### ❌ "conda: command not found"

**症状**: Windows 下 start.bat 无法运行

**原因**: Conda 未安装或未添加到 PATH

**解决方案**:

**方法 1: 安装 Miniconda**
1. 下载 [Miniconda](https://docs.conda.io/en/latest/miniconda.html)
2. 安装时勾选 "Add to PATH"
3. 重启终端

**方法 2: 使用 venv 替代**
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
streamlit run Home.py
```

---

### ❌ XGBoost/LightGBM 编译错误 (Windows)

**症状**: 
```
error: Microsoft Visual C++ 14.0 or greater is required
```

**原因**: 缺少 C++ 编译器

**解决方案**:

**方法 1: 使用预编译包 (推荐)**
```bash
pip install xgboost lightgbm catboost --prefer-binary
```

**方法 2: 安装 Visual C++ Build Tools**
1. 下载 [Build Tools](https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022)
2. 安装 "C++ build tools" 组件
3. 重新运行 `pip install -r requirements.txt`

---

### ❌ "ImportError: DLL load failed" (Windows)

**症状**: numpy, scipy 或其他科学计算库导入失败

**原因**: 缺少 Visual C++ Redistributable

**解决方案**:

```bash
# 1. 下载并安装 VC++ Redistributable
# https://aka.ms/vs/17/release/vc_redist.x64.exe

# 2. 或重新安装相关包
pip uninstall numpy scipy pandas
pip install numpy scipy pandas --no-cache-dir
```

---

### ❌ "Permission denied" 或访问被拒绝

**症状**: 安装或写入文件时权限错误

**原因**: 权限不足

**解决方案**:

```bash
# Windows: 以管理员身份运行 PowerShell

# macOS/Linux: 使用用户级安装
pip install --user -r requirements.txt

# 或使用虚拟环境(推荐)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## ⚠️ 运行时错误

### ❌ "Materials Project API Error" / "MP_API_KEY not found"

**症状**: 
```
MaterialsProjectError: API key not found or invalid
```

**原因**: API 密钥未配置

**解决方案**:

1. **获取 API 密钥**
   - 访问 [Materials Project Dashboard](https://materialsproject.org/dashboard)
   - 登录/注册
   - 复制您的 API 密钥

2. **配置密钥**
   ```bash
   # 编辑 .env 文件
   MP_API_KEY=your_actual_api_key_here
   ```

3. **重启应用**
   ```bash
   # 按 Ctrl+C 停止,然后重新运行
   streamlit run Home.py
   ```

**注意**: Proxy Models 无需 API 密钥即可使用

---

### ❌ "Streamlit run Home.py: command not found"

**症状**: streamlit 命令无法识别

**原因**: Streamlit 未安装或环境未激活

**解决方案**:

```bash
# 1. 确保环境激活
conda activate heac-0.2

# 2. 安装/升级 Streamlit
pip install streamlit>=1.30.0

# 3. 验证安装
streamlit --version
```

---

### ❌ "Address already in use" / 端口被占用

**症状**: 
```
OSError: [Errno 48] Address already in use
```

**原因**: 8501 端口被其他应用占用

**解决方案**:

**方法 1: 使用其他端口**
```bash
streamlit run Home.py --server.port 8502
```

**方法 2: 终止占用进程**
```bash
# Windows
netstat -ano | findstr :8501
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :8501
kill -9 <PID>
```

---

### ❌ "FileNotFoundError: [Errno 2] No such file or directory: 'models/'"

**症状**: 应用启动时提示找不到模型文件

**原因**: 模型文件缺失或路径错误

**解决方案**:

```bash
# 1. 检查当前目录
pwd  # 或 cd (Windows)

# 2. 确保在项目根目录
cd path/to/HEAC-0.2

# 3. 验证模型目录存在
ls models/  # 或 dir models\ (Windows)

# 4. 如果缺失,检查是否在 .gitignore 中
# 模型文件通常需要单独下载或训练
```

**临时解决**: 访问不需要模型的页面(如 HEA Cermet Lab)

---

### ❌ "无可用目标变量!" / "No valid target columns"

**症状**: 在 Model Training 或 GBFS 页面提示无目标变量

**原因**: 数据文件缺少预期的目标列(如 HV, KIC)

**解决方案**:

1. **检查数据格式**
   ```python
   import pandas as pd
   df = pd.read_csv('your_data.csv')
   print(df.columns)  # 查看所有列名
   ```

2. **确保包含目标列**
   - 硬度预测需要: `HV` 或 `Hardness` 列
   - 韧性预测需要: `KIC` 或 `Toughness` 列

3. **重命名列**
   ```python
   df.rename(columns={'Hardness_Value': 'HV'}, inplace=True)
   df.to_csv('your_data.csv', index=False)
   ```

---

### ❌ "Matminer not installed or missing dependencies"

**症状**: 特征生成时报错

**原因**: Matminer 依赖缺失

**解决方案**:

```bash
# 完整安装 matminer 及其依赖
pip install matminer scikit-learn

# 如果仍有问题,更新 pymatgen
pip install --upgrade pymatgen
```

---

## 🐌 性能问题

### ❓ 应用启动很慢 (>30 秒)

**原因**: 首次加载需要导入大量科学计算库和字体

**正常范围**:
- 首次启动: 10-20 秒
- 后续启动: 3-5 秒

**优化方法**:

1. **使用 SSD** 而非 HDD
2. **关闭不必要的页面**
   ```bash
   # 注释掉不常用的页面(暂时)
   # 编辑 .streamlit/config.toml
   ```
3. **检查网络字体加载**
   - 如果网络慢,Google Fonts 可能拖慢加载
   - 可临时注释 `.streamlit/custom.css` 中的 `@import url(...)`

---

### ❓ 特征计算非常慢

**症状**: Process Agent 的 Matminer 特征生成卡住

**原因**: Matminer 计算某些特征非常耗时

**解决方案**:

1. **使用缓存功能**
   - 系统自动缓存已计算的成分
   - 确保 `MP_CACHE_ENABLED=true` 在 `.env` 中

2. **减少候选数量**
   - Virtual Screening 时降低生成数量

3. **使用并行计算**
   - 项目已内置 ParallelFeatureInjector
   - 自动使用多核加速(高达 50x)

---

### ❓ 内存不足 / "MemoryError"

**症状**: 大数据集处理时崩溃

**原因**: 数据集过大,超出可用内存

**解决方案**:

1. **分批处理**
   ```python
   # 将大数据集拆分为小块
   chunk_size = 1000
   for chunk in pd.read_csv('large_data.csv', chunksize=chunk_size):
       process(chunk)
   ```

2. **增加虚拟内存** (临时)
   - Windows: 系统 → 高级系统设置 → 性能 → 虚拟内存

3. **清理 Streamlit 缓存**
   ```python
   # 在应用中点击侧边栏的 "🧹 清理Session" 按钮
   # 或手动清理
   st.cache_data.clear()
   ```

---

## 📊 数据问题

### ❌ "体积分数验证失败"

**症状**: Process Agent 提示陶瓷和粘结相总和不等于 100%

**原因**: 成分数据格式错误

**解决方案**:

1. **检查成分列**
   - 陶瓷类型: WC, TiC, TiN 等
   - 陶瓷含量: 应为重量百分比(如 75.0)
   - 粘结相: Co0.3Ni0.3Fe0.2Cr0.2 格式

2. **允许误差范围**
   - 系统允许 ±2% 误差
   - 如果接近但未通过,手动调整数据

---

### ❌ "Could not find 'Composition' column"

**症状**: 数据处理时找不到成分列

**原因**: CSV 文件缺少 Composition 列

**解决方案**:

1. **检查列名**
   - 确保有名为 `Composition` 的列
   - 注意大小写和空格

2. **重命名列**
   ```python
   df.rename(columns={'comp': 'Composition'}, inplace=True)
   ```

3. **正确的成分格式**
   ```
   WC-10Co
   75WC-15Co-10Ni
   Co0.3Ni0.3Fe0.2Cr0.2
   ```

---

### ❌ "请至少选择一个粘结相元素"

**症状**: Virtual Screening 无法开始

**原因**: 未选择候选元素

**解决方案**:

在 Virtual Screening 页面:
1. 在左侧栏选择至少 2 个粘结相元素
2. 设置合理的参数范围
3. 点击 "开始筛选"

---

## 🔍 错误信息索引

### "Training Failed: [具体错误]"

**位置**: Model Training 页面

**常见原因**:
1. 特征数据缺失 → 先运行 Process Agent
2. 目标变量缺失 → 检查数据文件
3. 数据类型错误 → 确保数值列为 float/int

---

### "模型目录不存在: models/"

**位置**: Virtual Screening 页面

**原因**: 未训练任何模型

**解决方案**: 先在 Model Training 页面训练并保存模型

---

### "筛选失败: [错误]"

**位置**: Virtual Screening

**常见原因**:
1. 模型未加载 → 检查 models/ 目录
2. 参数范围无效 → 最小值 < 最大值
3. 生成数量过大 → 降低到 <10,000

---

### "处理失败: [错误]"

**位置**: HEA Data Preprocessing / Process Agent

**常见原因**:
1. 文件格式错误 → 使用标准 CSV/Excel
2. 编码问题 → 保存为 UTF-8
3. 缺少必需列 → 检查 Composition 列

---

## 🆘 获取更多帮助

如果上述方法无法解决您的问题:

### 1. 检查日志

查看终端输出的完整错误信息:
```bash
streamlit run Home.py 2>&1 | tee debug.log
```

### 2. 搜索文档

- [README.md](../README.md) - 完整功能说明
- [INSTALLATION.md](../INSTALLATION.md) - 详细安装指南
- [QUICK_START.md](QUICK_START.md) - 快速上手

### 3. 提交 Issue

访问 [GitHub Issues](https://github.com/YHzed/HEAC-0.2/issues) 并提供:
- **环境信息**: OS, Python 版本, 安装方式
- **错误信息**: 完整的终端输出
- **重现步骤**: 如何触发错误
- **预期行为**: 应该发生什么

### 4. 社区支持

- GitHub Discussions
- 项目 Wiki
- 联系维护者

---

## ✅ 调试检查清单

问题解决前验证:

- [ ] 使用正确的 Python 版本 (3.10 或 3.11)
- [ ] 虚拟环境已激活
- [ ] 所有依赖已安装 (`pip list`)
- [ ] 在项目根目录运行
- [ ] `.env` 文件配置正确
- [ ] 模型文件存在(如需要)
- [ ] 数据格式符合要求
- [ ] 终端显示完整错误信息
- [ ] 已尝试重启应用
- [ ] 已清理缓存 (`st.cache_data.clear()`)

---

## 💡 预防性建议

### 定期维护

```bash
# 1. 更新依赖
pip install --upgrade -r requirements.txt

# 2. 更新项目
git pull origin main

# 3. 清理缓存
rm -rf __pycache__ .streamlit/cache
```

### 备份重要数据

```bash
# 备份训练数据
cp -r "training data" "training data_backup"

# 备份模型
cp -r models models_backup
```

### 使用虚拟环境

避免依赖冲突,始终使用虚拟环境:
```bash
# Conda (推荐)
conda create -n heac-0.2 python=3.11
conda activate heac-0.2

# venv
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows
```

---

*故障排除指南 v1.0 | 最后更新: 2026-01-22*  
*如发现新问题或解决方案,欢迎贡献到本文档*
