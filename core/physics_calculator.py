"""
物理属性计算器

功能：
- wt% ↔ vol% 转换（基于密度）
- 粘结相密度计算（混合法则 + pymatgen）
- 晶格失配度计算
- 其他物理属性计算

依赖：
- pymatgen: 元素物性查询
- composition_parser: 成分数据
"""

import logging
from typing import Dict, Optional, Tuple
from pymatgen.core import Composition, Element
import numpy as np

logger = logging.getLogger(__name__)

# 陶瓷相密度数据 (g/cm³)
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
    'ZrO2': 5.68,
    'TiO2': 4.23
}

# 陶瓷相晶格常数 (Å)
CERAMIC_LATTICE = {
    'WC': 2.906,   # a轴 (六方结构，取a值)
    'TiC': 4.328,  # 立方
    'TiN': 4.242,  # 立方
    'TaC': 4.456,  # 立方
    'NbC': 4.470,  # 立方
    'VC': 4.166,   # 立方
    'Cr3C2': 5.53  # 近似立方等效
}

# 金属元素密度 (g/cm³) - 固态
METAL_DENSITY = {
    'Co': 8.90,
    'Ni': 8.91,
    'Fe': 7.87,
    'Cr': 7.19,
    'Mn': 7.21,
    'Cu': 8.96,
    'Al': 2.70,
    'Ti': 4.51,
    'V': 6.00,
    'Mo': 10.28,
    'W': 19.25,
    'Nb': 8.57,
    'Ta': 16.69,
    'Zr': 6.52,
    'Hf': 13.31,
    'Re': 21.02,
    'Ru': 12.45,
    'Rh': 12.41,
    'Pd': 12.02,
    'Ir': 22.56,
    'Pt': 21.45,
    'Au': 19.32,
    'Ag': 10.49
}


