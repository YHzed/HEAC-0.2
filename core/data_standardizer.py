"""
统一数据格式标准化系统

此模块提供整个项目的数据标准化功能：
1. 列名标准化和映射
2. 成分解析和标准化
3. 数据合并（同数据不同名称的智能识别）

作者：HEAC项目组
版本：1.0
"""

import re
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
from collections import defaultdict
import warnings


class DataStandardizer:
    """
    数据标准化器：统一整个项目的数据格式
    
    核心功能：
    1. 列名标准化映射
    2. 数据类型转换
    3. 同义列名识别和合并
    """
    
    # 标准列名映射表（所有可能的同义词 -> 标准名称）
    COLUMN_MAPPING = {
        # 成分相关
        'binder_composition': ['binder_comp', 'binder', 'composition', 'comp', 'formula', 'alloy_composition'],
        'wc_content': ['wc%', 'wc_pct', 'wc_percent', 'tungsten_carbide'],
        'co_content': ['co%', 'co_pct', 'co_percent', 'cobalt'],
        'ni_content': ['ni%', 'ni_pct', 'ni_percent', 'nickel'],
        'fe_content': ['fe%', 'fe_pct', 'fe_percent', 'iron'],
        'cr_content': ['cr%', 'cr_pct', 'cr_percent', 'chromium'],
        
        # 工艺参数
        'sinter_temp': ['temperature', 'temp', 't_sinter', 'sintering_temp', 'process_temp', 'sinter_temperature'],
        'sinter_time': ['time', 'sintering_time', 't_time', 'holding_time', 'process_time'],
        'grain_size': ['grain_size_um', 'grain_size_micron', 'd_grain', 'particle_size', 'wc_grain_size'],
        'pressure': ['sintering_pressure', 'p_sinter', 'applied_pressure'],
        
        # 性能指标
        'hardness': ['hv', 'vickers_hardness', 'hardness_hv', 'hardness_value'],
        'toughness': ['fracture_toughness', 'k_ic', 'kic', 'toughness_mpa_m'],
        'trs': ['transverse_rupture_strength', 'flexural_strength', 'bend_strength'],
        'density': ['relative_density', 'bulk_density', 'rho'],
        
        # 物理特征（已计算）
        'vec': ['valence_electron_concentration', 'average_vec'],
        'delta': ['atomic_size_difference', 'size_mismatch', 'delta_pct'],
        's_mix': ['mixing_entropy', 'entropy', 's_config'],
        'h_mix': ['mixing_enthalpy', 'enthalpy', 'delta_h_mix'],
        
        # 辅助模型预测特征
        'pred_formation_energy': ['formation_energy_pred', 'ef_pred', 'pred_ef'],
        'pred_lattice_param': ['lattice_pred', 'a_pred', 'pred_lattice'],
        'lattice_mismatch_wc': ['lattice_mismatch', 'mismatch_wc', 'strain'],
        'pred_magnetic_moment': ['magmom_pred', 'magnetic_moment_pred', 'pred_magmom'],
        'pred_bulk_modulus': ['bulk_modulus_pred', 'b_pred', 'pred_b'],
        'pred_shear_modulus': ['shear_modulus_pred', 'g_pred', 'pred_g'],
        'pred_pugh_ratio': ['pugh_ratio_pred', 'b_g_ratio_pred', 'pred_pugh'],
        'pred_brittleness_index': ['brittleness_pred', 'brittleness', 'pred_brit'],
    }
    
    # 反向映射（同义词 -> 标准名）
    _REVERSE_MAPPING = None
    
    @classmethod
    def _build_reverse_mapping(cls):
        """构建反向映射表"""
        if cls._REVERSE_MAPPING is None:
            cls._REVERSE_MAPPING = {}
            for standard_name, aliases in cls.COLUMN_MAPPING.items():
                # 标准名映射到自己
                cls._REVERSE_MAPPING[standard_name] = standard_name
                # 所有别名映射到标准名
                for alias in aliases:
                    cls._REVERSE_MAPPING[alias.lower()] = standard_name
        return cls._REVERSE_MAPPING
    
    def __init__(self):
        """初始化数据标准化器"""
        self._build_reverse_mapping()
    
    def standardize_column_names(self, df: pd.DataFrame, inplace: bool = False) -> pd.DataFrame:
        """
        标准化DataFrame的列名
        
        Args:
            df: 输入DataFrame
            inplace: 是否原地修改
            
        Returns:
            标准化列名后的DataFrame
        """
        if not inplace:
            df = df.copy()
        
        # 构建当前列名到标准列名的映射
        rename_dict = {}
        for col in df.columns:
            col_lower = col.lower().strip().replace(' ', '_')
            if col_lower in self._REVERSE_MAPPING:
                standard_name = self._REVERSE_MAPPING[col_lower]
                rename_dict[col] = standard_name
        
        if rename_dict:
            df.rename(columns=rename_dict, inplace=True)
            print(f"✅ 标准化了 {len(rename_dict)} 个列名")
            for old, new in rename_dict.items():
                print(f"   {old} → {new}")
        
        return df
    
    def merge_duplicate_columns(self, df: pd.DataFrame, strategy: str = 'first') -> pd.DataFrame:
        """
        合并重复列（同数据不同名称）
        
        Args:
            df: 输入DataFrame
            strategy: 合并策略
                - 'first': 保留第一个非空值
                - 'last': 保留最后一个非空值
                - 'mean': 数值列取平均
                - 'mode': 分类列取众数
        
        Returns:
            合并后的DataFrame
        """
        # 先标准化列名
        df = self.standardize_column_names(df)
        
        # 找出重复的列名
        duplicated_cols = df.columns[df.columns.duplicated()].unique()
        
        if len(duplicated_cols) == 0:
            return df
        
        print(f"⚠️  发现 {len(duplicated_cols)} 个重复列，正在合并...")
        
        # 对每个重复列进行合并
        for col in duplicated_cols:
            # 获取所有同名列的位置索引
            col_mask = (df.columns == col)
            col_indices = [i for i, x in enumerate(col_mask) if x]
            
            # 提取这些列的数据
            dup_data = df.iloc[:, col_indices]
            
            # 根据策略合并
            if strategy == 'first':
                merged = dup_data.bfill(axis=1).iloc[:, 0]
            elif strategy == 'last':
                merged = dup_data.ffill(axis=1).iloc[:, -1]
            elif strategy == 'mean' and pd.api.types.is_numeric_dtype(dup_data.iloc[:, 0]):
                merged = dup_data.mean(axis=1)
            elif strategy == 'mode':
                merged = dup_data.mode(axis=1).iloc[:, 0]
            else:
                # 默认使用first策略
                merged = dup_data.bfill(axis=1).iloc[:, 0]
            
            # 删除所有重复列（使用列位置索引）
            cols_to_keep = [i for i in range(len(df.columns)) if i not in col_indices]
            df = df.iloc[:, cols_to_keep]
            
            # 添加合并后的列
            df[col] = merged
            
            print(f"   合并列: {col} (策略: {strategy})")
        
        return df
    
    def validate_and_convert_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        验证和转换数据类型
        
        Args:
            df: 输入DataFrame
            
        Returns:
            类型转换后的DataFrame
        """
        df = df.copy()
        
        # 定义每种标准列的预期类型
        numeric_cols = [
            'wc_content', 'co_content', 'ni_content', 'fe_content', 'cr_content',
            'sinter_temp', 'sinter_time', 'grain_size', 'pressure',
            'hardness', 'toughness', 'trs', 'density',
            'vec', 'delta', 's_mix', 'h_mix',
            'pred_formation_energy', 'pred_lattice_param', 'lattice_mismatch_wc',
            'pred_magnetic_moment', 'pred_bulk_modulus', 'pred_shear_modulus',
            'pred_pugh_ratio', 'pred_brittleness_index'
        ]
        
        string_cols = ['binder_composition']
        
        # 转换数值列
        for col in numeric_cols:
            if col in df.columns:
                try:
                    # 尝试转换为数值，将非数值转为NaN
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                except Exception as e:
                    warnings.warn(f"无法转换列 {col} 为数值类型: {e}")
        
        # 转换字符串列
        for col in string_cols:
            if col in df.columns:
                df[col] = df[col].astype(str)
        
        return df


class CompositionParser:
    """
    成分解析器：统一解析各种成分表示格式
    
    支持的格式：
    1. AlCoCrFeNi（隐式等摩尔比）
    2. Al10Co20Cr30Fe20Ni20（显式摩尔比）
    3. Al1.5Co2.0Ni1.0（小数摩尔比）
    4. Al:10 Co:20 Cr:30（带分隔符）
    5. Al 10% Co 20% Cr 30%（百分比格式）
    6. b WC 25 Co（硬质相+粘结相混合格式）
    """
    
    def __init__(self):
        """初始化成分解析器"""
        self.element_pattern = re.compile(r'([A-Z][a-z]?)(\d*\.?\d*)')
        # 硬质相关键词
        self.hard_phase_keywords = ['WC', 'TiC', 'TaC', 'NbC', 'VC', 'Cr3C2']
    
    def parse(self, composition_str: str, extract_binder_only: bool = True) -> Optional[Dict[str, float]]:
        """
        解析成分字符串
        
        Args:
            composition_str: 成分字符串
            extract_binder_only: 是否只提取粘结相（默认True，用于辅助模型）
            
        Returns:
            标准化的成分字典 {Element: atomic_fraction}，如果解析失败返回None
        """
        if pd.isna(composition_str) or not composition_str:
            return None
        
        composition_str = str(composition_str).strip()
        
        # 检查是否包含硬质相（如 "b WC 25 Co"）
        has_hard_phase = any(kw in composition_str for kw in self.hard_phase_keywords)
        
        if has_hard_phase:
            # 特殊处理硬质相+粘结相混合格式
            return self._parse_cermet_format(composition_str, extract_binder_only)
        
        # 标准格式解析
        return self._parse_standard_format(composition_str)
    
    def _parse_cermet_format(self, composition_str: str, extract_binder_only: bool = True) -> Optional[Dict[str, float]]:
        """
        解析金属陶瓷格式：硬质相 + 粘结相
        
        示例：
        - "b WC 25 Co" -> WC含量隐含（100-25=75%），Co=25%
        - "b WC 19.5 Co" -> WC=80.5%, Co=19.5%
        - "WC 85 Co 10 Ni 5" -> WC=85%, Co=10%, Ni=5%
        
        Args:
            composition_str: 成分字符串
            extract_binder_only: 如果True，只返回粘结相成分（用于辅助模型）
            
        Returns:
            成分字典
        """
        # 移除前缀标识符（如"b"）
        composition_str = re.sub(r'^[a-z]\s+', '', composition_str.strip())
        
        # 分词
        tokens = composition_str.split()
        
        composition = {}
        i = 0
        
        while i < len(tokens):
            token = tokens[i]
            
            # 检查是否是硬质相关键词
            is_hard_phase = token in self.hard_phase_keywords
            
            # 检查下一个token是否是数字
            if i + 1 < len(tokens):
                try:
                    amount = float(tokens[i + 1])
                    composition[token] = amount
                    i += 2
                    continue
                except ValueError:
                    pass
            
            # 如果没有数字，尝试解析元素符号
            match = self.element_pattern.match(token)
            if match:
                element = match.group(1)
                amount_str = match.group(2)
                amount = float(amount_str) if amount_str else 1.0
                composition[element] = amount
                i += 1
            else:
                # 硬质相但没有明确含量，跳过
                i += 1
        
        # 如果只有粘结相元素（没有含量），需要计算WC含量
        total_binder = sum(v for k, v in composition.items() if k not in self.hard_phase_keywords)
        
        if total_binder > 0 and 'WC' not in composition:
            # 粘结相含量已知，WC = 100 - 粘结相总量
            composition['WC'] = 100 - total_binder
        
        # 归一化到100%
        total = sum(composition.values())
        if total > 0:
            composition = {k: v / total * 100 for k, v in composition.items()}
        else:
            return None
        
        # 如果只需要粘结相
        if extract_binder_only:
            binder_comp = {k: v for k, v in composition.items() 
                          if k not in self.hard_phase_keywords}
            
            if not binder_comp:
                return None
            
            # 归一化粘结相到100%（原子分数）
            binder_total = sum(binder_comp.values())
            if binder_total > 0:
                binder_comp = {k: v / binder_total for k, v in binder_comp.items()}
            
            return binder_comp
        
        return composition
    
    def _parse_standard_format(self, composition_str: str) -> Optional[Dict[str, float]]:
        """
        解析标准格式成分
        
        Args:
            composition_str: 成分字符串
            
        Returns:
            成分字典
        """
        # 预处理：移除常见的分隔符和百分号
        composition_str = composition_str.replace(':', ' ')
        composition_str = composition_str.replace('%', '')
        composition_str = composition_str.replace(',', ' ')
        composition_str = composition_str.replace(';', ' ')
        
        # 尝试匹配元素和数量
        matches = self.element_pattern.findall(composition_str)
        
        if not matches:
            return None
        
        composition = {}
        total_amount = 0.0
        
        for element, amount_str in matches:
            # 如果没有指定数量，默认为1
            amount = float(amount_str) if amount_str else 1.0
            
            if element in composition:
                composition[element] += amount
            else:
                composition[element] = amount
            
            total_amount += amount
        
        # 归一化到原子分数
        if total_amount > 0:
            composition = {el: amt / total_amount for el, amt in composition.items()}
        else:
            return None
        
        return composition
    
    def to_standard_string(self, composition: Dict[str, float], decimal_places: int = 2) -> str:
        """
        将成分字典转换为标准字符串格式
        
        Args:
            composition: 成分字典
            decimal_places: 保留小数位数
            
        Returns:
            标准格式字符串，如 "Al0.20Co0.20Cr0.20Fe0.20Ni0.20"
        """
        if not composition:
            return ""
        
        # 按元素符号排序
        sorted_elements = sorted(composition.items())
        
        # 构建字符串
        parts = []
        for element, fraction in sorted_elements:
            frac_str = f"{fraction:.{decimal_places}f}".rstrip('0').rstrip('.')
            if frac_str == '1':
                parts.append(element)
            else:
                parts.append(f"{element}{frac_str}")
        
        return "".join(parts)
    
    def validate_composition(self, composition: Dict[str, float], tolerance: float = 0.01) -> bool:
        """
        验证成分是否有效
        
        Args:
            composition: 成分字典
            tolerance: 总和允许的误差范围
            
        Returns:
            是否有效
        """
        if not composition:
            return False
        
        total = sum(composition.values())
        
        # 检查总和是否接近1.0
        if abs(total - 1.0) > tolerance:
            warnings.warn(f"成分总和 {total:.4f} 不等于1.0（误差>{tolerance}）")
            return False
        
        # 检查所有值是否为正
        if any(v <= 0 for v in composition.values()):
            warnings.warn("成分包含非正值")
            return False
        
        return True


# 全局实例（单例模式）
data_standardizer = DataStandardizer()
composition_parser = CompositionParser()


def standardize_dataframe(df: pd.DataFrame, 
                         merge_duplicates: bool = True,
                         validate_types: bool = True) -> pd.DataFrame:
    """
    一键标准化DataFrame的便捷函数
    
    Args:
        df: 输入DataFrame
        merge_duplicates: 是否合并重复列
        validate_types: 是否验证和转换数据类型
        
    Returns:
        标准化后的DataFrame
    """
    print("=" * 60)
    print("开始数据标准化流程...")
    print("=" * 60)
    
    # 1. 标准化列名
    df = data_standardizer.standardize_column_names(df)
    
    # 2. 合并重复列
    if merge_duplicates:
        df = data_standardizer.merge_duplicate_columns(df)
    
    # 3. 验证和转换类型
    if validate_types:
        df = data_standardizer.validate_and_convert_types(df)
    
    print("=" * 60)
    print(f"✅ 数据标准化完成！最终形状: {df.shape}")
    print("=" * 60)
    
    return df


if __name__ == "__main__":
    # 测试代码
    print("数据标准化系统 - 测试模式")
    print("-" * 60)
    
    # 测试成分解析
    parser = CompositionParser()
    
    test_compositions = [
        "AlCoCrFeNi",
        "Al10Co20Cr30Fe20Ni20",
        "Al1.5Co2.0Ni1.0",
        "Al:10 Co:20 Cr:30 Fe:20 Ni:20",
        "Al 20% Co 20% Cr 20% Fe 20% Ni 20%"
    ]
    
    print("\n【成分解析测试】")
    for comp_str in test_compositions:
        parsed = parser.parse(comp_str)
        standard_str = parser.to_standard_string(parsed) if parsed else "解析失败"
        print(f"\n输入: {comp_str}")
        print(f"解析: {parsed}")
        print(f"标准格式: {standard_str}")
        if parsed:
            is_valid = parser.validate_composition(parsed)
            print(f"验证: {'✅ 有效' if is_valid else '❌ 无效'}")
    
    # 测试DataFrame标准化
    print("\n" + "=" * 60)
    print("【DataFrame标准化测试】")
    
    test_df = pd.DataFrame({
        'Binder_Comp': ['AlCoCrFeNi', 'CoCrNi'],
        'Temperature': [1400, 1450],
        'Hardness_HV': [1500, 1600],
        'Co%': [20, 30],
        'Grain_Size_um': [1.0, 1.5]
    })
    
    print("\n原始DataFrame:")
    print(test_df)
    
    standardized_df = standardize_dataframe(test_df)
    
    print("\n标准化后的DataFrame:")
    print(standardized_df)
    print("\n列名:", standardized_df.columns.tolist())
