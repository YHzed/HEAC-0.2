# 数据库架构升级 v2.0 - 快速参考

## 🚀 5分钟快速开始

### 1. 创建新数据库
```python
from core import CermetDatabaseV2
db = CermetDatabaseV2('cermet_v2.db')
db.create_tables()
```

### 2. 导入数据
```python
# 单条数据（自动解析+特征计算）
exp_id = db.add_experiment(
    raw_composition="WC-10CoCrFeNi",
    hv=1500, kic=12,
    auto_calculate_features=True
)
```

### 3. 查询数据
```python
# 查询单条
data = db.get_experiment(exp_id)
print(f"VEC: {data['features']['vec_binder']}")

# 统计
stats = db.get_statistics()
```

### 4. 提取训练数据
```python
from core.data_extractor import DataExtractor
extractor = DataExtractor(db)
df = extractor.get_training_data(target='hv', hea_only=True)
```

---

## 📊 支持的成分格式

| 格式 | 示例 | 说明 |
|------|------|------|
| 短横线 | `WC-10CoCrFeNi` | 最常用 |
| 空格 | `WC 85 Co 10 Ni 5` | 多组分 |
| b前缀 | `b WC 25 Co` | 粘结相百分比 |
| 复杂 | `b WC 69 CoCrFeNiMo 1 Cr3C2 10 Mo` | 第二硬质相+添加剂 |
| x占位符 | `WC x Co` | 未知含量 |

---

## 🔧 核心功能

✅ 自动成分解析（4种格式）  
✅ 相分离存储（硬质相/粘结相）  
✅ wt%↔vol% 自动转换  
✅ 物理特征自动计算（VEC、晶格失配等）  
✅ Proxy Models 集成（可选）  
✅ 多表高效查询  
✅ 批量数据提取  

---

## 📝 常用命令

```bash
# 运行测试
python tests/test_core_components.py
python tests/test_full_integration.py

# 数据迁移
python scripts/migrate_to_v2.py --old-db cermet_materials.db --limit 100
```

---

## 📖 完整文档

- 部署指南: `docs/database_v2_deployment.md`
- 工作总结: `walkthrough.md`
- 实施计划: `implementation_plan.md`

---

**版本**: v2.0 | **状态**: 生产就绪 ✅
