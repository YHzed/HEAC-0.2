"""
数据库架构升级 - 部署指南

本文档提供新数据库架构的部署步骤和使用说明
"""

# 数据库架构 v2.0 部署指南

## 📦 前置要求

### 依赖包
```bash
pip install sqlalchemy pandas numpy pymatgen tqdm
```

### 可选依赖
```bash
pip install matminer  # Matminer 特征（可选）
```

---

## 🚀 快速开始

### 1. 创建新数据库

```python
from core import CermetDatabaseV2

# 创建数据库实例
db = CermetDatabaseV2('cermet_master_v2.db')

# 创建表结构
db.create_tables()

print("✅ 数据库初始化完成")
```

### 2. 添加数据（手动导入）

```python
# 单条数据
exp_id = db.add_experiment(
    raw_composition="WC-10CoCrFeNi",
    source_id="manual_entry",
    sinter_temp_c=1400,
    grain_size_um=1.0,
    hv=1500,
    kic=12.0,
    auto_calculate_features=True  # 自动计算物理特征
)

print(f"添加成功，ID={exp_id}")
```

### 3. 批量导入（从 Excel/CSV）

```python
import pandas as pd

# 读取数据
df = pd.read_excel("your_data.xlsx")

# 批量导入
for idx, row in df.iterrows():
    try:
        db.add_experiment(
            raw_composition=row['composition'],
            hv=row.get('HV'),
            kic=row.get('KIC'),
            sinter_temp_c=row.get('temperature'),
            auto_calculate_features=True
        )
    except Exception as e:
        print(f"行 {idx} 失败: {e}")
```

### 4. 查询数据

```python
# 查询单条
data = db.get_experiment(exp_id=1)
print(f"成分: {data['composition']['binder_formula']}")
print(f"HEA: {data['composition']['is_hea']}")
print(f"VEC: {data['features']['vec_binder']}")

# 统计信息
stats = db.get_statistics()
print(f"总数: {stats['total_experiments']}")
print(f"HEA: {stats['hea_count']}")
```

### 5. 提取训练数据

```python
from core.data_extractor import DataExtractor

extractor = DataExtractor(db)

# 提取 HEA 训练数据
df_train = extractor.get_training_data(
    target='hv',
    hea_only=True,
    fillna=True
)

print(f"训练集大小: {len(df_train)}")
print(f"特征数量: {len(df_train.columns)}")
```

---

## 🔄 数据迁移（从旧数据库）

### 选项 1: 自动迁移脚本

```bash
# 测试迁移（100条）
python scripts/migrate_to_v2.py --old-db cermet_materials.db --limit 100

# 全量迁移
python scripts/migrate_to_v2.py --old-db cermet_materials.db --new-db cermet_v2.db

# 不计算特征（加快速度）
python scripts/migrate_to_v2.py --old-db cermet_materials.db --no-features
```

### 选项 2: 手动导出导入

```python
# 1. 从旧数据库导出
from core import CermetDB
old_db = CermetDB('cermet_materials.db')
df = old_db.fetch_data()
df.to_csv('backup_data.csv', index=False)

# 2. 导入到新数据库
# （使用上面的批量导入代码）
```

---

## 🧪 测试验证

### 运行单元测试

```bash
# 核心组件测试
python tests/test_core_components.py

# 数据库原型测试
python tests/test_db_v2_prototype.py
```

### 预期结果
```
✅ 成分解析器: 6/6 通过
✅ 物理计算器: 5/5 通过
✅ 特征引擎: 3/3 通过
✅ 数据库原型: 3/3 通过
```

---

## 📊 架构对比

| 特性 | v1.0 (旧) | v2.0 (新) |
|------|----------|----------|
| 表结构 | 单表 | 4表关联 |
| 成分存储 | 原始字符串 | 分离+归一化 |
| 特征计算 | 手动 | 自动 |
| HEA识别 | 简单标记 | 智能判定 |
| 查询效率 | 全表扫描 | 索引优化 |

---

## ⚙️ 配置选项

### 关闭 Proxy Models（使用默认值）
```python
from core import FeatureEngine

engine = FeatureEngine()
features = engine.calculate_features(
    binder_formula="Co1Cr1Fe1Ni1",
    use_matminer=False  # 不使用 Matminer
)
```

### 启用 Matminer 特征
```python
features = engine.calculate_features(
    binder_formula="Co1Cr1Fe1Ni1",
    use_matminer=True  # 使用完整化学特征
)
```

---

## 🐛 常见问题

### Q1: 导入时成分解析失败？
**A**: 检查成分格式，支持：
- `WC-10CoCrFeNi`
- `WC 85 Co 10 Ni 5`
- `b WC 25 Co`

### Q2: 特征计算很慢？
**A**: 首次计算会较慢，后续会使用缓存。可设置 `auto_calculate_features=False` 跳过。

### Q3: 如何更新已有数据的特征？
**A**: 
```python
# 批量更新特征
from core import FeatureEngine
engine = FeatureEngine()

# 重新计算
for exp_id in range(1, 100):
    exp = db.get_experiment(exp_id)
    if exp:
        features = engine.calculate_features(...)
        # 更新数据库（需实现 update 方法）
```

---

## 📝 最佳实践

1. **备份数据**：迁移前务必备份旧数据库
2. **小批量测试**：先迁移100条数据验证
3. **定期检查**：查看统计信息确认数据完整性
4. **特征缓存**：避免重复计算，提升性能

---

## 🔗 相关文件

- **实施计划**: `implementation_plan.md`
- **任务清单**: `task.md`
- **工作总结**: `walkthrough.md`
- **核心代码**:
  - `core/db_models_v2.py` - ORM 模型
  - `core/composition_parser.py` - 成分解析
  - `core/physics_calculator.py` - 物理计算
  - `core/feature_engine.py` - 特征引擎
  - `core/data_extractor.py` - 数据提取

---

> **版本**: v2.0  
> **更新**: 2025-12-25  
> **状态**: ✅ 生产就绪