class PhysicsCalculator:
    """物理属性计算器"""
    
    def __init__(self):
        """初始化计算器"""
        self.ceramic_density = CERAMIC_DENSITY
        self.metal_density = METAL_DENSITY
        self.ceramic_lattice = CERAMIC_LATTICE
    
    def wt_to_vol(
        self, 
        binder_wt_pct: float, 
        binder_formula: str, 
        ceramic_formula: str
    ) -> Optional[float]:
        """
        质量百分比转体积百分比
        
        Args:
            binder_wt_pct: 粘结相质量百分比 (0-100)
            binder_formula: 粘结相化学式 (如 "Co1Cr1Fe1Ni1")
            ceramic_formula: 陶瓷相化学式 (如 "WC")
            
        Returns:
            粘结相体积百分比 (0-100)，失败返回 None
            
        原理：
            Vol_b / (Vol_b + Vol_c) = ?
            其中 Vol_b = Wt_b / ρ_b, Vol_c = Wt_c / ρ_c
            Wt_b + Wt_c = 100
        """
        try:
            # 计算粘结相密度
            binder_density = self.calculate_density(binder_formula)
            if binder_density is None or binder_density <= 0:
                logger.warning(f"Invalid binder density for {binder_formula}")
                return None
            
            # 获取陶瓷相密度
            ceramic_density = self.ceramic_density.get(ceramic_formula, None)
            if ceramic_density is None:
                logger.warning(f"Unknown ceramic density for {ceramic_formula}, using default 15.0")
                ceramic_density = 15.0  # 默认值（接近 WC）
            
            # 质量百分比
            wt_b = binder_wt_pct
            wt_c = 100 - binder_wt_pct
            
            if wt_b <= 0 or wt_c < 0:
                return None
            
            # 体积计算
            vol_b = wt_b / binder_density
            vol_c = wt_c / ceramic_density
            
            # 体积百分比
            vol_b_pct = vol_b / (vol_b + vol_c) * 100
            
            return vol_b_pct
            
        except Exception as e:
            logger.error(f"Error in wt_to_vol conversion: {e}")
            return None
    
    def vol_to_wt(
        self, 
        binder_vol_pct: float, 
        binder_formula: str, 
        ceramic_formula: str
    ) -> Optional[float]:
        """
        体积百分比转质量百分比
        
        Args:
            binder_vol_pct: 粘结相体积百分比 (0-100)
            binder_formula: 粘结相化学式
            ceramic_formula: 陶瓷相化学式
            
        Returns:
            粘结相质量百分比 (0-100)
            
        推导：
            设 Vol_b = v, Vol_c = (1-v) [归一化]
            Wt_b / ρ_b = v
            Wt_c / ρ_c = (1-v)
            Wt_b + Wt_c = 1
            
            解得: Wt_b = v*ρ_b / (v*ρ_b + (1-v)*ρ_c)
        """
        try:
            binder_density = self.calculate_density(binder_formula)
            if binder_density is None or binder_density <= 0:
                return None
            
            ceramic_density = self.ceramic_density.get(ceramic_formula, 15.0)
            
            v_frac = binder_vol_pct / 100.0  # 归一化到 0-1
            
            if v_frac <= 0 or v_frac >= 1:
                return None
            
            # 质量分数计算
            wt_b_frac = (v_frac * binder_density) / \
                        (v_frac * binder_density + (1 - v_frac) * ceramic_density)
            
            wt_b_pct = wt_b_frac * 100
            
            return wt_b_pct
            
        except Exception as e:
            logger.error(f"Error in vol_to_wt conversion: {e}")
            return None
    
    def calculate_density(self, formula: str) -> Optional[float]:
        """
        计算粘结相密度（混合法则）
        
        Args:
            formula: 化学式，如 "Co1Cr1Fe1Ni1" 或 "Co0.25Cr0.25Fe0.25Ni0.25"
            
        Returns:
            密度 (g/cm³)
            
        方法：
            1. 优先使用 pymatgen 获取原子权重
            2. 使用质量加权平均密度
        """
        try:
            # 使用 pymatgen 解析化学式
            comp = Composition(formula)
            el_amt_dict = comp.get_el_amt_dict()
            
            # 计算摩尔质量和密度
            total_mass = 0.0
            total_volume = 0.0
            
            for el, amt in el_amt_dict.items():
                el_str = str(el)
                
                # 获取原子质量
                try:
                    element = Element(el_str)
                    atomic_mass = element.atomic_mass  # amu (g/mol)
                except:
                    logger.warning(f"Cannot get atomic mass for {el_str}")
                    continue
                
                # 获取密度
                density = self.metal_density.get(el_str, None)
                
                # 如果字典中没有，尝试从 pymatgen 获取
                if density is None:
                    try:
                        density = element.density_of_solid
                    except:
                        logger.warning(f"Cannot get density for {el_str}")
                        density = 8.0  # 默认金属密度
                
                # 计算质量和体积
                mass = amt * atomic_mass
                volume = mass / density if density > 0 else 0
                
                total_mass += mass
                total_volume += volume
            
            # 总体密度
            if total_volume > 0:
                density = total_mass / total_volume
                return density
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error calculating density for {formula}: {e}")
            
            # 回退到简单平均
            try:
                elements = self._extract_elements(formula)
                if elements:
                    densities = [self.metal_density.get(el, 8.0) for el in elements]
                    return np.mean(densities)
            except:
                pass
            
            return None
    
    def lattice_mismatch(
        self, 
        binder_lattice: float, 
        ceramic_type: str,
        structure_type: str = 'fcc'
    ) -> Optional[float]:
        """
        计算晶格失配度
        
        Args:
            binder_lattice: 粘结相晶格常数 (Å)，通常来自 Proxy Model 预测
            ceramic_type: 陶瓷相类型，如 "WC"
            structure_type: 粘结相结构类型 ('fcc' 或 'bcc')
            
        Returns:
            晶格失配度（无量纲），定义为相对差异
            
        原理：
            对于 FCC 结构，最近邻距离 d_nn = a / √2
            对于 BCC 结构，最近邻距离 d_nn = a * √3 / 2
            
            失配度 δ = |d_nn_binder - a_ceramic| / a_ceramic
        """
        try:
            # 获取陶瓷相晶格常数
            ceramic_lattice = self.ceramic_lattice.get(ceramic_type, None)
            if ceramic_lattice is None:
                logger.warning(f"Unknown ceramic lattice for {ceramic_type}")
                return None
            
            # 计算粘结相最近邻距离
            if structure_type.lower() == 'fcc':
                d_nn_binder = binder_lattice / np.sqrt(2)
            elif structure_type.lower() == 'bcc':
                d_nn_binder = binder_lattice * np.sqrt(3) / 2
            else:
                logger.warning(f"Unknown structure type: {structure_type}, assuming FCC")
                d_nn_binder = binder_lattice / np.sqrt(2)
            
            # 计算失配度
            mismatch = abs(d_nn_binder - ceramic_lattice) / ceramic_lattice
            
            return mismatch
            
        except Exception as e:
            logger.error(f"Error calculating lattice mismatch: {e}")
            return None
    
    def calculate_vec(self, formula: str) -> Optional[float]:
        """
        计算价电子浓度 (Valence Electron Concentration)
        
        Args:
            formula: 化学式
            
        Returns:
            VEC 值
        """
        try:
            # 元素价电子数字典
            vec_dict = {
                'Co': 9, 'Ni': 10, 'Fe': 8, 'Cr': 6, 'Mn': 7, 'Cu': 11,
                'Al': 3, 'Ti': 4, 'V': 5, 'Mo': 6, 'W': 6,
                'Nb': 5, 'Ta': 5, 'Zr': 4, 'Hf': 4,
                'Re': 7, 'Ru': 8, 'Rh': 9, 'Pd': 10,
                'Ir': 9, 'Pt': 10, 'Au': 11, 'Ag': 11
            }
            
            comp = Composition(formula)
            el_frac_dict = comp.get_el_amt_dict()
            
            # 归一化原子分数
            total = sum(el_frac_dict.values())
            el_frac_dict = {k: v / total for k, v in el_frac_dict.items()}
            
            # 计算 VEC
            vec = 0.0
            for el, frac in el_frac_dict.items():
                el_str = str(el)
                vec += frac * vec_dict.get(el_str, 0)
            
            return vec
            
        except Exception as e:
            logger.error(f"Error calculating VEC: {e}")
            return None
    
    def calculate_mean_atomic_radius(self, formula: str) -> Optional[float]:
        """
        计算平均原子半径
        
        Args:
            formula: 化学式
            
        Returns:
            平均原子半径 (Å)
        """
        try:
            comp = Composition(formula)
            el_frac_dict = comp.get_el_amt_dict()
            
            # 归一化
            total = sum(el_frac_dict.values())
            el_frac_dict = {k: v / total for k, v in el_frac_dict.items()}
            
            # 计算平均半径
            mean_radius = 0.0
            for el, frac in el_frac_dict.items():
                try:
                    element = Element(str(el))
                    radius = element.atomic_radius  # pm
                    if radius is not None:
                        mean_radius += frac * radius
                except:
                    logger.warning(f"Cannot get atomic radius for {el}")
            
            return mean_radius
            
        except Exception as e:
            logger.error(f"Error calculating mean atomic radius: {e}")
            return None
    
    def _extract_elements(self, formula: str) -> list:
        """简单提取元素符号（回退方法）"""
        import re
        pattern = r'([A-Z][a-z]?)'
        return re.findall(pattern, formula)
    
    def calculate_composite_properties(
        self, 
        binder_modulus: float,
        ceramic_modulus: float,
        binder_vol_pct: float,
        method: str = 'voigt'
    ) -> Dict[str, float]:
        """
        计算复合材料属性（混合法则）
        
        Args:
            binder_modulus: 粘结相模量 (GPa)
            ceramic_modulus: 陶瓷相模量 (GPa)
            binder_vol_pct: 粘结相体积百分比 (0-100)
            method: 'voigt' (上限) 或 'reuss' (下限) 或 'hs' (Hashin-Shtrikman)
            
        Returns:
            {'effective_modulus': float}
        """
        try:
            v_b = binder_vol_pct / 100.0
            v_c = 1 - v_b
            
            if method == 'voigt':
                # 上限估计（等应变）
                E_eff = v_b * binder_modulus + v_c * ceramic_modulus
            elif method == 'reuss':
                # 下限估计（等应力）
                E_eff = 1 / (v_b / binder_modulus + v_c / ceramic_modulus)
            elif method == 'hs':
                # Hashin-Shtrikman 上界（简化）
                E_eff = (v_b * binder_modulus + v_c * ceramic_modulus) / 2
            else:
                E_eff = v_b * binder_modulus + v_c * ceramic_modulus
            
            return {'effective_modulus': E_eff}
            
        except Exception as e:
            logger.error(f"Error calculating composite properties: {e}")
            return {}
