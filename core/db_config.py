"""
金属陶瓷数据库配置模块

定义标准字段映射、单位转换规则和数据验证逻辑。
"""

from typing import Dict, List, Any, Optional

# ==============================================================================
# 标准字段映射 (标准字段名 -> 可能的别名列表)
# ==============================================================================

STANDARD_SCHEMA: Dict[str, List[str]] = {
    # ========== 身份信息 ==========
    "composition_raw": ["Composition", "comp", "成分", "组成"],
    "group_id": ["Group", "数据来源", "source", "分组"],
    "subgroup": ["Subgroup", "子组", "sub_group"],
    
    # ========== 组分信息 ==========
    "binder_vol_pct": [
        "Binder, vol-%", 
        "Binder_Vol_Pct", 
        "粘结相体积分数",
        "Binder Vol%",
        "vol%"
    ],
    "binder_wt_pct": [
        "Binder, wt-%", 
        "Binder_Wt_Pct", 
        "粘结相质量分数",
        "Binder Wt%",
        "wt%"
    ],
    "ceramic_type": [
        "Ceramic_Type", 
        "陶瓷相类型",
        "Ceramic Type",
        "ceramic"
    ],
    "binder_composition": [
        "Binder_Composition",
        "Binder Composition",
        "粘结相成分"
    ],
    
    # ========== 工艺参数 ==========
    "sinter_temp_c": [
        "T, °C",
        "Sinter_Temp_C",
        "烧结温度",
        "Temperature",
        "Temp",
        "T"
    ],
    "grain_size_um": [
        "d, mm",
        "Grain_Size_um",
        "晶粒尺寸",
        "Grain Size",
        "d"
    ],
    "sinter_method": [
        "Sintering",
        "Sintering_Method",
        "烧结方法",
        "Sinter Method"
    ],
    "load_kgf": [
        "Load, kgf",
        "Load",
        "测试载荷",
        "Test Load"
    ],
    
    # ========== 性能指标 ==========
    "hv": [
        "HV, kgf/mm2",
        "HV_kgf_mm2",
        "硬度",
        "Hardness",
        "HV"
    ],
    "kic": [
        "KIC, MPa·m1/2",
        "KIC_MPa_m",
        "断裂韧性",
        "Fracture Toughness",
        "KIC"
    ],
    "trs": [
        "TRS, MPa",
        "TRS_MPa",
        "抗弯强度",
        "Transverse Rupture Strength",
        "TRS"
    ],
}

# ==============================================================================
# 缺失值标记 (这些值会被转换为 NULL/None)
# ==============================================================================

MISSING_VALUE_INDICATORS: List[str] = [
    "-",
    "",
    "nan",
    "NaN",
    "N/A",
    "n/a",
    "NA",
    "null",
    "NULL",
    "None",
    "#N/A",
]

# ==============================================================================
# 数据清洗函数
# ==============================================================================


def clean_numeric_value(value: Any) -> Optional[float]:
    """
    清洗数值字段，处理缺失值
    
    Args:
        value: 原始值
        
    Returns:
        清洗后的数值，如果是缺失值则返回 None
    """
    if value is None:
        return None
    
    # 检查是否为缺失值标记
    if str(value).strip() in MISSING_VALUE_INDICATORS:
        return None
    
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def clean_string_value(value: Any) -> Optional[str]:
    """
    清洗字符串字段
    
    Args:
        value: 原始值
        
    Returns:
        清洗后的字符串，如果是缺失值则返回 None
    """
    if value is None:
        return None
    
    str_val = str(value).strip()
    
    # 检查是否为缺失值标记
    if str_val in MISSING_VALUE_INDICATORS:
        return None
    
    return str_val if str_val else None


# 字段特定的转换函数映射
FIELD_CONVERTERS: Dict[str, callable] = {
    "grain_size_um": clean_numeric_value,  # 直接清洗，不进行单位转换
    "hv": clean_numeric_value,
    "kic": clean_numeric_value,
    "trs": clean_numeric_value,
    "binder_vol_pct": clean_numeric_value,
    "binder_wt_pct": clean_numeric_value,
    "sinter_temp_c": clean_numeric_value,
    "load_kgf": clean_numeric_value,
    "subgroup": clean_numeric_value,
    "composition_raw": clean_string_value,
    "group_id": clean_string_value,
    "ceramic_type": clean_string_value,
    "binder_composition": clean_string_value,
    "sinter_method": clean_string_value,
}

# ==============================================================================
# HEA 粘结相判定逻辑
# ==============================================================================

