# Materials Project 数据库使用指南

本指南介绍如何使用项目的 Materials Project (MP) 数据库集成功能。

## 目录

- [快速开始](#快速开始)
- [配置API密钥](#配置api密钥)
- [使用数据库API](#使用数据库api)
- [命令行工具](#命令行工具)
- [缓存管理](#缓存管理)
- [常见问题](#常见问题)

## 快速开始

### 1. 获取API密钥

1. 访问 [Materials Project](https://materialsproject.org/)
2. 注册或登录账户
3. 进入 [Dashboard页面](https://materialsproject.org/dashboard)
4. 复制您的API密钥

### 2. 配置环境

在项目根目录的 `.env` 文件中配置API密钥：

```bash
MP_API_KEY=your_api_key_here
```

> ⚠️ **安全提示**: `.env` 文件已被添加到 `.gitignore`，不会被提交到版本控制系统。

### 3. 测试连接

运行测试确保配置正确：

```bash
python tests/test_mp_integration.py
```

## 使用数据库API

### 导入数据库

```python
from core.material_database import db
```

### 基本查询

#### 查询本地数据

```python
# 获取元素属性
al = db.get_element("Al")
print(f"铝的密度: {al['rho']} g/cm³")

# 获取化合物密度（仅本地）
wc_density = db.get_compound_density("WC")
print(f"WC密度: {wc_density} g/cm³")

# 获取生成焓（仅本地）
wc_enthalpy = db.get_formation_enthalpy("WC")
print(f"WC生成焓: {wc_enthalpy} kJ/mol")
```

#### 查询Materials Project数据

```python
# 从MP获取完整材料数据
tio2_data = db.get_mp_data("TiO2")
print(f"Material ID: {tio2_data['material_id']}")
print(f"密度: {tio2_data['density']} g/cm³")
print(f"能带隙: {tio2_data['band_gap']} eV")

# 仅获取密度
density = db.get_density_from_mp("TiO2")
print(f"TiO2密度: {density} g/cm³")

# 仅获取生成焓
energy = db.get_formation_enthalpy_from_mp("TiO2")
print(f"TiO2生成能: {energy} eV/atom")
```

#### 自动回退机制

```python
# 优先使用本地数据，本地没有时自动从MP获取
density = db.get_compound_density("CaTiO3", use_mp=True)

# WC在本地有数据，直接返回本地值
wc_density = db.get_compound_density("WC", use_mp=True)  # 返回15.63

# CaTiO3本地没有，自动从MP获取
cto_density = db.get_compound_density("CaTiO3", use_mp=True)
```

### 搜索功能

```python
# 搜索特定化学系统的所有材料
materials = db.search_mp_materials("Fe-C")
for mat in materials[:5]:
    print(f"{mat['formula_pretty']}: {mat['material_id']}")

# 搜索特定化学式
tio2_variants = db.search_mp_materials("TiO2")
print(f"找到 {len(tio2_variants)} 个TiO2相")
```

### 更新本地数据库

```python
# 从MP获取数据并保存到本地JSON
success = db.update_compound_from_mp("TiO2", save=True)

if success:
    print("成功更新本地数据库")
```

## 命令行工具

### 数据获取工具 (fetch_mp_data.py)

#### 获取单个材料

```bash
# 基本查询
python scripts/fetch_mp_data.py --formula "TiO2"

# 详细信息
python scripts/fetch_mp_data.py --formula "TiO2" --verbose

# 查询并更新到本地数据库
python scripts/fetch_mp_data.py --formula "TiO2" --update
```

#### 批量获取材料

创建一个文本文件 `compounds.txt`，每行一个化学式：

```
TiO2
Al2O3
Fe2O3
SiO2
```

然后运行：

```bash
python scripts/fetch_mp_data.py --batch compounds.txt --update
```

#### 搜索材料

```bash
# 搜索Fe-C系统
python scripts/fetch_mp_data.py --search "Fe-C"

# 显示更多结果
python scripts/fetch_mp_data.py --search "Fe-C" --max-results 20
```

### 缓存管理工具 (browse_mp_cache.py)

#### 查看缓存统计

```bash
python scripts/browse_mp_cache.py --stats
```

输出示例：
```
============================================================
Materials Project 缓存统计
============================================================
缓存目录: E:\ML\HEAC0.2\core\data\mp_cache
缓存文件数: 15
总大小: 245.67 KB
缓存TTL: 30 天
过期文件数: 3
============================================================
```

#### 列出所有缓存

```bash
python scripts/browse_mp_cache.py --list
```

#### 查看特定缓存内容

```bash
python scripts/browse_mp_cache.py --view summary_TiO2.json
```

#### 清理过期缓存

```bash
# 模拟运行（不实际删除）
python scripts/browse_mp_cache.py --clean --dry-run

# 实际清理
python scripts/browse_mp_cache.py --clean
```

## 缓存管理

### 缓存配置

在 `.env` 文件中配置缓存参数：

```bash
# 启用缓存
MP_CACHE_ENABLED=true

# 缓存目录
MP_CACHE_DIR=core/data/mp_cache

# 缓存过期时间（天）
MP_CACHE_TTL_DAYS=30

# API速率限制（每秒请求数）
MP_RATE_LIMIT=10
```

### 缓存工作原理

1. **首次请求**: 从Materials Project API获取数据，保存到本地缓存
2. **后续请求**: 如果缓存未过期，直接从缓存读取
3. **过期处理**: 缓存超过TTL后，下次请求会重新从API获取

### 手动清理缓存

```bash
# 删除所有缓存文件
rm -rf core/data/mp_cache/*

# 或使用提供的工具
python scripts/browse_mp_cache.py --clean
```

## 常见问题

### Q: 如何处理API速率限制？

A: 项目内置了速率限制控制，默认每秒最多10个请求。可以在`.env`中调整`MP_RATE_LIMIT`参数。

### Q: 本地数据和MP数据单位不一致怎么办？

A: 
- **密度**: 都是 g/cm³
- **生成焓**: 本地数据通常是 kJ/mol，MP数据是 eV/atom
- 使用时注意查看数据来源和单位

### Q: 如何知道数据来自本地还是MP？

A: 使用`update_compound_from_mp`更新的数据会包含`source`字段：

```python
data = db._compounds_data.get("TiO2")
print(data.get("source"))  # "Materials Project"
```

### Q: 批量更新时如何处理错误？

A: `fetch_mp_data.py`会捕获并显示错误，继续处理剩余材料。查看输出的成功/失败统计。

### Q: 缓存文件可以手动编辑吗？

A: 不建议。缓存文件是JSON格式，包含元数据。如需修改数据，应该修改`core/data/compounds.json`等源文件。

### Q: 如何临时禁用缓存？

A: 在`.env`中设置：
```bash
MP_CACHE_ENABLED=false
```

### Q: API密钥泄露了怎么办？

A: 
1. 立即在 [Materials Project Dashboard](https://materialsproject.org/dashboard) 重新生成密钥
2. 更新`.env`文件
3. 如果密钥已提交到Git，还需要清理Git历史

## 高级用法

### 自定义缓存位置

```python
from core.config import Config

# 临时修改缓存目录
Config.MP_CACHE_DIR = "custom/cache/path"
```

### 批量处理示例

```python
from core.material_database import db

compounds = ["TiO2", "Al2O3", "SiO2", "Fe2O3"]

for compound in compounds:
    try:
        density = db.get_density_from_mp(compound)
        if density:
            print(f"{compound}: {density:.2f} g/cm³")
            # 保存到本地
            db.update_compound_from_mp(compound, save=True)
    except Exception as e:
        print(f"Error processing {compound}: {e}")
```

## 相关资源

- [Materials Project 官方文档](https://docs.materialsproject.org/)
- [MP API 文档](https://api.materialsproject.org/)
- [mp-api Python包](https://github.com/materialsproject/api)
