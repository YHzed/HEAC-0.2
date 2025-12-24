"""
HEA Cermet Lab 特征定义和常量

集中管理所有模型的特征定义、默认值和系统常量。
"""

from typing import Dict, List

# ==============================================================================
# ModelX 特征定义 (硬度预测)
# ==============================================================================

MODELX_FEATURES: List[str] = [
    'Composite_MagpieData mean NUnfilled',
    'Binder_MagpieData avg_dev NdUnfilled',
    'Binder_frac d valence electrons',
    'pred_formation_energy',
    'Binder_MagpieData range Column',
    'Grain_Size_um',
    'lattice_mismatch_wc',
    'Diff_Number',
    'Binder_MagpieData minimum SpaceGroupNumber',
    'Binder_Element_Count',
    'Binder_Vol_Pct',
]

# ModelX 模型信息
MODELX_INFO = {
    'target': 'HV_kgf_mm2',
    'num_features': 11,
    'r2_score': 0.91,
    'description': 'XGBoost模型用于预测硬度(HV)',
}

# ==============================================================================
# ModelY 特征定义 (断裂韧性预测)
# ==============================================================================

MODELY_FEATURES: List[str] = [
    'pred_magnetic_moment',
    'Binder_Ni_atomic_frac',
    'Composite_MagpieData mean GSmagmom',
    'Mean_Free_Path',
    'Binder_transition metal fraction',
    'Grain_Size_um',
    'lattice_mismatch_wc',
    'Sinter_Temp_C',
    'Binder_frac d valence electrons',
    'pred_formation_energy',
    'pred_lattice_param',
    'Binder_MagpieData range MeltingT',
    'Binder_Vol_Pct',
]

# ModelY 模型信息
MODELY_INFO = {
    'target': 'KIC_MPa_m',
    'num_features': 13,
    'r2_score': 0.76,
    'description': 'XGBoost模型用于预测断裂韧性(KIC)',
}

# ==============================================================================
# Proxy 模型默认值
# ==============================================================================

PROXY_DEFAULTS: Dict[str, float] = {
    'pred_formation_energy': -0.5,   # eV/atom (典型HEA负值)
    'pred_lattice_param': 3.6,       # Å (FCC HEA典型值)
    'pred_magnetic_moment': -0.5,    # μB/atom (典型值)
}

# Proxy 模型信息
PROXY_MODEL_INFO = {
    'formation_energy': {
        'input_features': 250,
        'feature_type': 'Matminer (magpie)',
        'output_unit': 'eV/atom',
        'description': '形成能预测',
    },
    'lattice_parameter': {
        'input_features': 'variable',  # 经过裁剪
        'feature_type': 'Matminer (magpie)',
        'output_unit': 'Å',
        'description': 'FCC晶格常数预测',
        'note': '预测体积，转换为晶格常数: a = (4*V)^(1/3)',
    },
    'magnetic_moment': {
        'input_features': 250,
        'feature_type': 'Matminer (magpie)',
        'output_unit': 'μB/atom',
        'description': '磁矩预测',
    },
}

# ==============================================================================
# 元素和物理常量
# ==============================================================================

# 过渡金属列表
TRANSITION_METALS: List[str] = [
    'Ti', 'V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu',
    'Zr', 'Nb', 'Mo', 'Tc', 'Ru', 'Rh', 'Pd', 'Ag',
    'Hf', 'Ta', 'W', 'Re', 'Os', 'Ir', 'Pt', 'Au'
]

# 常见HEA元素原子序数
ATOMIC_NUMBERS: Dict[str, int] = {
    'Co': 27, 'Ni': 28, 'Fe': 26, 'Cr': 24, 'Mo': 42,
    'Nb': 41, 'W': 74, 'Ti': 22, 'V': 23, 'C': 6, 'N': 7,
    'Al': 13, 'Cu': 29, 'Mn': 25, 'Ta': 73, 'Zr': 40,
    'Hf': 72, 'Re': 75, 'Ru': 44
}

# 元素电负性 (Pauling scale)
ELECTRONEGATIVITY: Dict[str, float] = {
    'Co': 1.88, 'Ni': 1.91, 'Fe': 1.83, 'Cr': 1.66, 'Mo': 2.16,
    'Nb': 1.6, 'W': 2.36, 'Ti': 1.54, 'V': 1.63, 'C': 2.55, 'N': 3.04,
    'Al': 1.61, 'Cu': 1.90, 'Mn': 1.55, 'Ta': 1.5, 'Zr': 1.33,
    'Hf': 1.3, 'Re': 1.9, 'Ru': 2.2
}

