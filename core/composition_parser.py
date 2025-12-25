"""
智能成分解析器

功能：
- 解析复杂的金属陶瓷成分字符串
- 分离硬质相（陶瓷相）和粘结相（金属相）
- 归一化化学式
- 计算成分比例

支持格式：
- "WC-10CoCrFeNi"
- "80TiC-20Mo"  
- "WC 85 Co 10 Ni 5"
- "b WC 25 Co"
- "94.12 WC x Co"
"""

import re
from typing import Dict, List, Tuple, Optional
from pymatgen.core import Composition, Element
import logging

logger = logging.getLogger(__name__)


# 陶瓷相元素集合（硬质相）
CERAMIC_PHASES = {
    'WC', 'TiC', 'TiN', 'TiCN', 'TaC', 'NbC', 'VC', 
    'Cr3C2', 'Mo2C', 'W2C', 'ZrC', 'HfC', 'SiC',
    'Al2O3', 'ZrO2', 'TiO2'  # 氧化物
}

# 粘结相金属元素集合
BINDER_METALS = {
    'Co', 'Ni', 'Fe', 'Cr', 'Mn', 'Cu', 'Al', 'Ti', 'V', 
    'Mo', 'W', 'Nb', 'Ta', 'Zr', 'Hf', 'Re', 'Ru', 'Rh', 
    'Pd', 'Ir', 'Pt', 'Au', 'Ag', 'Mg', 'Zn', 'Si'
}

# 陶瓷相密度 (g/cm³)
CERAMIC_DENSITY = {
    'WC': 15.63,
    'TiC': 4.93,
    'TiN': 5.22,
    'TaC': 14.3,
    'NbC': 7.6,
    'VC': 5.77,
    'Mo2C': 9.18,
    'Cr3C2': 6.68,
    'W2C': 17.15,
    'ZrC': 6.73,
    'HfC': 12.2,
    'SiC': 3.21,
    'Al2O3': 3.95,
    'ZrO2': 5.68
}

# 陶瓷相晶格常数 (Å)
CERAMIC_LATTICE = {
    'WC': 2.906,
    'TiC': 4.328,
    'TiN': 4.242,
    'TaC': 4.456,
    'NbC': 4.470,
    'VC': 4.166
}


