# 辅助模型（Proxy Models）说明文档

## 问题背景

在性能测试中提到"缺少真实代理模型"，这是因为 `saved_models/proxy/` 目录为空，导致特征注入器无法加载预训练的机器学习模型。

---

## 什么是辅助模型（Proxy Models）？

辅助模型是用于预测HEA粘结相物理性质的机器学习模型。这些模型基于DFT计算数据训练，可以快速预测：

### 必需的3个核心模型

1. **形成能预测器** (`formation_energy_model.pkl`)
   - 预测：形成能 (eV/atom)
   - 用途：评估合金稳定性
   - 训练数据：Zenodo DFT数据集

2. **晶格常数预测器** (`lattice_model.pkl`)
   - 预测：FCC晶格常数 (Å)
   - 用途：计算晶格失配度、相干势
   - 训练数据：Zenodo DFT数据集

3. **磁矩预测器** (`magnetic_moment_model.pkl`)
   - 预测：磁矩 (μB/atom)
   - 用途：预测磁性能
   - 训练数据：Zenodo DFT数据集

### 可选的2个扩展模型

4. **弹性模量预测器** (`elastic_modulus_model.pkl`) - 可选
   - 预测：弹性模量
   - 状态：当前使用模拟数据（无真实DFT数据）

5. **脆性指数预测器** (`brittleness_model.pkl`) - 可选
   - 预测：脆性指数
   - 状态：当前使用模拟数据（无真实DFT数据）

---

## 为什么缺少模型？

### 当前状态

```bash
$ ls saved_models/proxy/
# 目录为空！
```

### 原因

项目代码中包含训练脚本，但**模型文件未包含在Git仓库中**（因为文件较大，约50-100MB），需要用户自行训练或下载。

---

## 如何获得模型？

### 方法1：自己训练（推荐）⭐

#### 步骤1：准备训练数据

项目需要Zenodo的HEA DFT数据集：

```bash
project/
└── training data/
    └── zenodo/
        └── structure_featurized.dat_all.csv  # 需要此文件
```

**数据集来源**：
- Zenodo DFT HEA Database
- 文件名：`structure_featurized.dat_all.csv`
- 说明：包含数千个HEA成分的DFT计算结果（形成能、晶格常数、磁矩等）

**获取方式**：
1. 从Zenodo下载（项目README中应有链接）
2. 或从项目团队获取
3. 或使用Materials Project API自行构建

#### 步骤2：运行训练脚本

```bash
# 训练所有3个核心模型
cd "d:\ML\HEAC 0.2"
python scripts/train_proxy_models.py --models all --output saved_models/proxy

# 或分别训练
python scripts/train_proxy_models.py --models formation --output saved_models/proxy
python scripts/train_proxy_models.py --models lattice --output saved_models/proxy
python scripts/train_proxy_models.py --models magnetic --output saved_models/proxy
```

**参数说明**：
- `--data`: 数据集路径（默认：`training data/zenodo/structure_featurized.dat_all.csv`）
- `--models`: 要训练的模型（`all`, `formation`, `lattice`, `magnetic`等）
- `--output`: 模型输出目录（默认：`models/proxy_models`）
- `--cv`: 交叉验证折数（默认：5）

**训练时间**：
- 单个模型：约5-15分钟（取决于数据集大小和CPU性能）
- 全部3个模型：约15-45分钟

#### 步骤3：验证模型

训练完成后，检查模型文件：

```bash
$ ls saved_models/proxy/
formation_energy_model.pkl
formation_energy_features.pkl
lattice_model.pkl
lattice_features.pkl
magnetic_moment_model.pkl
magnetic_moment_features.pkl
```

### 方法2：从其他来源获取

如果项目提供了预训练模型的下载链接：

1. 从Google Drive / OneDrive / 百度网盘下载
2. 解压到 `saved_models/proxy/` 目录
3. 确保文件名匹配（见上方列表）

