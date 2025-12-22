#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HEA.xlsx 数据处理脚本

功能：
1. 解析成分字符串，分离硬质相和粘结相
2. 将质量分数转换为原子比
3. 提取粘结相成分公式
4. 清洗和标准化数据
5. 添加派生特征

作者: HEAC 0.2 项目组
日期: 2025-12-19
"""

import pandas as pd
import numpy as np
import re
import sys
import os
from pathlib import Path
from pymatgen.core import Composition

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.data_standardizer import CompositionParser


class HEADataProcessor:
    """HEA 数据处理器"""
    
    def __init__(self):
        """初始化处理器"""
        self.parser = CompositionParser()
        
        # 硬质相关键词（扩展列表）
        self.hard_phases = [
            'WC', 'TiCN', 'TiC', 'TiN', 'TaC', 'NbC', 'VC', 'Mo2C', 'Cr3C2',
            'ZrC', 'HfC', 'MoC', 'ZrO2', 'Al2O3', 'SiC', 'B4C', 'TiB2'
        ]
        
        # 金属元素列表
        self.metal_elements = [
            'Co', 'Ni', 'Fe', 'Cr', 'Mo', 'W', 'Ti', 'Al', 'Nb', 'Ta', 
            'Re', 'Mn', 'Cu', 'V', 'Zr', 'Hf'
        ]
    
    def parse_composition_advanced(self, comp_str, binder_vol_pct=None):
        """
        高级成分解析，支持混合格式
        
        Args:
            comp_str: 成分字符串，如 "b WC 25 Co" 或 "b WC x Co"
            binder_vol_pct: 粘结相体积分数（可选），用于处理 x 占位符
            
        Returns:
            dict: {
                'binder_elements': {'Co': 25.0, ...},  # 质量%
                'ceramic_elements': {'WC': 75.0, ...},  # 质量%
                'binder_wt_pct': 25.0,  # 粘结相总质量%
                'binder_formula': 'Co',  # 粘结相化学式（用于 Matminer）
                'binder_atomic_formula': 'Co1',  # 粘结相原子比公式
            }
        """
        if pd.isna(comp_str) or not comp_str:
            return None
        
        comp_str = str(comp_str).strip()
        
        # 去除 'b ' 前缀
        if comp_str.lower().startswith('b '):
            comp_str = comp_str[2:].strip()
        
        # 检测是否包含 x 占位符
        has_x_placeholder = 'x' in comp_str.lower() or 'X' in comp_str
        
        # 如果有 x 占位符，特殊处理
        if has_x_placeholder:
            # 检查是否为 "数字 WC x Co" 格式（硬质相质量已知）
            if re.match(r'^\d+', comp_str):
                return self._parse_ceramic_known_format(comp_str)
            # 否则使用原有逻辑（粘结相未知）
            return self._parse_composition_with_x(comp_str, binder_vol_pct)
        
        # 按空格分割
        tokens = comp_str.split()
        
        parsed_items = {}
        i = 0
        
        # 改用"数字优先"的解析策略
        # "WC 25 Co" 应该解析为 WC(隐含), 25 Co
        # 即：如果遇到数字，它和后面的化学式配对
        #     如果遇到化学式且后面不是数字，则该化学式隐含数量
        
        while i < len(tokens):
            token = tokens[i]
            
            # 尝试解析为数字
            try:
                val = float(token)
                # 这是一个数字，下一个token应该是化学式
                if i + 1 < len(tokens):
                    chem = tokens[i + 1]
                    # 清理化学式
                    chem_clean = re.sub(r'[^a-zA-Z0-9]', '', chem)
                    if chem_clean in parsed_items:
                        parsed_items[chem_clean] += val
                    else:
                        parsed_items[chem_clean] = val
                    i += 2
                else:
                    # 孤立的数字，跳过
                    i += 1
            except ValueError:
                # 这是化学式
                chem = token
                chem_clean = re.sub(r'[^a-zA-Z0-9]', '', chem)
                
                # 检查下一个token是否为数字
                # 如果是，说明这个化学式没有明确数量（隐含）
                # 如果不是，说明格式可能是 "化学式 数字"（不常见）
                if i + 1 < len(tokens):
                    try:
                        # 尝试把下一个当数字
                        next_val = float(tokens[i + 1])
                        # 下一个确实是数字，说明当前化学式是隐含数量的
                        # 使用默认值1
                        if chem_clean in parsed_items:
                            parsed_items[chem_clean] += 1.0
                        else:
                            parsed_items[chem_clean] = 1.0
                        i += 1  # 只前进1，让数字在下一轮处理
                    except ValueError:
                        # 下一个不是数字，可能是另一个化学式
                        # 当前化学式使用默认值
                        if chem_clean in parsed_items:
                            parsed_items[chem_clean] += 1.0
                        else:
                            parsed_items[chem_clean] = 1.0
                        i += 1
                else:
                    # 最后一个token且是化学式，使用默认值
                    if chem_clean in parsed_items:
                        parsed_items[chem_clean] += 1.0
                    else:
                        parsed_items[chem_clean] = 1.0
                    i += 1
        
        # 分类：粘结相 vs 硬质相
        binder_elements = {}
        ceramic_elements = {}
        
        for chem, amount in parsed_items.items():
            chem_clean = re.sub(r'[^a-zA-Z0-9]', '', chem)
            
            # 判断是否为硬质相
            is_ceramic = False
            
            # 1. 直接匹配硬质相列表
            if any(hp.lower() == chem_clean.lower() for hp in self.hard_phases):
                is_ceramic = True
            # 2. 含 C/N/O 且不是纯金属
            elif ('C' in chem_clean or 'N' in chem_clean or 'O' in chem_clean) and len(chem_clean) > 2:
                if chem_clean not in self.metal_elements:
                    is_ceramic = True
            
            if is_ceramic:
                ceramic_elements[chem_clean] = amount
            else:
                binder_elements[chem_clean] = amount
        
        # 检查是否为金属陶瓷格式（有硬质相且只有简单数值）
        # 例如 "WC 25 Co" -> WC有默认值1，这是错误的
        # 正确理解：Co=25%，WC=75%
        has_ceramic = len(ceramic_elements) > 0
        has_binder = len(binder_elements) > 0
        
        if has_ceramic and has_binder:
            # 过滤掉值为0的陶瓷相（避免"WC 12 Co 0 NbC"被误判）
            ceramic_elements_nonzero = {k: v for k, v in ceramic_elements.items() if v > 0}
            
            # 检查是否为金属陶瓷格式
            # 格式1: 只有一个非零硬质相且值为1  (如 "WC 25 Co")
            # 格式2: 有一个主硬质相(值=1)和小量添加剂 (如 "WC 10 Co 0.2 Mo2C")
            is_cermet_format = False
            
            if len(ceramic_elements_nonzero) >= 1:
                # 检查是否有一个值为1的主硬质相
                main_ceramics = [k for k, v in ceramic_elements_nonzero.items() if v == 1.0]
                
                if len(main_ceramics) >= 1:
                    # 有主硬质相，检查其他硬质相是否都是小量添加剂（<5）
                    other_ceramics = {k: v for k, v in ceramic_elements_nonzero.items() if v != 1.0}
                    total_additives = sum(other_ceramics.values())
                    
                    # 如果添加剂总量很小（<5），视为金属陶瓷格式
                    if total_additives < 5.0:
                        is_cermet_format = True
            
            if is_cermet_format:
                # 这是金属陶瓷格式："WC 25 Co" 
                # 粘结相数值就是质量百分比
                binder_wt_pct = sum(binder_elements.values())
                
                # 验证粘结相百分比合理性
                if binder_wt_pct > 0 and binder_wt_pct < 100:
                    # 硬质相占剩余部分（按原始比例分配）
                    ceramic_wt_pct = 100 - binder_wt_pct
                    total_ceramic_ratio = sum(ceramic_elements_nonzero.values())
                    # 按比例分配硬质相质量
                    ceramic_elements = {k: (v / total_ceramic_ratio) * ceramic_wt_pct 
                                        for k, v in ceramic_elements_nonzero.items()}
                else:
                    # 不合理，按标准格式处理
                    total_wt = sum(binder_elements.values()) + sum(ceramic_elements_nonzero.values())
                    if total_wt == 0:
                        return None
                    binder_wt_pct = (sum(binder_elements.values()) / total_wt) * 100
            else:
                # 检查是否为特殊格式："WC 10 VC 9.6 Co 0.4 Ru"
                # 所有明确的数字都是质量%，值为1的元素占剩余部分
                total_explicit = sum(v for v in binder_elements.values()) + sum(v for v in ceramic_elements.values() if v != 1.0)
                elements_with_one = {k: v for k, v in ceramic_elements.items() if v == 1.0}
                
                # 如果：1)总和<100  2)有值为1的元素  3)总和大于10（避免误判金属陶瓷格式）
                if total_explicit < 100 and total_explicit > 10 and len(elements_with_one) > 0:
                    # 这是特殊格式：所有数字都是质量%
                    # 值为1的元素占剩余部分
                    remaining = 100 - total_explicit
                    
                    # 总粘结相质量%
                    binder_wt_pct = sum(binder_elements.values())
                    
                    # 更新值为1的元素
                    for k in elements_with_one.keys():
                        ceramic_elements[k] = remaining / len(elements_with_one)
                else:
                    # 标准格式："WC 85 Co 10 Ni 5"（所有成分都有明确数值）
                    total_wt = sum(binder_elements.values()) + sum(ceramic_elements.values())
                    
                    if total_wt == 0:
                        return None
                    
                    binder_wt_pct = (sum(binder_elements.values()) / total_wt) * 100
        elif has_binder and not has_ceramic:
            # 纯粘结相（无硬质相）
            binder_wt_pct = 100.0
        else:
            # 纯硬质相或其他异常情况
            return None
        
        # 如果粘结相为空，尝试补救
        if not binder_elements:
            # 对于纯 WC 或其他硬质相，使用默认粘结相
            binder_elements = {'Co': 0.1}
            binder_wt_pct = 0.1
        
        # 生成粘结相公式（质量分数格式）
        binder_formula_wt = ''.join([f"{el}{amt}" for el, amt in sorted(binder_elements.items())])
        
        # 将质量分数转换为原子比
        binder_atomic_comp = self._weight_to_atomic(binder_elements)
        binder_atomic_formula = self._format_atomic_formula(binder_atomic_comp)
        
        return {
            'binder_elements': binder_elements,
            'ceramic_elements': ceramic_elements,
            'binder_wt_pct': binder_wt_pct,
            'binder_formula': binder_formula_wt,
            'binder_atomic_formula': binder_atomic_formula,
            'binder_atomic_comp': binder_atomic_comp,
            'has_unknown': False
        }
    
    def _parse_ceramic_known_format(self, comp_str):
        """
        处理硬质相质量已知的格式: "94.12 WC x Co"
        
        Args:
            comp_str: 如 "94.12 WC x Co" (硬质相94.12%, 粘结相=100-94.12)
            
        Returns:
            dict: 成分信息，如果无法处理返回None
        """
        # 提取开头的数字（硬质相质量%）
        match = re.match(r'^([\d.]+)\s+(.+)', comp_str)
        if not match:
            return None
        
        ceramic_wt_pct = float(match.group(1))
        remaining_str = match.group(2)
        
        # 提取硬质相和粘结相类型
        tokens = remaining_str.replace('x', '').replace('X', '').split()
        ceramic_type = None
        binder_type = None
        
        for token in tokens:
            token_clean = re.sub(r'[^a-zA-Z0-9]', '', token)
            if not token_clean:
                continue
                
            if any(hp.lower() == token_clean.lower() for hp in self.hard_phases):
                ceramic_type = token_clean
            elif token_clean in self.metal_elements:
                binder_type = token_clean
        
        if not binder_type or not ceramic_type:
            return None
        
        # 粘结相质量 = 100 - 硬质相质量
        binder_wt_pct = 100 - ceramic_wt_pct
        
        if binder_wt_pct <= 0 or binder_wt_pct >= 100:
            return None
        
        # 构建结果
        binder_elements = {binder_type: binder_wt_pct}
        ceramic_elements = {ceramic_type: ceramic_wt_pct}
        
        # 转换为原子比
        binder_atomic_comp = self._weight_to_atomic(binder_elements)
        binder_atomic_formula = self._format_atomic_formula(binder_atomic_comp)
        
        return {
            'binder_elements': binder_elements,
            'ceramic_elements': ceramic_elements,
            'binder_wt_pct': binder_wt_pct,
            'binder_formula': f'{binder_type}{binder_wt_pct:.2f}',
            'binder_atomic_formula': binder_atomic_formula,
            'binder_atomic_comp': binder_atomic_comp,
            'has_unknown': False
        }
    
    def _parse_composition_with_x(self, comp_str, binder_vol_pct=None):
        """
        处理包含 x 占位符的成分字符串
        
        Args:
            comp_str: 如 "WC x Co" (x 表示未知的粘结相含量)
            binder_vol_pct: 粘结相体积分数（如果有）
            
        Returns:
            dict: 成分信息，如果无法处理返回None
        """
        # 提取硬质相和粘结相类型
        # 例如 "WC x Co" -> ceramic: WC, binder: Co
        tokens = comp_str.replace('x', '').replace('X', '').split()
        
        ceramic_type = None
        binder_type = None
        
        for token in tokens:
            token_clean = re.sub(r'[^a-zA-Z0-9]', '', token)
            if not token_clean:
                continue
                
            # 判断是硬质相还是粘结相
            if any(hp.lower() == token_clean.lower() for hp in self.hard_phases):
                ceramic_type = token_clean
            elif token_clean in self.metal_elements:
                binder_type = token_clean
        
        # 如果没有找到粘结相或硬质相，无法处理
        if not binder_type or not ceramic_type:
            return None
        
        # 尝试从体积分数推算质量分数
        if binder_vol_pct is not None and pd.notna(binder_vol_pct):
            try:
                vol_pct = float(binder_vol_pct)
                if vol_pct > 0 and vol_pct < 100:
                    # 使用体积分数转质量分数
                    # 这需要密度信息，这里使用简化估算
                    # WC密度约15.6 g/cm³，Co密度约8.9 g/cm³
                    binder_wt_pct = self._vol_to_weight_approx(
                        binder_type, ceramic_type, vol_pct
                    )
                else:
                    # 无效的体积分数
                    return None
            except:
                return None
        else:
            # 没有体积分数信息，标记为未知
            return {
                'binder_elements': {binder_type: np.nan},
                'ceramic_elements': {ceramic_type: np.nan},
                'binder_wt_pct': np.nan,
                'binder_formula': binder_type,
                'binder_atomic_formula': f'{binder_type}1',
                'binder_atomic_comp': {binder_type: 1.0},
                'has_unknown': True
            }
        
        # 有体积分数，可以计算
        binder_elements = {binder_type: binder_wt_pct}
        ceramic_elements = {ceramic_type: 100 - binder_wt_pct}
        
        # 转换为原子比
        binder_atomic_comp = self._weight_to_atomic(binder_elements)
        binder_atomic_formula = self._format_atomic_formula(binder_atomic_comp)
        
        return {
            'binder_elements': binder_elements,
            'ceramic_elements': ceramic_elements,
            'binder_wt_pct': binder_wt_pct,
            'binder_formula': binder_type + str(binder_wt_pct),
            'binder_atomic_formula': binder_atomic_formula,
            'binder_atomic_comp': binder_atomic_comp,
            'has_unknown': False
        }
    
    def _vol_to_weight_approx(self, binder_elem, ceramic_type, vol_pct):
        """
        体积分数转质量分数（简化估算）
        
        Args:
            binder_elem: 粘结相元素
            ceramic_type: 硬质相类型
            vol_pct: 粘结相体积分数
            
        Returns:
            float: 粘结相质量分数
        """
        # 典型密度值 (g/cm³)
        densities = {
            'WC': 15.6,
            'TiC': 4.93,
            'TiCN': 5.2,
            'TiN': 5.4,
            'Co': 8.9,
            'Ni': 8.9,
            'Fe': 7.87,
            'Cr': 7.19,
        }
        
        # 获取密度，如果没有使用默认值
        rho_binder = densities.get(binder_elem, 8.5)  # 默认金属密度
        rho_ceramic = densities.get(ceramic_type, 15.0)  # 默认硬质相密度
        
        # 体积分数 -> 质量分数
        # Vb / (Vb + Vc) = vol_pct / 100
        # Wb / (Wb + Wc) = ?
        # 其中 Wb = mb, Wc = mc, Vb = mb/ρb, Vc = mc/ρc
        
        # 设总质量为100g，粘结相质量为 x，硬质相质量为 (100-x)
        # x / ρb / (x/ρb + (100-x)/ρc) = vol_pct / 100
        # 求解 x
        
        v_frac = vol_pct / 100.0
        # x / ρb = v_frac * (x/ρb + (100-x)/ρc)
        # x / ρb = v_frac * x / ρb + v_frac * (100-x) / ρc
        # x / ρb - v_frac * x / ρb = v_frac * (100-x) / ρc
        # x * (1 - v_frac) / ρb = v_frac * (100-x) / ρc
        # x * (1 - v_frac) * ρc = v_frac * (100-x) * ρb
        # x * [(1-v_frac)*ρc] = v_frac * 100 * ρb - v_frac * x * ρb
        # x * [(1-v_frac)*ρc + v_frac*ρb] = v_frac * 100 * ρb
        # x = v_frac * 100 * ρb / [(1-v_frac)*ρc + v_frac*ρb]
        
        denominator = (1 - v_frac) * rho_ceramic + v_frac * rho_binder
        if denominator == 0:
            return np.nan
        
        binder_wt_pct = (v_frac * 100 * rho_binder) / denominator
        
        return binder_wt_pct
    
    def _weight_to_atomic(self, weight_dict):
        """
        将质量分数转换为原子分数
        
        Args:
            weight_dict: {'Co': 80, 'Ni': 20}  # 质量%
            
        Returns:
            dict: {'Co': 0.xx, 'Ni': 0.xx}  # 原子分数
        """
        try:
            # 使用 pymatgen 进行转换
            formula_str = ''.join([f"{el}{wt}" for el, wt in weight_dict.items()])
            comp = Composition(formula_str)
            
            # 获取原子分数
            total_atoms = sum(comp.get_el_amt_dict().values())
            atomic_comp = {str(el): amt / total_atoms 
                          for el, amt in comp.get_el_amt_dict().items()}
            
            return atomic_comp
        except:
            # 简化近似：假设摩尔质量相似
            total = sum(weight_dict.values())
            return {el: wt / total for el, wt in weight_dict.items()}
    
    def _format_atomic_formula(self, atomic_comp, decimal_places=2):
        """
        格式化原子比公式
        
        Args:
            atomic_comp: {'Co': 0.8, 'Ni': 0.2}
            decimal_places: 小数位数
            
        Returns:
            str: 'Co0.8Ni0.2'
        """
        parts = []
        for el, frac in sorted(atomic_comp.items()):
            frac_str = f"{frac:.{decimal_places}f}".rstrip('0').rstrip('.')
            if frac_str == '1' or frac_str == '':
                frac_str = '1'
            parts.append(f"{el}{frac_str}")
        
        return ''.join(parts)
    
    def process_dataframe(self, df):
        """
        处理整个 DataFrame
        
        Args:
            df: 原始 DataFrame
            
        Returns:
            DataFrame: 处理后的 DataFrame
        """
        processed_rows = []
        
        for idx, row in df.iterrows():
            # 获取粘结相体积分数
            binder_vol_raw = row.get('Binder, vol-%', '')
            binder_vol_pct = None
            if pd.notna(binder_vol_raw) and str(binder_vol_raw).strip() != '-':
                try:
                    binder_vol_pct = float(binder_vol_raw)
                except:
                    binder_vol_pct = None
            
            # 解析成分（传递体积分数信息）
            comp_info = self.parse_composition_advanced(
                row.get('Composition', ''),
                binder_vol_pct=binder_vol_pct
            )
            
            if not comp_info:
                continue
            
            # 处理硬度值
            try:
                hv = float(str(row.get('HV, kgf/mm2', '')).replace(',', '').strip())
            except:
                hv = np.nan
            
            # 处理断裂韧性
            try:
                kic = float(str(row.get('KIC, MPa·m1/2', '')).replace(',', '').strip())
            except:
                kic = np.nan
            
            # 处理抗弯强度
            try:
                trs_val = row.get('TRS, MPa', '')
                if pd.notna(trs_val) and str(trs_val).strip() != '-':
                    trs = float(str(trs_val).replace(',', '').strip())
                else:
                    trs = np.nan
            except:
                trs = np.nan
            
            # 处理温度
            try:
                temp_val = row.get('T, °C', '')
                if pd.notna(temp_val) and str(temp_val).strip() != '-':
                    temp = float(temp_val)
                else:
                    temp = np.nan
            except:
                temp = np.nan
            
            # 处理晶粒尺寸 (假设为 μm)
            try:
                grain_size = float(row.get('d, mm', 1.0))
            except:
                grain_size = np.nan
            
            # 处理粘结相体积分数
            try:
                binder_vol = float(row.get('Binder, vol-%', 0))
            except:
                binder_vol = np.nan
            
            # 构建新行
            new_row = {
                # 原始信息
                'Group': row.get('Group', ''),
                'Subgroup': row.get('Subgroup', ''),
                'Original_Composition': row.get('Composition', ''),
                
                # 粘结相信息
                'Binder_Composition': comp_info['binder_formula'],
                'Binder_Atomic_Formula': comp_info['binder_atomic_formula'],
                'Binder_Wt_Pct': comp_info['binder_wt_pct'],
                'Binder_Vol_Pct': binder_vol,
                
                # 硬质相信息
                'Ceramic_Type': ', '.join(comp_info['ceramic_elements'].keys()),
                'Ceramic_Wt_Pct': 100 - comp_info['binder_wt_pct'],
                
                # 工艺参数
                'Sinter_Temp_C': temp,
                'Grain_Size_um': grain_size,
                'Load_kgf': row.get('Load, kgf', ''),
                'Sintering_Method': row.get('Sintering', ''),
                
                # 性能参数
                'HV_kgf_mm2': hv,
                'KIC_MPa_m': kic,
                'TRS_MPa': trs,
            }
            
            # 添加原子比详细信息（用于特征工程）
            for el, frac in comp_info['binder_atomic_comp'].items():
                new_row[f'Binder_{el}_atomic_frac'] = frac
            
            processed_rows.append(new_row)
        
        return pd.DataFrame(processed_rows)
    
    def add_derived_features(self, df):
        """
        添加派生特征
        
        Args:
            df: 处理后的 DataFrame
            
        Returns:
            DataFrame: 添加特征后的 DataFrame
        """
        df = df.copy()
        
        # 1. 粘结相类型分类
        def classify_binder_type(comp):
            if pd.isna(comp):
                return 'Unknown'
            comp = str(comp).upper()
            if 'NI' in comp and 'CO' in comp:
                return 'Co-Ni'
            elif 'CO' in comp:
                return 'Co-based'
            elif 'NI' in comp:
                return 'Ni-based'
            elif 'FE' in comp:
                return 'Fe-based'
            else:
                return 'Other'
        
        df['Binder_Type'] = df['Binder_Composition'].apply(classify_binder_type)
        
        # 2. 硬质相类型分类
        def classify_ceramic_type(ceramic):
            if pd.isna(ceramic):
                return 'Unknown'
            ceramic = str(ceramic).upper()
            if 'WC' in ceramic:
                return 'WC-based'
            elif 'TIC' in ceramic or 'TICN' in ceramic or 'TIN' in ceramic:
                return 'Ti-carbide/nitride'
            else:
                return 'Other'
        
        df['Ceramic_Type_Class'] = df['Ceramic_Type'].apply(classify_ceramic_type)
        
        # 3. 成分复杂度（粘结相元素数量）
        def count_elements(formula):
            if pd.isna(formula):
                return 0
            # 简单统计大写字母数量
            return len(re.findall(r'[A-Z][a-z]?', str(formula)))
        
        df['Binder_Element_Count'] = df['Binder_Atomic_Formula'].apply(count_elements)
        
        # 4. 硬度等级分类
        def classify_hardness(hv):
            if pd.isna(hv):
                return 'Unknown'
            if hv < 800:
                return 'Low'
            elif hv < 1200:
                return 'Medium'
            elif hv < 1600:
                return 'High'
            else:
                return 'Very High'
        
        df['Hardness_Grade'] = df['HV_kgf_mm2'].apply(classify_hardness)
        
        # 5. 韧性等级分类
        def classify_toughness(kic):
            if pd.isna(kic):
                return 'Unknown'
            if kic < 10:
                return 'Low'
            elif kic < 15:
                return 'Medium'
            elif kic < 20:
                return 'High'
            else:
                return 'Very High'
        
        df['Toughness_Grade'] = df['KIC_MPa_m'].apply(classify_toughness)
        
        return df


def main():
    """主函数"""
    print("=" * 80)
    print("HEA.xlsx 数据处理脚本")
    print("=" * 80)
    
    # 文件路径
    input_file = Path("Training data/HEA.xlsx")
    timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    output_file = Path(f"Training data/HEA_processed_{timestamp}.csv")
    report_file = Path(f"Training data/HEA_processing_report_{timestamp}.txt")
    
    # 检查输入文件
    if not input_file.exists():
        print(f"❌ 错误：找不到文件 {input_file}")
        return
    
    print(f"\n📂 读取文件: {input_file}")
    
    # 读取数据
    try:
        df_original = pd.read_excel(input_file)
        print(f"✅ 成功读取 {len(df_original)} 行数据")
        print(f"\n列名: {df_original.columns.tolist()}")
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return
    
    # 初始化处理器
    print("\n🔧 初始化数据处理器...")
    processor = HEADataProcessor()
    
    # 处理数据
    print("\n⚙️  处理数据中...")
    df_processed = processor.process_dataframe(df_original)
    print(f"✅ 成功处理 {len(df_processed)} 行数据")
    
    # 添加派生特征
    print("\n🎯 添加派生特征...")
    df_final = processor.add_derived_features(df_processed)
    print(f"✅ 特征列数: {len(df_final.columns)}")
    
    # 保存结果
    print(f"\n💾 保存处理后的数据到: {output_file}")
    df_final.to_csv(output_file, index=False, encoding='utf-8-sig')
    print("✅ 数据保存成功")
    
    # 生成报告
    print(f"\n📊 生成处理报告: {report_file}")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("HEA.xlsx 数据处理报告\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"处理时间: {pd.Timestamp.now()}\n\n")
        
        f.write("数据统计:\n")
        f.write(f"  原始数据行数: {len(df_original)}\n")
        f.write(f"  处理后行数: {len(df_processed)}\n")
        f.write(f"  数据保留率: {len(df_processed)/len(df_original)*100:.1f}%\n\n")
        
        f.write("列信息:\n")
        f.write(f"  总列数: {len(df_final.columns)}\n")
        f.write(f"  列名: {', '.join(df_final.columns)}\n\n")
        
        f.write("粘结相类型分布:\n")
        f.write(df_final['Binder_Type'].value_counts().to_string() + "\n\n")
        
        f.write("硬质相类型分布:\n")
        f.write(df_final['Ceramic_Type_Class'].value_counts().to_string() + "\n\n")
        
        f.write("硬度等级分布:\n")
        f.write(df_final['Hardness_Grade'].value_counts().to_string() + "\n\n")
        
        f.write("韧性等级分布:\n")
        f.write(df_final['Toughness_Grade'].value_counts().to_string() + "\n\n")
        
        f.write("数据质量评估:\n")
        f.write(f"  缺失值统计:\n")
        missing_stats = df_final.isnull().sum()
        for col, count in missing_stats[missing_stats > 0].items():
            f.write(f"    {col}: {count} ({count/len(df_final)*100:.1f}%)\n")
    
    print("✅ 报告生成成功")
    
    # 显示预览
    print("\n" + "=" * 80)
    print("处理结果预览（前5行）:")
    print("=" * 80)
    
    preview_cols = [
        'Original_Composition', 'Binder_Atomic_Formula', 'Binder_Wt_Pct',
        'HV_kgf_mm2', 'KIC_MPa_m', 'Binder_Type'
    ]
    available_cols = [col for col in preview_cols if col in df_final.columns]
    print(df_final[available_cols].head().to_string())
    
    print("\n" + "=" * 80)
    print("✅ 处理完成！")
    print("=" * 80)
    print(f"\n输出文件:")
    print(f"  1. 数据文件: {output_file.absolute()}")
    print(f"  2. 报告文件: {report_file.absolute()}")
    print("\n提示: 您可以使用处理后的数据进行机器学习建模和特征工程。")


if __name__ == "__main__":
    main()