class CompositionParser:
    """智能成分解析器"""
    
    def __init__(self):
        """初始化解析器"""
        self.ceramic_phases = CERAMIC_PHASES
        self.binder_metals = BINDER_METALS
        
    def parse(self, raw_string: str) -> Dict:
        """
        解析成分字符串
        
        Args:
            raw_string: 原始成分字符串
            
        Returns:
            dict: {
                'binder_elements': {'Co': 0.25, 'Cr': 0.25, ...},  # 原子比
                'ceramic_elements': {'WC': 90, 'TiC': 10},  # 质量比
                'binder_wt_pct': 10.0,  # 粘结相质量百分比
                'binder_formula': 'Co1Cr1Fe1Ni1',  # 归一化化学式
                'ceramic_formula': 'WC',  # 主陶瓷相
                'secondary_phase': 'TiC',  # 第二陶瓷相（可选）
                'success': True,  # 解析是否成功
                'message': 'Parsing successful'
            }
        """
        try:
            # 清理输入
            cleaned = self._clean_string(raw_string)
            
            # 尝试不同的解析策略
            result = None
            
            # 策略1: 标准分隔符格式 "WC-10Co" 或 "WC-10CoCrFeNi"
            result = self._parse_dash_format(cleaned)
            if result and result['success']:
                return result
            
            # 策略2: 空格分隔格式 "WC 85 Co 10 Ni 5"
            result = self._parse_space_format(cleaned)
            if result and result['success']:
                return result
            
            # 策略3: "b" 前缀格式 "b WC 25 Co"
            result = self._parse_b_prefix_format(cleaned)
            if result and result['success']:
                return result
            
            # 策略4: 包含 "x" 占位符 "WC x Co"
            result = self._parse_x_placeholder_format(cleaned)
            if result and result['success']:
                return result
            
            # 如果所有策略都失败
            return {
                'success': False,
                'message': f'Unable to parse composition: {raw_string}',
                'raw_string': raw_string
            }
            
        except Exception as e:
            logger.error(f"Error parsing composition '{raw_string}': {e}")
            return {
                'success': False,
                'message': str(e),
                'raw_string': raw_string
            }
    
    def _clean_string(self, s: str) -> str:
        """清理输入字符串"""
        if not s:
            return ""
        
        # 移除多余空格
        s = ' '.join(s.split())
        
        # 标准化符号
        s = s.replace('–', '-').replace('—', '-')  # 统一连字符
        s = s.replace('，', ',')  # 中文逗号
        
        return s.strip()
    
    def _parse_dash_format(self, s: str) -> Optional[Dict]:
        """
        解析短横线格式: "WC-10CoCrFeNi", "80WC-20Co"
        """
        if '-' not in s:
            return None
        
        parts = s.split('-')
        if len(parts) != 2:
            return None
        
        ceramic_part, binder_part = parts
        
        # 解析陶瓷部分
        ceramic_match = re.match(r'(\d*\.?\d*)\s*([A-Z][a-z]?\d*[A-Z]?\d*)', ceramic_part)
        if not ceramic_match:
            return None
        
        ceramic_wt = ceramic_match.group(1)
        ceramic_formula = ceramic_match.group(2)
        
        # 解析粘结相部分
        binder_match = re.match(r'(\d*\.?\d*)\s*(.*)', binder_part)
        if not binder_match:
            return None
        
        binder_wt = binder_match.group(1)
        binder_composition = binder_match.group(2)
        
        # 处理百分比
        if ceramic_wt:
            ceramic_wt_pct = float(ceramic_wt)
        else:
            ceramic_wt_pct = None
        
        if binder_wt:
            binder_wt_pct = float(binder_wt)
        else:
            binder_wt_pct = None
        
        # 如果只有一个给出了百分比
        if ceramic_wt_pct is not None and binder_wt_pct is None:
            binder_wt_pct = 100 - ceramic_wt_pct
        elif binder_wt_pct is not None and ceramic_wt_pct is None:
            ceramic_wt_pct = 100 - binder_wt_pct
        elif ceramic_wt_pct is None and binder_wt_pct is None:
            # 默认假设
            return None
        
        # 检查是否为陶瓷相
        if ceramic_formula not in self.ceramic_phases:
            return None
        
        # 解析粘结相元素
        binder_elements = self._extract_binder_elements(binder_composition)
        if not binder_elements:
            return None
        
        # 归一化粘结相化学式
        binder_formula = self._normalize_formula(binder_elements)
        
        return {
            'binder_elements': binder_elements,
            'ceramic_elements': {ceramic_formula: ceramic_wt_pct},
            'binder_wt_pct': binder_wt_pct,
            'binder_formula': binder_formula,
            'ceramic_formula': ceramic_formula,
            'secondary_phase': None,
            'success': True,
            'message': 'Parsed dash format successfully'
        }
    
    def _parse_space_format(self, s: str) -> Optional[Dict]:
        """
        解析空格分隔格式: "WC 85 Co 10 Ni 5"
        """
        tokens = s.split()
        if len(tokens) < 3:
            return None
        
        # 尝试解析为 "元素 数字" 对
        components = {}
        i = 0
        while i < len(tokens) - 1:
            element = tokens[i]
            try:
                value = float(tokens[i + 1])
                components[element] = value
                i += 2
            except (ValueError, IndexError):
                i += 1
        
        if not components:
            return None
        
        # 分类陶瓷相和粘结相
        ceramic_elements = {}
        binder_elements = {}
        
        for element, value in components.items():
            if element in self.ceramic_phases:
                ceramic_elements[element] = value
            elif element in self.binder_metals:
                binder_elements[element] = value / 100.0  # 转换为原子比
        
        if not ceramic_elements or not binder_elements:
            return None
        
        # 计算粘结相质量百分比
        total_ceramic = sum(ceramic_elements.values())
        binder_wt_pct = 100 - total_ceramic
        
        # 主陶瓷相
        main_ceramic = max(ceramic_elements.keys(), key=ceramic_elements.get)
        
        # 归一化粘结相
        binder_formula = self._normalize_formula(binder_elements)
        
        return {
            'binder_elements': binder_elements,
            'ceramic_elements': ceramic_elements,
            'binder_wt_pct': binder_wt_pct,
            'binder_formula': binder_formula,
            'ceramic_formula': main_ceramic,
            'secondary_phase': None,
            'success': True,
            'message': 'Parsed space format successfully'
        }
    
    def _parse_b_prefix_format(self, s: str) -> Optional[Dict]:
        """
        解析 "b" 前缀格式: "b WC 25 Co"
        "b" 表示粘结相百分比
        """
        if not s.startswith('b '):
            return None
        
        # 移除 "b " 前缀
        s = s[2:].strip()
        
        # 解析剩余部分
        tokens = s.split()
        if len(tokens) < 3:
            return None
        
        # 格式应该是: "WC 25 Co" = 陶瓷相 粘结相% 粘结相成分
        ceramic_formula = tokens[0]
        try:
            binder_wt_pct = float(tokens[1])
        except ValueError:
            return None
        
        binder_composition = ' '.join(tokens[2:])
        
        # 检查陶瓷相
        if ceramic_formula not in self.ceramic_phases:
            return None
        
        # 解析粘结相
        binder_elements = self._extract_binder_elements(binder_composition)
        if not binder_elements:
            return None
        
        binder_formula = self._normalize_formula(binder_elements)
        
        return {
            'binder_elements': binder_elements,
            'ceramic_elements': {ceramic_formula: 100 - binder_wt_pct},
            'binder_wt_pct': binder_wt_pct,
            'binder_formula': binder_formula,
            'ceramic_formula': ceramic_formula,
            'secondary_phase': None,
            'success': True,
            'message': 'Parsed b-prefix format successfully'
        }
    
    def _parse_x_placeholder_format(self, s: str) -> Optional[Dict]:
        """
        解析包含 "x" 占位符的格式: "WC x Co"
        需要从外部提供体积分数
        """
        # 这种情况需要额外信息，暂时返回部分解析结果
        tokens = s.split()
        if 'x' not in tokens:
            return None
        
        # 简单实现：识别陶瓷相和粘结相
        ceramic_formula = None
        binder_composition = []
        
        for token in tokens:
            if token == 'x':
                continue
            elif token in self.ceramic_phases:
                ceramic_formula = token
            elif token in self.binder_metals:
                binder_composition.append(token)
        
        if not ceramic_formula or not binder_composition:
            return None
        
        # 假设等比例
        binder_elements = {el: 1.0 / len(binder_composition) for el in binder_composition}
        binder_formula = self._normalize_formula(binder_elements)
        
        return {
            'binder_elements': binder_elements,
            'ceramic_elements': {ceramic_formula: None},  # 未知
            'binder_wt_pct': None,  # 需要外部数据
            'binder_formula': binder_formula,
            'ceramic_formula': ceramic_formula,
            'secondary_phase': None,
            'success': True,
            'message': 'Parsed x-placeholder format (wt% missing)',
            'requires_external_data': True
        }
    
    def _extract_binder_elements(self, composition_str: str) -> Dict[str, float]:
        """
        从字符串中提取粘结相元素
        
        例如: "CoCrFeNi" -> {'Co': 0.25, 'Cr': 0.25, 'Fe': 0.25, 'Ni': 0.25}
        """
        if not composition_str:
            return {}
        
        # 尝试使用 pymatgen 解析
        try:
            comp = Composition(composition_str)
            el_dict = comp.get_el_amt_dict()
            
            # 过滤只保留金属元素
            binder_elements = {}
            for el, amt in el_dict.items():
                if el in self.binder_metals:
                    binder_elements[el] = amt
            
            # 归一化
            total = sum(binder_elements.values())
            if total > 0:
                binder_elements = {k: v / total for k, v in binder_elements.items()}
            
            return binder_elements
        
        except Exception:
            # 回退到简单的正则匹配
            pass
        
        # 简单策略：识别大写字母开头的元素符号
        pattern = r'([A-Z][a-z]?)'
        matches = re.findall(pattern, composition_str)
        
        valid_elements = [m for m in matches if m in self.binder_metals]
        
        if not valid_elements:
            return {}
        
        # 假设等比例
        return {el: 1.0 / len(valid_elements) for el in valid_elements}
    
    def _normalize_formula(self, element_dict: Dict[str, float]) -> str:
        """
        归一化化学式
        
        Args:
            element_dict: {'Co': 0.25, 'Cr': 0.25, ...}
            
        Returns:
            'Co1Cr1Fe1Ni1'
        """
        if not element_dict:
            return ""
        
        # 使用 pymatgen 归一化
        try:
            comp = Composition(element_dict)
            return comp.formula.replace(" ", "")
        except Exception:
            # 手动构建
            sorted_elements = sorted(element_dict.keys())
            formula_parts = []
            for el in sorted_elements:
                amt = element_dict[el]
                if amt > 0:
                    formula_parts.append(f"{el}{amt:.0f}" if amt == int(amt) else f"{el}{amt:.2f}")
            return ''.join(formula_parts)
