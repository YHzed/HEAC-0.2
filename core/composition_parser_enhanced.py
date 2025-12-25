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
        
        首先尝试数字在前格式，然后回退到父类方法
        """
        # 尝试数字在前格式
        result = self._parse_number_first_format(raw_string)
        if result and result.get('success'):
            return result
        
        # 回退到父类的标准解析
        return super().parse(raw_string)
    
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
        
        # 检查第二个token是否为陶瓷相
        if tokens[1] not in self.ceramic_phases:
            return None
        
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


# 创建全局实例
enhanced_parser = EnhancedCompositionParser()

# 便捷函数
def parse_composition(raw_string: str) -> Dict:
    """便捷解析函数"""
    return enhanced_parser.parse(raw_string)