def is_hea_binder(composition: Optional[str]) -> bool:
    """
    判定粘结相是否为高熵合金 (HEA)
    
    严格HEA判定规则：
    1. 粘结相包含 >= 5 种金属元素
    2. 每个元素的摩尔分数在 5-35% 范围内
    3. 常见 HEA 元素：Co, Ni, Fe, Cr, Mo, W, Ti, V, Nb, Ta, Zr, Hf, Al, Cu, Mn
    
    注意：此函数仅基于元素种类的简单判定，无法验证摩尔分数
          完整验证需要在composition_parser中进行
    
    Args:
        composition: 成分字符串，如 "WC-10Co-5Ni-3Fe"
        
    Returns:
        True 如果可能是 HEA 粘结相，否则 False
    """
    if not composition:
        return False
    
    # 常见 HEA 元素（粘结相金属元素）
    hea_elements = {
        'Co', 'Ni', 'Fe', 'Cr', 'Mo', 'W', 'Ti', 'V', 
        'Nb', 'Ta', 'Zr', 'Hf', 'Al', 'Cu', 'Mn', 'Re', 'Ru'
    }
    
    # 陶瓷相元素（不计入 HEA 判定）
    ceramic_elements = {'WC', 'TiC', 'TiN', 'TiCN', 'VC', 'NbC', 'TaC', 'Cr3C2'}
    
    comp_upper = composition.upper()
    
    # 统计包含的金属元素
    found_elements = set()
    for element in hea_elements:
        # 检查元素是否出现在成分中（区分大小写）
        if element in composition or element.upper() in comp_upper:
            found_elements.add(element)
    
    # 严格HEA定义：至少包含 5 种金属元素
    # 注：摩尔分数验证需要在parser中进行，此处仅做初步判定
    return len(found_elements) >= 5


# ==============================================================================
# 数据验证规则
# ==============================================================================

VALIDATION_RULES: Dict[str, Dict[str, Any]] = {
    "hv": {
        "min": 0,
        "max": 5000,
        "unit": "kgf/mm2",
        "description": "维氏硬度"
    },
    "kic": {
        "min": 0,
        "max": 50,
        "unit": "MPa·m^1/2",
        "description": "断裂韧性"
    },
    "trs": {
        "min": 0,
        "max": 10000,
        "unit": "MPa",
        "description": "抗弯强度"
    },
    "sinter_temp_c": {
        "min": 0,
        "max": 3000,
        "unit": "°C",
        "description": "烧结温度"
    },
    "grain_size_um": {
        "min": 0.01,
        "max": 100000,
        "unit": "μm",
        "description": "晶粒尺寸"
    },
    "binder_vol_pct": {
        "min": 0,
        "max": 100,
        "unit": "%",
        "description": "粘结相体积分数"
    },
    "binder_wt_pct": {
        "min": 0,
        "max": 100,
        "unit": "%",
        "description": "粘结相质量分数"
    },
}


def validate_field(field_name: str, value: Optional[float]) -> tuple[bool, Optional[str]]:
    """
    验证字段值是否在合理范围内
    
    Args:
        field_name: 字段名
        value: 字段值
        
    Returns:
        (is_valid, error_message)
    """
    if value is None:
        return True, None  # 允许缺失值
    
    if field_name not in VALIDATION_RULES:
        return True, None  # 无验证规则的字段直接通过
    
    rules = VALIDATION_RULES[field_name]
    
    if value < rules["min"] or value > rules["max"]:
        return False, (
            f"{rules['description']} 值 {value} 超出合理范围 "
            f"[{rules['min']}, {rules['max']}] {rules['unit']}"
        )
    
    return True, None


# ==============================================================================
# 辅助函数
# ==============================================================================

def get_standard_field_name(column_name: str) -> Optional[str]:
    """
    根据列名获取对应的标准字段名
    
    Args:
        column_name: 原始列名
        
    Returns:
        标准字段名，如果未找到则返回 None
    """
    for std_field, aliases in STANDARD_SCHEMA.items():
        if column_name in aliases:
            return std_field
    return None


def create_column_mapping(df_columns: List[str]) -> Dict[str, str]:
    """
    自动创建列映射（原始列名 -> 标准字段名）
    
    Args:
        df_columns: DataFrame 的列名列表
        
    Returns:
        映射字典 {原始列名: 标准字段名}
    """
    mapping = {}
    for col in df_columns:
        std_field = get_standard_field_name(col)
        if std_field:
            mapping[col] = std_field
    return mapping
