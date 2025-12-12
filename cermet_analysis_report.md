# 金属陶瓷(Cermet)分析计算理论与改进报告

本报告详细总结了目前系统中采用的计算理论模型，并依据最新的科学评估，指出了现有系统的理论短板，提出了针对性的改进方案与实施路线图。

---

## 1. 现有计算理论 (Current Theoretical Framework)

目前的系统主要基于“静态几何参数”和“线性加权混合法则”，适合作为机器学习的基础特征生成器 ($X$ Features)，但在指导实际烧结工艺和预测复杂相变方面存在局限。

### 1.1 基础热力学参数
目前主要位于 `core/hea_cermet.py`，采用经典高熵合金经验公式：
*   **混合熵 ($S_{mix}$)**: $\sum c_i \ln c_i$ (理想溶液模型)
*   **混合焓 ($H_{mix}$)**: Miedema模型近似 ($\sum 4 H_{ij} c_i c_j$)
*   **原子尺寸差异 ($\delta$)**: $\sqrt{\sum c_i (1 - r_i/\bar{r})^2}$
*   **价电子浓度 (VEC)**: $\sum c_i (VEC)_i$，用于初步预测 FCC/BCC 结构。

### 1.2 物理性能估算
*   **密度**: 混合法则 (Rule of Mixtures)。
*   **平均自由程 ($\lambda$)**: Exner公式，仅考虑几何分布。
*   **液相线温度 ($T_{liq}$)**: 简单的熔点加权平均 $\sum c_i T_{m,i}$。
*   **缺碳势**: 基于碳化物生成焓的线性加权。

---

## 2. 核心短板与科学改进方案 (Scientific Limitations & Advanced Models)

根据最新的专家评估，为了从“数据计算器”进化为具备物理直觉的“材料设计引擎”，需在以下三个关键模块进行深度改进。

### 2.1 热力学与相图计算模块 (Thermodynamics & Phase Stability) —— **最显著的短板**

目前通过简单的加权平均（Linear Combination/Vegard's Law）来估算属性，忽略了非线性相变。

*   **液相线温度 ($T_{liq}$) 的线性陷阱**
    *   **不足**：金属陶瓷粘结相通常是共晶体系（Eutectic Systems），实际 $T_{liq}$ 往往**远低于**加权平均值。这将误导烧结窗口的判断。
    *   **改进方案**：
        1.  引入 **共晶深度修正模型 (Deep Eutectic Correction)**：使用经验公式 $T_{liq} = \sum c_i T_{m,i} - K \cdot \Delta S_{mix}$ 进行一阶修正。
        2.  长期目标：集成 CALPHAD 接口（如 PyCalphad）进行精确计算。

*   **有害相预测 (Brittle Phases)**
    *   **不足**：HEA 粘结相在烧结冷却过程中极易析出 **$\sigma$ 相** 或 **Laves 相**，仅靠 VEC 无法准确预测。
    *   **改进方案**：
        1.  引入 **$\sigma$ 相形成判据**：结合 $\Delta H_{mix}$ 和原子半径差 $\delta$ 以及电子空穴数 ($N_v$) 建立新的判据指数。
        2.  建立“高风险过滤器”：当计算出的特征落在特定区间（如特定 VEC 范围）时，标记警报。

*   **碳窗口 (Carbon Window) 的动态计算**
    *   **不足**：目前只计算了“缺碳势”数值，未给出“游离石墨” vs “$\eta$ 相”的具体边界。
    *   **改进方案**：建立简化的 W-C-Binder 热力学平衡模型，预测能够维持两相区（Two-phase region）的临界碳含量区间。

### 2.2 界面与润湿性模块 (Interface & Wettability) —— **决定韧性的关键**

目前主要关注粘结相本体属性，忽略了“粘结相-硬质相”的交互。

*   **润湿性与粘附功 ($W_{ad}$)**
    *   **不足**：缺失直接决定烧结致密度的粘附功计算。
    *   **改进方案**：增加 **粘附功计算模块**。
        $$ W_{ad} \approx \gamma_{SV} + \gamma_{LV} - \gamma_{SL} $$
        利用经验电子理论 (EET) 或基于电负性差/生成焓差的经验公式来估算界面结合强度指数 (Wettability Index)。

*   **热膨胀系数失配 (CTE Mismatch)**
    *   **不足**：**完全缺失**。金属粘结相（高 CTE）与陶瓷相（低 CTE）冷却后的残余热应力是微裂纹的核心原因。
    *   **改进方案**：
        1.  在 `elements.json` 中补充 CTE 数据 ($\alpha$)。
        2.  计算失配度 $\Delta \alpha = |\alpha_{binder} - \alpha_{ceramic}|$，作为预测 TRS（抗弯强度）的关键特征。

### 2.3 微观结构演化模块 (Microstructure Evolution) —— **忽略了动态过程**

*   **晶粒生长抑制 (Grain Growth Inhibition)**
    *   **不足**：无法量化 VC, Cr3C2, TaC 等抑制剂对 WC 晶粒的“钉扎效应”。
    *   **改进方案**：定义 **抑制剂效能指数 (Inhibitor Potency Index)**，评估不同元素（Ti, V, Zr）在 WC 晶界的偏聚倾向。

*   **邻接度 (Contiguity)**
    *   **不足**：缺乏对 WC-WC 骨架连接比例的估算。
    *   **改进方案**：引入经验公式 $C = f(V_{binder}, \text{Dihedral Angle})$，结合粘结相体积分数和润湿角估算邻接度。

---

## 3. 数据库升级需求 (Database Requirements)

为了支持上述高级模型，数据库需进行紧急补充：

1.  **补充热膨胀系数 (CTE)**:
    *   目标文件: `core/data/elements.json`
    *   需求: 添加 `cte_micron_per_k` (μm/(m·K)) 字段。
2.  **温度相关性数据**:
    *   现状只有室温数据。需收集关键元素在 1400℃ 附近的扩散系数和表面能数据（或建立温度系数模型）。
3.  **核壳结构数据**:
    *   针对 Ti(C,N) 基体系，收集 Core-Rim 结构的固溶体属性数据。

---

## 4. 改进路线图 (Improvement Roadmap)

按优先级排序的实施计划：

1.  **[P0] 补充 CTE 数据与计算**
    *   **动作**: 更新 `elements.json`，在分析报告中增加 $\Delta \alpha$ 计算。
    *   **价值**: 低成本，高回报，直接关联热裂纹预测。

2.  **[P1] 修正液相线温度 ($T_{liq}$)**
    *   **动作**: 废弃纯线性加权，实施“共晶压低”经验修正公式。
    *   **价值**: 纠正烧结窗口的严重偏差。

3.  **[P1] 引入界面结合力指标**
    *   **动作**: 定义并计算 `Wettability_Index`。
    *   **价值**: 提升对韧性 (Fracture Toughness) 的预测能力。

4.  **[P2] 相稳定性过滤器**
    *   **动作**: 增加 $\sigma$ 相预警逻辑 (e.g., Check if $VEC \in [6.8, 8.5]$ & $\delta > 4\%$)。
    *   **价值**: 排除明显的脆性配方。