# 陶瓷相晶格参数 (Å)
CERAMIC_LATTICE_PARAMS: Dict[str, float] = {
    'WC': 2.906,   # Hexagonal a parameter
    'TiC': 4.32,   # FCC a parameter
    'TiN': 4.24,   # FCC a parameter
    'VC': 4.16,    # FCC a parameter
    'NbC': 4.47,   # FCC a parameter
    'TaC': 4.45,   # FCC a parameter
}

# ==============================================================================
# 合理性检查范围
# ==============================================================================

# 成分约束
COMPOSITION_CONSTRAINTS = {
    'min_element_fraction': 0.001,    # 最小元素分数 (0.1%)
    'max_element_fraction': 1.0,      # 最大元素分数
    'min_total': 0.99,                # 归一化总和下限
    'max_total': 1.01,                # 归一化总和上限
    'max_elements': 10,               # 最大元素数
}

# 设计空间约束
DESIGN_SPACE_CONSTRAINTS = {
    'ceramic_vol_fraction': {
        'min': 0.0,
        'max': 0.95,
        'recommended': (0.4, 0.8),
        'unit': 'fraction',
    },
    'grain_size_um': {
        'min': 0.1,
        'max': 50.0,
        'recommended': (0.5, 5.0),
        'unit': 'μm',
    },
    'sinter_temp_c': {
        'min': 1000.0,
        'max': 1800.0,
        'recommended': (1350.0, 1550.0),
        'unit': '°C',
    },
    'sinter_time_min': {
        'min': 10.0,
        'max': 600.0,
        'recommended': (30.0, 120.0),
        'unit': 'min',
    },
}

# 预测结果合理性范围
PREDICTION_RANGES = {
    'HV': {
        'min': 500.0,
        'max': 3500.0,
        'typical': (1200.0, 2000.0),
        'unit': 'HV',
    },
    'KIC': {
        'min': 3.0,
        'max': 25.0,
        'typical': (8.0, 15.0),
        'unit': 'MPa·m½',
    },
    'pred_formation_energy': {
        'min': -3.0,
        'max': 1.0,
        'typical': (-1.0, 0.0),
        'unit': 'eV/atom',
    },
    'pred_lattice_param': {
        'min': 3.0,
        'max': 4.5,
        'typical': (3.5, 3.7),
        'unit': 'Å',
    },
    'pred_magnetic_moment': {
        'min': -5.0,
        'max': 5.0,
        'typical': (-1.0, 1.0),
        'unit': 'μB/atom',
    },
}

# ==============================================================================
# 缓存配置
# ==============================================================================

CACHE_CONFIG = {
    'matminer_cache_size': 512,       # Matminer特征缓存大小
    'feature_cache_size': 256,        # 一般特征缓存大小
    'prediction_cache_size': 128,     # 预测结果缓存大小
}

# ==============================================================================
# 日志和调试配置
# ==============================================================================

DEBUG_CONFIG = {
    'verbose_warnings': True,          # 是否显示详细警告
    'log_feature_computation': False,  # 是否记录特征计算过程
    'log_predictions': True,           # 是否记录预测结果
}

# ==============================================================================
# 帮助函数
# ==============================================================================

def get_element_property(element: str, property_name: str) -> float:
    """
    获取元素属性
    
    Args:
        element: 元素符号
        property_name: 属性名 ('atomic_number', 'electronegativity')
        
    Returns:
        属性值，如果未找到返回默认值
    """
    if property_name == 'atomic_number':
        return ATOMIC_NUMBERS.get(element, 0)
    elif property_name == 'electronegativity':
        return ELECTRONEGATIVITY.get(element, 1.5)  # 默认值
    else:
        raise ValueError(f"Unknown property: {property_name}")


def is_transition_metal(element: str) -> bool:
    """检查元素是否为过渡金属"""
    return element in TRANSITION_METALS


def validate_prediction(value: float, metric: str) -> tuple[bool, str]:
    """
    验证预测值是否在合理范围内
    
    Args:
        value: 预测值
        metric: 指标名称 ('HV', 'KIC', 等)
        
    Returns:
        (is_valid, message)
    """
    if metric not in PREDICTION_RANGES:
        return True, ""
    
    range_info = PREDICTION_RANGES[metric]
    min_val, max_val = range_info['min'], range_info['max']
    typical_min, typical_max = range_info['typical']
    
    if value < min_val or value > max_val:
        return False, (
            f"{metric}预测值{value:.2f}超出物理合理范围"
            f"[{min_val}, {max_val}] {range_info['unit']}"
        )
    
    if value < typical_min or value > typical_max:
        warning = (
            f"{metric}预测值{value:.2f}在合理范围内但不在典型范围"
            f"[{typical_min}, {typical_max}] {range_info['unit']}"
        )
        return True, warning
    
    return True, ""
