# HEA & 金属陶瓷单点分析：当前理论基础报告

本报告详细列出了 `core/system_architecture.py` 中 `PhysicsEngine` 和 `AIPredictor` 类目前实际使用的理论模型、公式及逻辑。请审阅此报告并在其上进行指示或修正。

## 1. 物理引擎 (Physics Engine)
**代码位置**: `core/system_architecture.py` -> `PhysicsEngine`

该模块将“设计空间输入”（成分、烧结工艺）转化为“物理特征”。

### 1.1 原子尺度特征 (Atomic Features)
*   **价电子浓度 (VEC)**
    *   **公式**: $VEC_{mix} = \sum (c_i \times VEC_i)$
    *   **来源**: Hume-Rothery 规则延伸。
    *   **当前判断逻辑**: 若 $VEC \ge 8.0$，假设为 FCC 结构（延性好）；否则为 BCC（强度高但脆）。
*   **混合熵 ($S_{mix}$)**
    *   **公式**: $S_{mix} = -R \sum c_i \ln c_i$ (理想溶液模型)
    *   **单位**: 无量纲 (因代码中省略了气体常数 R，直接计算 $\sum c \ln c$)。
*   **混合焓 ($H_{mix}$)**
    *   **公式**: $H_{mix} = \sum_{i<j} 4 H_{ij} c_i c_j$
    *   **数据**: $H_{ij}$ 来自 Miedema 模型二元焓数据库 (`enthalpy.json`)。

### 1.2 界面与微观结构 (Interface & Microstructure)
*   **晶格错配度 (Lattice Mismatch)**
    *   **公式**: $\epsilon = |a_{binder} - a_{WC}| / a_{WC}$
    *   **粘结相晶格常数 ($a_{binder}$)**:
        *   使用维嘉德定律 (Vegard's Law) 估算: $a_{binder} = \sum c_i a_i$
        *   $a_i$ 估算: 基于原子半径 $r_i$ 和预测的晶体结构 (FCC/BCC) 进行几何推导。
            *   FCC: $a = r \times 2\sqrt{2}$
            *   BCC: $a = r \times 4 / \sqrt{3}$
    *   **目标相 (WC)**: 固定 $a_{WC} \approx 2.906 Å$。
*   **热膨胀系数错配 (CTE Mismatch)**
    *   **公式**: $\Delta \alpha = |\alpha_{binder} - \alpha_{WC}|$
    *   **计算**: $\alpha_{binder} = \sum c_i \alpha_i$ (线性混合)
    *   **现状**: 依赖 `elements.json` 中的 `cte_micron_per_k` 数据。如果缺失则忽略。
*   **润湿性指数 (Wettability Index)**
    *   **公式**: $W_{index} = \sum c_i W_i$
    *   **现状**: $W_i$ 是一个经验评分 (0-10)，目前主要基于数据库中预设的 `wettability_index_wc` 字段。

### 1.3 工艺参数特征 (Process Features)
*   **同系温度 (Homologous Temperature)**
    *   **公式**: $T_{Homo} = T_{sinter} / T_{liquidus}$
    *   **$T_{liquidus}$**: 目前简化为线性熔点平均 $\sum c_i T_{m,i}$ (注：这通常会高估共晶合金的熔点)。
    *   **评价**: $T_{Homo} > 0.8$ 通常意味着烧结致密化良好。
*   **致密化因子 (Densification Proxy)**
    *   **公式**: $F_{dens} = T_{Homo} \times \ln(t_{time} + 1)$
    *   **逻辑**: 温度越高（相对于熔点）、时间越长，致密度越好。

---

## 2. AI 性能预测 (AI Predictor / Heuristics)
**代码位置**: `core/system_architecture.py` -> `AIPredictor`

目前尚未加载真实的 ML 模型，而是使用**启发式公式 (Toy Models)** 进行演示。

### 2.1 界面质量 (Interface Quality)
*   **公式**: $Q_{int} = 0.5 \times (1 - \min(\epsilon, 1.0)) + 0.5 \times (W_{index} / 10)$
*   **逻辑**: 错配度越低、润湿性越好，界面质量越高 (0 ~ 1)。

### 2.2 维氏硬度 (HV)
*   **公式**: $HV = 1600 + 200 \times |VEC - 8.0| - \text{PorosityPenalty}$
*   **逻辑**:
    *   基准硬度 1600。
    *   固溶强化项：假设偏离 VEC 8.0 (FCC稳定区) 会增加晶格畸变/强度。
    *   孔隙率惩罚：如果 $T_{Homo} < 0.9$，扣除硬度。

### 2.3 断裂韧性 (K1C)
*   **公式**: $K_{1C} = 10 + 2 \times \max(0, VEC - 7.5) + 5 \times Q_{int}$
*   **逻辑**:
    *   基准韧性 10。
    *   VEC > 7.5 (趋向FCC) 提供延/韧性加成。
    *   界面质量 ($Q_{int}$) 好，显著提高韧性。

---

## 3. 待确认/需指示事项 (Instructions Needed)
请针对以下几点给予指示：

1.  **液相线计算**: 目前是线性加权，是否需要引入简单的“共晶压低”修正系数？
2.  **晶格错配计算**: 是否需要更精确的晶格常数模型？
3.  **预测模型**: 目前的硬度和韧性公式仅为占位符。您是否希望替换为更具体的经验公式（如 Yi-Liu 方程或其他文献公式）？
