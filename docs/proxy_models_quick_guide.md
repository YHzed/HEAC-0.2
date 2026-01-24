# 代理模型训练快速指南

## ✅ 推荐用法（仅训练3个有效模型）

```bash
cd "d:\ML\HEAC 0.2"

# 默认：仅训练有真实数据的模型
python scripts/train_proxy_models.py --output saved_models/proxy

# 等价于：
python scripts/train_proxy_models.py --models formation lattice magnetic --output saved_models/proxy
```

**训练的模型**：
1. ✅ formation_energy (R² ≈ 0.89)
2. ✅ lattice (R² ≈ 0.89)
3. ✅ magnetic_moment (R² ≈ 0.71)

**预计时间**: 15-30分钟

---

## ❌ 不推荐（包含失效模型）

```bash
# 不要使用 --models all，会训练失效的模型
python scripts/train_proxy_models.py --models all  # ⛔ 包含3个失效模型
```

**失效的模型**（已禁用）：
1. ❌ bulk_modulus (R² ≈ -0.50) - 使用随机数据
2. ❌ shear_modulus (R² ≈ -0.65) - 使用随机数据
3. ❌ brittleness (R² ≈ -0.60) - 使用随机数据

**问题原因**: `core/proxy_models.py` 第399-400行和448行使用 `np.random.normal()` 生成模拟数据

---

## 已完成的修改

### 1. 修改默认参数
**文件**: `scripts/train_proxy_models.py`
- **修改前**: `default=['all']` - 默认训练所有模型（包含失效的）
- **修改后**: `default=['formation', 'lattice', 'magnetic']` - 仅训练有效模型

### 2. 增强警告信息
弹性模量和脆性模型训练时会显示明确警告：
```
⚠️  警告: 弹性模量模型使用模拟数据，性能极差（R² ≈ -0.5）
   建议：跳过此模型或从Materials Project获取真实数据
```

---

## 验证

重新训练后，检查模型文件：

```bash
ls saved_models/proxy/
```

**预期输出**（仅6个文件）：
```
formation_energy_model.pkl
formation_energy_features.pkl
lattice_model.pkl  
lattice_features.pkl
magnetic_moment_model.pkl
magnetic_moment_features.pkl
```

**不应包含**：
- ❌ bulk_modulus_model.pkl
- ❌ shear_modulus_model.pkl
- ❌ brittleness_model.pkl

---

## 性能对比

| 模型 | 数据来源 | R² | 状态 |
|------|---------|-----|------|
| formation_energy | Zenodo DFT | 0.89 | ✅ 使用 |
| lattice | Zenodo DFT | 0.89 | ✅ 使用 |
| magnetic_moment | Zenodo DFT | 0.71 | ✅ 使用 |
| bulk_modulus | 随机数据 | -0.50 | ❌ 已禁用 |
| shear_modulus | 随机数据 | -0.65 | ❌ 已禁用 |
| brittleness | 随机数据 | -0.60 | ❌ 已禁用 |

---

**更新时间**: 2026-01-14  
**下一步**: 重新运行训练脚本，仅生成3个有效模型
