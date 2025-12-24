"""
输入验证模块

提供DesignSpace和成分输入的验证功能。
"""

from typing import Dict, Tuple
from dataclasses import dataclass
from .feature_definitions import (
    COMPOSITION_CONSTRAINTS,
    DESIGN_SPACE_CONSTRAINTS,
    ATOMIC_NUMBERS
)


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    errors: list[str]
    warnings: list[str]


def validate_composition(composition: Dict[str, float]) -> ValidationResult:
    """
    验证成分输入
    
    Args:
        composition: 元素→分数字典
        
    Returns:
        ValidationResult
    """
    errors = []
    warnings = []
    
    # 检查是否为空
    if not composition:
        errors.append("成分不能为空")
        return ValidationResult(False, errors, warnings)
    
    # 检查元素数量
    if len(composition) > COMPOSITION_CONSTRAINTS['max_elements']:
        errors.append(
            f"元素数量({len(composition)})超过最大限制"
            f"({COMPOSITION_CONSTRAINTS['max_elements']})"
        )
    
    # 检查元素是否合法
    for element in composition.keys():
        if element not in ATOMIC_NUMBERS:
            warnings.append(f"未知元素: {element}，可能影响预测准确性")
    
    # 检查分数范围
    for element, fraction in composition.items():
        if fraction < 0:
            errors.append(f"{element}的分数不能为负: {fraction}")
        if fraction > COMPOSITION_CONSTRAINTS['max_element_fraction']:
            errors.append(
                f"{element}的分数({fraction})超过最大值"
                f"({COMPOSITION_CONSTRAINTS['max_element_fraction']})"
            )
        if fraction < COMPOSITION_CONSTRAINTS['min_element_fraction']:
            warnings.append(
                f"{element}的分数({fraction})非常小，可能可以忽略"
            )
    
    # 检查归一化
    total = sum(composition.values())
    min_total = COMPOSITION_CONSTRAINTS['min_total']
    max_total = COMPOSITION_CONSTRAINTS['max_total']
    
    if total < min_total or total > max_total:
        errors.append(
            f"成分总和({total:.4f})不在合理范围[{min_total}, {max_total}]内，"
            "请确保成分已归一化"
        )
    
    is_valid = len(errors) == 0
    return ValidationResult(is_valid, errors, warnings)


def validate_design_space(design: 'DesignSpace') -> ValidationResult:
    """
    验证设计空间参数
    
    Args:
        design: DesignSpace对象
        
    Returns:
        ValidationResult
    """
    errors = []
    warnings = []
    
    # 验证成分
    comp_result = validate_composition(design.hea_composition)
    errors.extend(comp_result.errors)
    warnings.extend(comp_result.warnings)
    
    # 验证陶瓷体积分数
    ceramic_constraints = DESIGN_SPACE_CONSTRAINTS['ceramic_vol_fraction']
    if not (ceramic_constraints['min'] <= design.ceramic_vol_fraction <= ceramic_constraints['max']):
        errors.append(
            f"陶瓷体积分数({design.ceramic_vol_fraction})超出范围"
            f"[{ceramic_constraints['min']}, {ceramic_constraints['max']}]"
        )
    
    rec_min, rec_max = ceramic_constraints['recommended']
    if not (rec_min <= design.ceramic_vol_fraction <= rec_max):
        warnings.append(
            f"陶瓷体积分数({design.ceramic_vol_fraction})不在推荐范围"
            f"[{rec_min}, {rec_max}]内，可能影响性能"
        )
    
    # 验证晶粒尺寸
    grain_constraints = DESIGN_SPACE_CONSTRAINTS['grain_size_um']
    if not (grain_constraints['min'] <= design.grain_size_um <= grain_constraints['max']):
        errors.append(
            f"晶粒尺寸({design.grain_size_um}μm)超出范围"
            f"[{grain_constraints['min']}, {grain_constraints['max']}]"
        )
    
    rec_min, rec_max = grain_constraints['recommended']
    if not (rec_min <= design.grain_size_um <= rec_max):
        warnings.append(
            f"晶粒尺寸({design.grain_size_um}μm)不在推荐范围[{rec_min}, {rec_max}]内"
        )
    
    # 验证烧结温度
    temp_constraints = DESIGN_SPACE_CONSTRAINTS['sinter_temp_c']
    if not (temp_constraints['min'] <= design.sinter_temp_c <= temp_constraints['max']):
        errors.append(
            f"烧结温度({design.sinter_temp_c}°C)超出范围"
            f"[{temp_constraints['min']}, {temp_constraints['max']}]"
        )
    
    # 验证烧结时间
    time_constraints = DESIGN_SPACE_CONSTRAINTS['sinter_time_min']
    if not (time_constraints['min'] <= design.sinter_time_min <= time_constraints['max']):
        errors.append(
            f"烧结时间({design.sinter_time_min}min)超出范围"
            f"[{time_constraints['min']}, {time_constraints['max']}]"
        )
    
    # 验证陶瓷类型
    from .feature_definitions import CERAMIC_LATTICE_PARAMS
    if design.ceramic_type not in CERAMIC_LATTICE_PARAMS:
        warnings.append(
            f"未知陶瓷类型: {design.ceramic_type}，将使用WC的晶格参数"
        )
    
    is_valid = len(errors) == 0
    return ValidationResult(is_valid, errors, warnings)
