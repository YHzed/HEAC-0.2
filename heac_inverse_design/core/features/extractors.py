"""
特征提取器

统一的特征提取接口，为ModelX和ModelY生成所需的所有特征。
"""

from typing import Dict, Optional
import numpy as np
from functools import lru_cache

# 导入原有系统的feature_definitions（复用常量）
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from core.feature_definitions import TRANSITION_METALS, CERAMIC_LATTICE_PARAMS
except:
    # Fallback
    TRANSITION_METALS = ['Ti', 'V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zr', 'Nb', 'Mo', 'W']
    CERAMIC_LATTICE_PARAMS = {'WC': 2.906, 'TiC': 4.32, 'TiN': 4.24, 'VC': 4.16}

# Matminer
try:
    from matminer.featurizers.composition import ElementProperty
    from pymatgen.core import Composition
    MATMINER_AVAILABLE = True
except ImportError:
    MATMINER_AVAILABLE = False


class FeatureExtractor:
    """统一特征提取器（优化版）"""
    
    def __init__(self):
        """初始化"""
        if MATMINER_AVAILABLE:
            self.matminer_featurizer = ElementProperty.from_preset("magpie")
        else:
            self.matminer_featurizer = None
        
        # 使用缓存替代直接计算
        try:
            from ...utils import get_matminer_cache
            self.matminer_cache = get_matminer_cache()
            self.use_cache = True
        except ImportError:
            self.matminer_cache = None
            self.use_cache = False
    
    @lru_cache(maxsize=512)
    def _compute_matminer_cached(self, comp_str: str) -> Dict[str, float]:
        """计算Matminer特征（带缓存）"""
        if not MATMINER_AVAILABLE:
            return {}
        
        try:
            comp = Composition(comp_str)
            feats = self.matminer_featurizer.featurize(comp)
            feat_labels = self.matminer_featurizer.feature_labels()
            return dict(zip(feat_labels, feats))
        except:
            return {}
    
    def extract_all(self,
                    composition: Dict[str, float],
                    grain_size: float,
                    ceramic_vol_fraction: float,
                    sinter_temp: float,
                    proxy_predictions: Dict[str, float],
                    ceramic_type: str = 'WC') -> Dict[str, float]:
        """
        提取所有特征（ModelX + ModelY）
        
        Args:
            composition: 粘结相成分（原子分数）
            grain_size: 晶粒尺寸(μm)
            ceramic_vol_fraction: 陶瓷体积分数
            sinter_temp: 烧结温度(°C)
            proxy_predictions: Proxy模型预测结果
            ceramic_type: 陶瓷类型
            
        Returns:
            包含所有特征的字典
        """
        features = {}
        
        # 1. Matminer特征（使用缓存优化）
        if self.use_cache and self.matminer_cache:
            matminer_feats_dict = self.matminer_cache.get_features(composition)
            # 转换为字典格式
            if MATMINER_AVAILABLE:
                feat_labels = self.matminer_featurizer.feature_labels()
                matminer_feats_dict = dict(zip(feat_labels, matminer_feats_dict))
            else:
                matminer_feats_dict = {}
        else:
            # Fallback到原有方法
            comp_str = ''.join([f"{el}{frac}" for el, frac in composition.items()])
            matminer_feats_dict = self._compute_matminer_cached(comp_str)
        
        # 2. 提取需要的Matminer特征
        features['Composite_MagpieData mean NUnfilled'] = matminer_feats_dict.get('MagpieData mean NUnfilled', 0.0)
        features['Binder_MagpieData avg_dev NdUnfilled'] = matminer_feats_dict.get('MagpieData avg_dev NdUnfilled', 0.0)
        features['Binder_frac d valence electrons'] = matminer_feats_dict.get('frac d valence electrons', 0.0)
        features['Binder_MagpieData range Column'] = matminer_feats_dict.get('MagpieData range Column', 0.0)
        features['Binder_MagpieData minimum SpaceGroupNumber'] = matminer_feats_dict.get('MagpieData minimum SpaceGroupNumber', 0.0)
        features['Composite_MagpieData mean GSmagmom'] = matminer_feats_dict.get('MagpieData mean GSmagmom', 0.0)
        features['Binder_MagpieData range MeltingT'] = matminer_feats_dict.get('MagpieData range MeltingT', 0.0)
        
        # 3. Proxy特征
        features.update(proxy_predictions)
        
        # 4. 简单特征
        features['Grain_Size_um'] = grain_size
        binder_vol_pct = (1 - ceramic_vol_fraction) * 100
        features['Binder_Vol_Pct'] = binder_vol_pct
        features['Sinter_Temp_C'] = sinter_temp
        
        # 5. 成分特征
        features['Binder_Ni_atomic_frac'] = composition.get('Ni', 0.0)
        
        # 6. 过渡金属比例
        tm_fraction = sum(composition.get(el, 0.0) for el in TRANSITION_METALS)
        features['Binder_transition metal fraction'] = tm_fraction
        
        # 7. 衍生特征
        # lattice_mismatch
        pred_lattice = proxy_predictions.get('pred_lattice_param', 3.6)
        a_ceramic = CERAMIC_LATTICE_PARAMS.get(ceramic_type, 2.906)
        d_fcc = pred_lattice / np.sqrt(2)
        mismatch = abs(d_fcc - a_ceramic) / a_ceramic
        features['lattice_mismatch_wc'] = mismatch
        
        # Mean_Free_Path
        if 0 < ceramic_vol_fraction < 1.0:
            mean_free_path = grain_size * (1 - ceramic_vol_fraction) / ceramic_vol_fraction
        else:
            mean_free_path = grain_size * 0.5
        features['Mean_Free_Path'] = mean_free_path
        
        # Diff_Number
        if len(composition) > 1:
            atomic_nums = [self._get_atomic_number(el) for el in composition.keys()]
            features['Diff_Number'] = max(atomic_nums) - min(atomic_nums)
        else:
            features['Diff_Number'] = 0
        
        # Binder_Element_Count
        features['Binder_Element_Count'] = sum(1 for v in composition.values() if v > 0.01)
        
        return features
    
    @staticmethod
    def _get_atomic_number(element: str) -> int:
        """获取原子序数"""
        atomic_numbers = {
            'Co': 27, 'Ni': 28, 'Fe': 26, 'Cr': 24, 'Mo': 42,
            'Nb': 41, 'W': 74, 'Ti': 22, 'V': 23, 'Al': 13
        }
        return atomic_numbers.get(element, 0)
