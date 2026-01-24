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

    def _clean_string(self, s: str) -> str:
        """Enhanced cleaning to handle commas"""
        s = super()._clean_string(s)
        return s.replace(',', ' ').replace(';', ' ')

    def _parse_number_first_format(self, s: str) -> Optional[Dict]:
        """
        解析数字在前的格式 (支持由逗号或空格分隔的复杂字符串)
        
        逻辑:
        1. 寻找第一个数字 (Ceramic %)
        2. 寻找随后的数字 (Binder %)
        3. 检查两者之和是否接近 100
        """
        # 清理输入
        s = self._clean_string(s)
        tokens = s.split()
        
        if len(tokens) < 3:
            return None
        
        try:
            # 1. 第一个数字 (Ceramic %)
            ceramic_pct = float(tokens[0])
            
            # 2. 扫描寻找匹配的 Binder %
            binder_pct = None
            split_index = -1
            
            for i in range(1, len(tokens)):
                try:
                    val = float(tokens[i])
                    # 检查是否互补 (允许 0.5% 误差)
                    if abs(ceramic_pct + val - 100.0) <= 0.5:
                        binder_pct = val
                        split_index = i
                        break
                except ValueError:
                    continue
            
            if binder_pct is None:
                return None
                
            # 3. 分割部分
            # Ceramic Part: tokens[1 : split_index]
            # Binder Part: tokens[split_index+1 :] (Binder composition usually follows binder %)
            
            ceramic_tokens = tokens[1:split_index]
            binder_comp_tokens = tokens[split_index+1:]
            
            # 如果 binder_comp_tokens 为空，可能粘结相就在 binder_pct 本身 (e.g. "90 WC 10 Co") -> "Co" might be attached or implied?
            # 这里的 tokens[split_index] 是 "10.0". 
            # 实际上输入可能是 "10.0 Co" -> split "10.0", "Co".
            # 或者 "Co10.0" -> split "Co10.0". 
            # 如果 tokens[split_index] 是 "10.0"，那么 binder composition 应该在后面
            
            binder_str = " ".join(binder_comp_tokens)
            
            # 解析陶瓷相 (寻找其中的主要陶瓷相)
            found_ceramics = [t for t in ceramic_tokens if t in self.ceramic_phases]
            if not found_ceramics:
                # 尝试看 ceramic_tokens 是否包含其他信息，或者回退到默认
                # 比如 "90.0 WC," -> "WC"
                pass
            
            ceramic_formula = found_ceramics[0] if found_ceramics else (ceramic_tokens[0] if ceramic_tokens else "WC")
            
            # 解析粘结相
            # 如果 binder_str 为空，检查 binder token 本身是否包含成分 (如 "Co10.0") -- 不，因为 float parse 成功意味着它是纯数字
            # 但也许它原本是 "Co10.0" 但被清洗了? 不，clean_string 不会拆分 "Co10.0" 为 "10.0".
            # 除非 "10.0" 单独存在。
            # 如果 binder_str 为空，我们可能在前面的 ceramic_tokens 里有误判?
            # 或者是 "90 WC, 10 Co"。 tokens: 90, WC, 10, Co. split_index=2. binder_comp=Co. OK.
            
            # Case: "90 WC, Mo2C 10.0 Co10.0" -> tokens: 90.0, WC, Mo2C, 10.0, Co10.0
            # split_index pointing to 10.0.
            # binder_comp = "Co10.0".
            
            binder_elements = self._extract_binder_elements(binder_str)
            if not binder_elements:
                return None
            
            binder_formula = self._normalize_formula(binder_elements)
            
            # 严格HEA验证：>= 5个元素且每个元素摩尔分数在5-35%
            is_hea = False
            if len(binder_elements) >= 5:
                # 检查每个元素的摩尔分数
                all_in_range = all(0.05 <= frac <= 0.35 for frac in binder_elements.values())
                is_hea = all_in_range
            
            return {
                'binder_elements': binder_elements,
                'ceramic_elements': {ceramic_formula: ceramic_pct},
                'binder_wt_pct': binder_pct,
                'binder_formula': binder_formula,
                'ceramic_formula': ceramic_formula,
                'secondary_phase': ceramic_tokens[1] if len(ceramic_tokens) > 1 else None,
                'success': True,
                'message': 'Parsed number-first format (flexible)',
                'is_hea': is_hea
            }
            
        except (ValueError, IndexError):
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
                
                # 严格HEA验证：>= 5个元素且每个元素摩尔分数在5-35%
                is_hea = False
                if len(normalized_binder) >= 5:
                    # 检查每个元素的摩尔分数
                    all_in_range = all(0.05 <= frac <= 0.35 for frac in normalized_binder.values())
                    is_hea = all_in_range
                
                return {
                    'binder_elements': normalized_binder,
                    'ceramic_elements': {},
                    'binder_wt_pct': 100.0,
                    'binder_formula': binder_formula,
                    'ceramic_formula': None, # 表示无陶瓷相
                    'secondary_phase': None,
                    'success': True,
                    'message': 'Parsed as Pure Alloy/HEA',
                    'is_hea': is_hea
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
