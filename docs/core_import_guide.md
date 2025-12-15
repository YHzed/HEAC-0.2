# Core模块统一导入示例

本文档展示如何使用更新后的`core`模块统一导入接口。

## 基础导入

### 之前的导入方式（仍然有效）

```python
from core.hea_calculator import HEACalculator
from core.material_database import db
from core.localization import get_text
from core.dataset_manager import DatasetManager
```

### 新的统一导入方式（推荐）

```python
from core import (
    HEACalculator,
    db,
    get_text,
    DatasetManager,
)
```

## 完整示例

### 1. 基本使用

```python
# 统一导入core模块组件
from core import (
    HEACalculator,
    MaterialProcessor,
    db,
    config,
    get_text,
)

# 使用计算器
calc = HEACalculator()
composition = {'Al': 1.0, 'Co': 1.0, 'Cr': 1.0, 'Fe': 1.0, 'Ni': 1.0}
vec = calc.calculate_vec(composition)
print(f"VEC: {vec}")  # 输出: VEC: 7.2

# 使用数据库
enthalpy = db.get_enthalpy('Al', 'Fe')
print(f"Al-Fe混合焓: {enthalpy} kJ/mol")
```

### 2. Streamlit应用页面（pages目录）

```python
import streamlit as st
import pandas as pd

# 之前需要多个单独的导入
# from core.data_processor import DataProcessor
# from core.analysis import Analyzer
# from core.models import ModelFactory, ModelTrainer
# from core.localization import get_text
# from core.dataset_manager import DatasetManager
# from core.model_manager import ModelManager

# 现在统一导入（推荐）
from core import (
    DataProcessor,
    Analyzer,
    ModelFactory,
    ModelTrainer,
    get_text,
    DatasetManager,
    ModelManager,
)

st.title(get_text('app_title'))
# ... 其他代码
```

### 3. 检查可选依赖

```python
import core

# 检查sklearn是否可用
if core._HAS_SKLEARN:
    from core import DataProcessor, Analyzer
    # 使用数据处理功能
    dp = DataProcessor()
else:
    print("警告: sklearn未安装，数据处理功能不可用")

# 检查ML模型是否可用
if core._HAS_ML:
    from core import ModelFactory, ModelTrainer, Optimizer
    # 使用ML功能
    model = ModelFactory.get_model('regression', 'Random Forest')
else:
    print("警告: ML依赖未完全安装")

# 检查Materials Project API
if core._HAS_MP_API:
    from core import MaterialsProjectClient
    # 使用MP API
else:
    print("警告: Materials Project API未安装")

# 检查Streamlit相关功能
if core._HAS_STREAMLIT:
    from core import ActivityLogger, initialize_session_state
    initialize_session_state()
else:
    print("信息: Streamlit环境未检测到")
```

## 可用的导出模块

### 核心计算
- `HEACalculator` - HEA参数计算器
- `hea_calc` - HEACalculator实例
- `MaterialProcessor` - 材料处理器

### 数据库
- `MaterialDatabase` - 材料数据库类
- `db` - MaterialDatabase实例
- `DatasetManager` - 数据集管理器

### 数据处理（需要sklearn）
- `DataProcessor` - 数据处理器
- `Analyzer` - 数据分析器

### 机器学习（需要sklearn等）
- `ModelFactory` - 模型工厂
- `ModelTrainer` - 模型训练器
- `Optimizer` - 超参数优化器
- `ModelManager` - 模型管理器

### 工具
- `Config` - 配置类
- `config` - Config实例
- `get_text` - 本地化文本获取函数
- `FormatConverter` - 格式转换器（可选）

### Streamlit相关（需要streamlit）
- `ActivityLogger` - 活动日志记录器
- `initialize_session_state` - 会话状态初始化

### Materials Project（需要mp-api）
- `MaterialsProjectClient` - MP API客户端

### 特性标志
- `_HAS_SKLEARN` - sklearn是否可用
- `_HAS_ML` - ML依赖是否完整
- `_HAS_MP_API` - MP API是否可用
- `_HAS_CONVERTER` - 格式转换器是否可用
- `_HAS_STREAMLIT` - Streamlit是否可用

## 迁移指南

如果你有现有的代码使用旧的导入方式，不用担心！两种方式都有效：

### 选项1: 保持不变
旧的导入方式仍然完全兼容，无需修改。

### 选项2: 逐步迁移
建议在新代码中使用统一导入，旧代码可以在维护时逐步更新。

### 示例迁移

**之前** (pages/1_General_ML_Lab.py):
```python
from core.data_processor import DataProcessor
from core.analysis import Analyzer
from core.models import ModelFactory, ModelTrainer
from core.optimization import Optimizer
from core.localization import get_text
from core.dataset_manager import DatasetManager
from core.model_manager import ModelManager
from core.hea_cermet import MaterialProcessor
from core.activity_logger import ActivityLogger
from core.session import initialize_session_state
```

**之后** (推荐):
```python
from core import (
    DataProcessor,
    Analyzer,
    ModelFactory,
    ModelTrainer,
    Optimizer,
    get_text,
    DatasetManager,
    ModelManager,
    MaterialProcessor,
    ActivityLogger,
    initialize_session_state,
)
```

好处：
- ✅ 更简洁
- ✅ 统一的导入来源
- ✅ 更容易维护
- ✅ 向后兼容

## 版本信息

```python
import core
print(core.__version__)  # 输出: 0.2.0
```
