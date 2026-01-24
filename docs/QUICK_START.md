# HEAC 0.2 快速开始指南

**目标**: 5 分钟内成功运行 HEAC 0.2 智能材料设计平台

---

## ⏱️ 30 秒安装

### Windows 用户(推荐)

**先决条件**: 已安装 [Conda](https://docs.conda.io/en/latest/miniconda.html)

```bash
# 1. 克隆项目
git clone https://github.com/YHzed/HEAC-0.2.git
cd HEAC-0.2

# 2. 创建环境
conda env create -f environment.yml

# 3. 双击启动
start.bat
```

✅ **完成!** 应用将自动在浏览器打开 `http://localhost:8501`

---

### macOS/Linux 用户

```bash
# 1. 克隆项目
git clone https://github.com/YHzed/HEAC-0.2.git
cd HEAC-0.2

# 2. 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动应用
streamlit run Home.py
```

浏览器访问: `http://localhost:8501`

---

## 🚀 2 分钟 - 首次运行

### 启动应用

**Windows**:
```bash
# 方法 1: 双击
start.bat

# 方法 2: 命令行
conda activate heac-0.2
streamlit run Home.py
```

**macOS/Linux**:
```bash
source .venv/bin/activate
streamlit run Home.py
```

### 界面预览

应用启动后,您将看到:

1. **主页** - 系统概览与核心功能入口
   - 📊 系统状态:模型精度、缓存性能、数据库规模
   - 🚀 核心功能:材料预测、数据管理、虚拟筛选
   
2. **侧边栏导航** - 8 个功能页面
   - 🧪 General ML Lab - 通用机器学习
   - 🔬 HEA Cermet Lab - HEA 陶瓷实验室
   - 📊 Process Agent - 数据处理代理
   - 🤖 Proxy Models - 辅助预测模型
   - 🎯 Model Training - 模型训练
   - 🔍 Virtual Screening - 虚拟筛选
   - 📂 Database Manager - 数据库管理

3. **新的学术风格 UI** (2026-01-22 更新)
   - Crimson Pro 标题字体 + Atkinson Hyperlegible 正文
   - 蓝色系专业配色
   - 优雅的卡片悬停效果

---

## 🎯 5 分钟 - 完整工作流

### 示例: 单点材料性能预测

让我们通过一个简单的例子,体验完整的预测流程。

#### Step 1: 访问 Proxy Models 页面

1. 点击侧边栏 **"Proxy Models"** (或主页的 "🎯 访问辅助模型页面" 按钮)
2. 您将看到 3 个训练好的模型:
   - Formation Energy (形成能) - R² = 0.97
   - Lattice Parameter (晶格参数) - R² = 0.96
   - Magnetic Moment (磁矩) - R² = 0.93

#### Step 2: 输入材料成分

在 **"单成分分析"** 标签页:

```
示例成分: Co0.3Ni0.3Fe0.2Cr0.2
```

**输入格式说明**:
- 元素符号 + 原子分数
- 所有分数加起来应等于 1.0
- 支持的元素:Co, Ni, Fe, Cr, Mn, Cu, Al, Ti 等

#### Step 3: 查看预测结果

点击 **"开始预测"** 后,系统将显示:

| 属性 | 预测值 | 单位 |
|------|--------|------|
| Formation Energy | -0.42 | eV/atom |
| Lattice Parameter | 3.58 | Å |
| Magnetic Moment | 1.23 | μB |

**结果解读**:
- 负的形成能表示该合金热力学稳定
- 晶格参数约 3.58 Å,接近 FCC 结构
- 具有铁磁性 (磁矩 > 0)

#### Step 4: 导出结果

点击 **"下载结果 CSV"** 保存预测数据,用于后续分析。

---

## 📚 下一步

恭喜!您已经成功运行 HEAC 0.2 并完成了第一个预测。

### 探索更多功能

1. **虚拟筛选**
   - 批量生成候选材料
   - 自动筛选高性能配方
   - 导出推荐方案

2. **数据管理**
   - 导入实验数据 (CSV/Excel)
   - 自动特征计算 (50x 速度提升)
   - 数据库查询与导出

3. **模型训练**
   - 训练自定义预测模型
   - SHAP 可解释性分析
   - 超参数自动优化 (Optuna)

### 学习资源

- **详细文档**: [`README.md`](../README.md) - 完整功能说明
- **安装指南**: [`INSTALLATION.md`](../INSTALLATION.md) - 进阶配置
- **API 参考**: `docs/` 目录 - 代码示例
- **故障排除**: 见下方常见问题

---

## ❓ 常见问题

### Q1: "找不到 heac-0.2 环境"

**解决方案**:
```bash
# 创建环境
conda env create -f environment.yml

# 激活环境
conda activate heac-0.2
```

---

### Q2: "Streamlit import error"

**解决方案**:
```bash
# 确保在正确的环境中
conda activate heac-0.2  # 或 source .venv/bin/activate

# 重新安装 streamlit
pip install streamlit>=1.30.0
```

---

### Q3: "Materials Project API Error"

**原因**: API 密钥未配置

**解决方案**:
1. 访问 [Materials Project Dashboard](https://materialsproject.org/dashboard)
2. 复制您的 API 密钥
3. 编辑 `.env` 文件:
   ```
   MP_API_KEY=your_actual_api_key_here
   ```
4. 重启应用

**注意**: Proxy Models 基于本地训练模型,无需 API 密钥即可使用。

---

### Q4: "应用启动很慢"

**原因**: 首次运行需要加载模型和字体

**正常情况**:
- 首次启动: 10-15 秒
- 后续启动: 3-5 秒

**优化建议**:
- 确保 SSD 存储
- 关闭不必要的后台程序
- 检查 `.streamlit/custom.css` 中的字体加载

---

### Q5: "如何停止应用?"

**方法**:
1. 在终端按 `Ctrl + C`
2. 关闭浏览器标签页(应用仍在后台运行)
3. Windows: 关闭命令行窗口

---

## 🆘 获取帮助

如果遇到其他问题:

1. **查看日志**: 终端输出的错误信息
2. **检查文档**: `INSTALLATION.md` 中的故障排除章节
3. **提交 Issue**: [GitHub Issues](https://github.com/YHzed/HEAC-0.2/issues)
4. **更新项目**: `git pull origin main` 获取最新修复

---

## ✅ 检查清单

安装成功的标志:

- [ ] 浏览器打开 `http://localhost:8501`
- [ ] 看到 "HEAC - 高熵合金硬质合金智能设计平台" 标题
- [ ] 系统概览显示 4 个指标卡片
- [ ] 侧边栏显示 8 个功能页面
- [ ] 页面使用 Crimson Pro 字体和蓝色主题
- [ ] 可以访问 Proxy Models 页面
- [ ] 单点预测功能正常

如果以上全部打勾,恭喜您成功安装! 🎉

---

*快速开始指南 v1.0 | 最后更新: 2026-01-22*
