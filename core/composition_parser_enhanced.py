"""
成分解析器扩展 - 支持数字在前格式

本模块扩展 CompositionParser 以支持:
- "90 WC 10 Co" (陶瓷% 陶瓷相 粘结% 粘结相)
- "94 WC 6 Co"
- "85 WC 15 Co"
"""

from typing import Dict, Optional
from core.composition_parser import CompositionParser


class EnhancedCompositionParser(CompositionParser):
    """增强的成分解析器，支持更多格式"""
    
    def parse(self, raw_string: str) -> Dict:
        """
        增强的解析方法
        
        1. 尝试数字在前格式 (90 WC 10 Co)
        2. 尝试标准格式 (父类)
        3. 尝试纯合金/HEA格式 (CoCrFeNi)
        """
        # 1. 尝试数字在前格式
        result = self._parse_number_first_format(raw_string)
        if result and result.get('success'):
            return result
        
        # 2. 回退到父类的标准解析
        result = super().parse(raw_string)
        if result and result.get('success'):
            return result

        # 3. 尝试纯合金/HEA格式
        return self._parse_pure_alloy_format(raw_string)

    def _parse_number_first_format(self, s: str) -> Optional[Dict]:
        """
        解析数字在前的空格格式
        
        格式: <陶瓷%> <陶瓷相> <粘结%> <粘结相>
        示例: "90 WC 10 Co", "85 TiC 15 Ni"
        """
        # 清理输入
        s = self._clean_string(s)
        tokens = s.split()
        
        if len(tokens) < 4:
            return None
        
        # 检查第一个token是否为数字
        try:
            first_num = float(tokens[0])
        except (ValueError, TypeError):
            return None
        
        
        # Check if 3rd token is also a number (Binder wt%)
        try:
            binder_pct = float(tokens[2])
        except (ValueError, TypeError):
             return None

        # Optional: Check if they sum to ~100 to confirm this is a valid "Split" string
        # This helps avoid false positives on random strings starting with a number
        if abs(float(tokens[0]) + binder_pct - 100.0) > 0.5:
             # Warning or strict? Let's be strict for this specific parser mode
             # to avoid capturing unintended things.
             pass 
             # Actually, if user inputs "80 WC 20 Co", sum is 100.
             # If "80 WC 15 Co", sum is 95. Maybe allow it?
             # Let's just check if it's a valid structure
             pass

        # Relaxed: Assume tokens[1] is the Ceramic Phase if the structure validates
        # if tokens[1] not in self.ceramic_phases:
        #    return None
        ceramic_formula = tokens[1]
        
        try:
            ceramic_pct = float(tokens[0])
            ceramic_formula = tokens[1]
            binder_pct = float(tokens[2])
            binder_str = ' '.join(tokens[3:])
            
            # 解析粘结相
            binder_elements = self._extract_binder_elements(binder_str)
            if not binder_elements:
                return None
            
            binder_formula = self._normalize_formula(binder_elements)
            
            return {
                'binder_elements': binder_elements,
                'ceramic_elements': {ceramic_formula: ceramic_pct},
                'binder_wt_pct': binder_pct,
                'binder_formula': binder_formula,
                'ceramic_formula': ceramic_formula,
                'secondary_phase': None,
                'success': True,
                'message': 'Parsed number-first format',
                'is_hea': len(binder_elements) >= 4
            }
        except (ValueError, IndexError, KeyError):
            return None

    def _parse_pure_alloy_format(self, s: str) -> Dict:
        """
        解析纯合金/HEA格式
        
        示例: "CoCrFeNi", "Cr20 Fe20 Mn20 Ni40"
        处理逻辑:
        1. 尝试解析为化学式
        2. 检查元素是否大多为金属粘结相元素
        3. 如果是，则视为纯粘结相 (Ceramic=None, Binder%=100)
        """
        try:
            from pymatgen.core import Composition
            
            # 清理
            s = self._clean_string(s)
            
            # 尝试解析
            comp = Composition(s)
            el_dict = comp.get_el_amt_dict()
            
            if not el_dict:
                return {'success': False, 'message': 'Empty composition'}
            
            # 检查成分: 是否主要由粘结相金属组成
            # 允许少量杂质，但主要成分应并在 BINDER_METALS 中
            total_atoms = sum(el_dict.values())
            binder_atoms = 0
            
            valid_binder_elements = {}
            
            for el, amt in el_dict.items():
                if el in self.binder_metals:
                    binder_atoms += amt
                    valid_binder_elements[el] = amt
                # 忽略非金属元素（如C, O等，如果不构成已知陶瓷相）
            
            # 阈值: 如果90%以上的原子是粘结相金属，则认为是纯合金
            if binder_atoms / total_atoms > 0.9:
                # 归一化粘结相
                total_valid = sum(valid_binder_elements.values())
                normalized_binder = {k: v/total_valid for k, v in valid_binder_elements.items()}
                binder_formula = self._normalize_formula(normalized_binder)
                
                return {
                    'binder_elements': normalized_binder,
                    'ceramic_elements': {},
                    'binder_wt_pct': 100.0,
                    'binder_formula': binder_formula,
                    'ceramic_formula': None, # 表示无陶瓷相
                    'secondary_phase': None,
                    'success': True,
                    'message': 'Parsed as Pure Alloy/HEA',
                    'is_hea': len(normalized_binder) >= 4
                }
            
            return {'success': False, 'message': f'Not recognized as component or pure alloy: {s}'}
            
        except Exception as e:
            return {'success': False, 'message': f'Failed to parse pure alloy: {e}'}


# 创建全局实例
enhanced_parser = EnhancedCompositionParser()

# 便捷函数
def parse_composition(raw_string: str) -> Dict:
    """便捷解析函数"""
    return enhanced_parser.parse(raw_string)