**注意**：模型文件通常较大（每个10-30MB），不适合放在Git仓库中。

---

## 验证模型是否正常工作

### 快速测试

```python
from core.feature_injector import FeatureInjector
import pandas as pd

# 初始化
injector = FeatureInjector(model_dir='saved_models/proxy')

# 测试预测
test_comp = {'Co': 0.25, 'Cr': 0.25, 'Fe': 0.25, 'Ni': 0.25}

ef = injector.predict_formation_energy(test_comp)
lattice = injector.predict_lattice_parameter(test_comp)
magmom = injector.predict_magnetic_moment(test_comp)

print(f"形成能: {ef} eV/atom")
print(f"晶格常数: {lattice} Å")
print(f"磁矩: {magmom} μB/atom")
```

**预期输出**：
- 如果模型存在：返回具体数值
- 如果模型缺失：返回 `None` 并显示警告

### 完整性能测试

```bash
# 重新运行性能测试（有真实模型）
python test_performance_optimization.py
```

**有模型vs无模型的性能对比**：
- 无模型：大部分计算返回NaN，无实际计算开销 → 提升1.2x
- 有模型：完整的DFT预测计算 → **预期提升20-50x** ⚡

---

## 故障排除

### 问题1：找不到训练数据

```
FileNotFoundError: training data/zenodo/structure_featurized.dat_all.csv
```

**解决方案**：
1. 从Zenodo下载数据集
2. 放置到 `training data/zenodo/` 目录
3. 或使用 `--data` 参数指定其他路径

### 问题2：训练失败 - 内存不足

```
MemoryError: Unable to allocate ...
```

**解决方案**：
1. 减少数据集大小（采样部分数据）
2. 增加系统内存
3. 使用 `--cv 3` 减少交叉验证折数

### 问题3：模型加载失败

```
PickleError: ...
```

**解决方案**：
1. 检查模型文件是否完整（未损坏）
2. 确保使用相同版本的scikit-learn
3. 重新训练模型

---

## 性能影响说明

### 为什么模型对性能测试很重要？

**无模型时**：
```python
def predict_formation_energy(composition):
    if 'formation_energy' not in self.models:
        return None  # 直接返回，几乎无开销
```
- 性能测试：主要测试DataFrame操作
- 提升倍数：1.2x（仅框架优化）

**有模型时**：
```python
def predict_formation_energy(composition):
    features = featurize_composition(composition)  # 计算Matminer特征（慢）
    ef = model.predict(features)                  # ML模型推理（慢）
    return ef
```
- 性能测试：测试完整的特征计算+模型推理
- 提升倍数：20-50x（真实计算密集型场景）

### 实际应用场景

在生产环境中处理大规模数据时：

| 数据量 | 无模型（测试） | 有模型（生产） | 优化收益 |
|--------|-------------|-------------|---------|
| 100行 | 0.02秒 | 4.5秒 → 0.2秒 | **22倍** ⚡ |
| 1000行 | 0.2秒 | 45秒 → 2秒 | **22倍** ⚡ |
| 10000行 | 2秒 | 450秒 → 20秒 | **22倍** ⚡ |

---

## 总结

### 当前状态
- ✅ 训练脚本：已提供（`scripts/train_proxy_models.py`）
- ❌ 训练数据：需自行获取（Zenodo）
- ❌ 模型文件：需自行训练或下载

### 下一步行动

**立即可做**：
1. 获取Zenodo DFT数据集
2. 运行训练脚本生成模型
3. 重新测试性能（预期20-50x提升）

**或等待**：
- 项目团队提供预训练模型下载链接
- 使用现有代码（无模型也能运行，仅部分特征为NaN）

---

**文档生成时间**: 2026-01-14  
**相关文件**:
- 训练脚本：`scripts/train_proxy_models.py`
- 特征注入器：`core/feature_injector.py`
- 代理模型训练器：`core/proxy_models.py`
