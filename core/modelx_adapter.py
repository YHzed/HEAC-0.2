"""
ModelX适配器

封装ModelX模型的加载和预测逻辑，处理特征准备和批量预测。
"""

import joblib
import numpy as np
import pandas as pd
from typing import Dict, List, Union, Tuple
from functools import lru_cache
from pathlib import Path

# 导入特征定义
from .feature_definitions import (
    MODELX_FEATURES,
    MODELY_FEATURES,
    CERAMIC_LATTICE_PARAMS,
    TRANSITION_METALS,
    get_element_property,
    CACHE_CONFIG
)

# Matminer imports
try:
    from matminer.featurizers.composition import ElementProperty
    from pymatgen.core import Composition
    MATMINER_AVAILABLE = True
except ImportError:
    MATMINER_AVAILABLE = False
    print("Warning: matminer not available. ModelX features will be limited.")


class ModelXAdapter:
    """
    适配器类，用于ModelX模型的特征准备和预测
    
    特征生成遵循严格的依赖链：
    Layer 1 (基础): Matminer化学特征, Binder_Vol_Pct, Grain_Size_um
    Layer 2 (Proxy): pred_lattice_param, pred_formation_energy, pred_magnetic_moment
    Layer 3 (衍生): lattice_mismatch_wc (依赖Layer 2的pred_lattice_param)
    """
    
    # 使用统一的特征定义
    EXPECTED_FEATURES = MODELX_FEATURES
    
    def __init__(self, model_path: str = 'models/ModelX.pkl'):
        """
        初始化ModelX适配器
        
        Args:
            model_path: ModelX模型文件路径
        """
        self.model_path = Path(model_path)
        self.model_dict = None
        self.model = None
        self.scaler = None
        self.feature_names = None
        
        # 初始化Matminer特征化器（使用缓存）
        if MATMINER_AVAILABLE:
            self.ep_featurizer = ElementProperty.from_preset("magpie")
        else:
            self.ep_featurizer = None
            
        self._load_model()
    
    def _load_model(self):
        """加载ModelX模型和相关组件"""
        if not self.model_path.exists():
            raise FileNotFoundError(f"ModelX model not found at {self.model_path}")
        
        try:
            self.model_dict = joblib.load(self.model_path)
            self.model = self.model_dict['model']
            self.scaler = self.model_dict['scaler']
            self.feature_names = self.model_dict['feature_names']
            
            # 验证特征名称
            if self.feature_names != self.EXPECTED_FEATURES:
                print(f"Warning: Feature names mismatch!")
                print(f"Expected: {self.EXPECTED_FEATURES}")
                print(f"Got: {self.feature_names}")
                
        except Exception as e:
            raise RuntimeError(f"Failed to load ModelX: {e}")
    
    @staticmethod
    @lru_cache(maxsize=CACHE_CONFIG['matminer_cache_size'])
    def _compute_matminer_features_cached(comp_tuple: Tuple) -> Dict[str, float]:
        """
        计算Matminer特征（缓存版）
        
        Args:
            comp_tuple: (元素, 原子分数)的元组，用于缓存
            
        Returns:
            Matminer特征字典
        """
        if not MATMINER_AVAILABLE:
            return {}
        
        # 转换回字典
        composition = dict(comp_tuple)
        
        try:
            # 创建Pymatgen Composition对象
            comp_obj = Composition(composition)
            
            # 使用Matminer特征化器
            ep_featurizer = ElementProperty.from_preset("magpie")
            features = ep_featurizer.featurize(comp_obj)
            feature_labels = ep_featurizer.feature_labels()
            
            return dict(zip(feature_labels, features))
        except Exception as e:
            print(f"Matminer featurization failed: {e}")
            return {}
    
    def compute_matminer_features(self, composition_atomic: Dict[str, float]) -> Dict[str, float]:
        """
        计算Matminer特征（使用缓存）
        
        Args:
            composition_atomic: 原子分数字典
            
        Returns:
            Matminer特征字典
        """
        # 转换为可hash的tuple用于缓存
        comp_tuple = tuple(sorted(composition_atomic.items()))
        return self._compute_matminer_features_cached(comp_tuple)
    
    def extract_modelx_features(
        self,
        composition_atomic: Dict[str, float],
        composition_wt: Dict[str, float],
        binder_vol_pct: float,
        grain_size_um: float,
        proxy_features: Dict[str, float],
        ceramic_type: str = 'WC'
    ) -> Dict[str, float]:
        """
        提取ModelX所需的18个特征
        
        严格按照依赖链计算：
        Layer 1 → Layer 2 → Layer 3
        
        Args:
            composition_atomic: 粘结相原子分数
            composition_wt: 粘结相质量分数
            binder_vol_pct: 粘结相质量百分比
            grain_size_um: 晶粒尺寸(μm)
            proxy_features: 代理模型预测特征 (Layer 2)
            ceramic_type: 陶瓷类型
            
        Returns:
            18个特征的字典
        """
        features = {}
        
        # ==== Layer 1: 基础特征 ====
        # 1. Matminer特征（使用原子分数）
        matminer_feats = self.compute_matminer_features(composition_atomic)
        
        # 2. 简单成分特征
        features['Grain_Size_um'] = grain_size_um
        features['Binder_Vol_Pct'] = binder_vol_pct
        
        # 原子分数特征
        features['Binder_Ni_atomic_frac'] = composition_atomic.get('Ni', 0.0)
        features['Binder_Nb_atomic_frac'] = composition_atomic.get('Nb', 0.0)
        features['Binder_Fe'] = composition_wt.get('Fe', 0.0)  # 注意：这里用质量分数
        
        # 3. 元素计数（阈值>0.01）
        features['Binder_Element_Count'] = sum(1 for v in composition_atomic.values() if v > 0.01)
        
        # 4. 2-norm计算
        features['Binder_2-norm'] = np.sqrt(sum(v**2 for v in composition_atomic.values()))
        
        # 5. 差异特征
        if len(composition_atomic) > 1:
            atomic_nums = [self._get_atomic_number(el) for el in composition_atomic.keys()]
            features['Diff_Number'] = max(atomic_nums) - min(atomic_nums)
            
            electroneg = [self._get_electronegativity(el) for el in composition_atomic.keys()]
            features['Diff_Electronegativity'] = max(electroneg) - min(electroneg)
        else:
            features['Diff_Number'] = 0
            features['Diff_Electronegativity'] = 0
        
        # 6. 从Matminer提取特定特征
        features['Composite_MagpieData mean GSmagmom'] = matminer_feats.get('MagpieData mean GSmagmom', 0.0)
        features['Binder_MagpieData range Column'] = matminer_feats.get('MagpieData range Column', 0.0)
        features['Binder_MagpieData mean Row'] = matminer_feats.get('MagpieData mean Row', 0.0)
        features['Binder_frac d valence electrons'] = matminer_feats.get('frac d valence electrons', 0.0)
        
        # ==== Layer 2: Proxy模型特征 ====
        features['pred_formation_energy'] = proxy_features.get('pred_formation_energy', 0.0)
        features['pred_lattice_param'] = proxy_features.get('pred_lattice_param', 0.0)
        features['pred_magnetic_moment'] = proxy_features.get('pred_magnetic_moment', 0.0)
        
        # ==== Layer 3: 衍生特征（依赖Layer 2） ====
        # lattice_mismatch_wc依赖于pred_lattice_param
        features['lattice_mismatch_wc'] = self._calculate_lattice_mismatch(
            features['pred_lattice_param'],
            ceramic_type
        )
        
        # 界面复杂度（简化计算）
        features['Interface_Complexity'] = features['Binder_Element_Count'] * features['Diff_Electronegativity']
        
        return features
    
    def extract_modely_features(
        self,
        composition_atomic: Dict[str, float],
        composition_wt: Dict[str, float],
        binder_vol_pct: float,
        grain_size_um: float,
        sinter_temp_c: float,
        proxy_features: Dict[str, float],
        ceramic_type: str = 'WC'
    ) -> Dict[str, float]:
        """
        提取ModelY所需的13个特征
        
        Args:
            composition_atomic: 粘结相原子分数
            composition_wt: 粘结相质量分数  
            binder_vol_pct: 粘结相体积百分比
            grain_size_um: 晶粒尺寸(μm)
            sinter_temp_c: 烧结温度(°C)
            proxy_features: 代理模型预测特征
            ceramic_type: 陶瓷类型
            
        Returns:
            13个特征的字典
        """
        features = {}
        
        # 1. Matminer特征
        matminer_feats = self.compute_matminer_features(composition_atomic)
        
        # 2. 从Matminer提取需要的3个特征
        features['Composite_MagpieData mean GSmagmom'] = matminer_feats.get('MagpieData mean GSmagmom', 0.0)
        features['Binder_frac d valence electrons'] = matminer_feats.get('frac d valence electrons', 0.0)
        features['Binder_MagpieData range MeltingT'] = matminer_feats.get('MagpieData range MeltingT', 0.0)
        
        # 3. 全部3个Proxy特征
        features['pred_magnetic_moment'] = proxy_features.get('pred_magnetic_moment', 0.0)
        features['pred_formation_energy'] = proxy_features.get('pred_formation_energy', 0.0)
        features['pred_lattice_param'] = proxy_features.get('pred_lattice_param', 0.0)
        
        # 4. 成分特征
        features['Binder_Ni_atomic_frac'] = composition_atomic.get('Ni', 0.0)
        
        # 5. 过渡金属比例（使用统一定义）
        tm_fraction = sum(composition_atomic.get(el, 0.0) for el in TRANSITION_METALS)
        features['Binder_transition metal fraction'] = tm_fraction
        
        # 6. 简单特征
        features['Grain_Size_um'] = grain_size_um
        features['Binder_Vol_Pct'] = binder_vol_pct
        features['Sinter_Temp_C'] = sinter_temp_c
        
        # 7. 衡生特征
        features['lattice_mismatch_wc'] = self._calculate_lattice_mismatch(
            proxy_features.get('pred_lattice_param', 3.6),
            ceramic_type
        )
        
        # 8. Mean Free Path计算
        # 简化公式: λ ≈ d * (1 - Vf) / Vf
        ceramic_vol_frac = (100 - binder_vol_pct) / 100.0
        if 0 < ceramic_vol_frac < 1.0:
            mean_free_path = grain_size_um * (1 - ceramic_vol_frac) / ceramic_vol_frac
        else:
            mean_free_path = grain_size_um * 0.5
        features['Mean_Free_Path'] = mean_free_path
        
        return features
    
    @staticmethod
    def _calculate_lattice_mismatch(pred_lattice_fcc: float, ceramic_type: str = 'WC') -> float:
        """
        计算晶格失配度
        
        Args:
            pred_lattice_fcc: 预测的FCC晶格常数(Å)
            ceramic_type: 陶瓷类型
            
        Returns:
            失配度（分数形式）
        """
        # 使用统一的陶瓷晶格参数定义
        a_ceramic = CERAMIC_LATTICE_PARAMS.get(ceramic_type, CERAMIC_LATTICE_PARAMS['WC'])
        
        # FCC最近邻距离: d_FCC = a / sqrt(2)
        d_fcc = pred_lattice_fcc / np.sqrt(2)
        
        # WC最近邻距离: d_WC = a (六方结构简化)
        d_ceramic = a_ceramic
        
        mismatch = abs(d_fcc - d_ceramic) / d_ceramic
        return mismatch
    
    @staticmethod  
    def _get_atomic_number(element: str) -> int:
        """获取元素原子序数"""
        return int(get_element_property(element, 'atomic_number'))
    
    @staticmethod
    def _get_electronegativity(element: str) -> float:
        """获取元素电负性"""
        return get_element_property(element, 'electronegativity')
    
    def prepare_features_dataframe(self, features_list: List[Dict[str, float]]) -> pd.DataFrame:
        """
        准备特征DataFrame，确保顺序和名称匹配
        
        Args:
            features_list: 特征字典列表
            
        Returns:
            按照ModelX期望顺序排列的DataFrame
        """
        df = pd.DataFrame(features_list)
        
        # 确保所有特征存在，缺失的填0
        for feat in self.EXPECTED_FEATURES:
            if feat not in df.columns:
                print(f"Warning: Missing feature {feat}, filling with 0")
                df[feat] = 0.0
        
        # 按照期望顺序选择列
        df = df[self.EXPECTED_FEATURES]
        
        # 检查NaN/Inf
        if df.isnull().any().any():
            print(f"Warning: NaN values detected in features!")
            df = df.fillna(0.0)
        
        if np.isinf(df.values).any():
            print(f"Warning: Inf values detected in features!")
            df = df.replace([np.inf, -np.inf], 0.0)
        
        return df
    
    def predict_batch(self, features_list: List[Dict[str, float]]) -> np.ndarray:
        """
        批量预测HV
        
        Args:
            features_list: 特征字典列表
            
        Returns:
            预测的HV数组
        """
        # 准备特征DataFrame
        X = self.prepare_features_dataframe(features_list)
        
        # 标准化
        X_scaled = self.scaler.transform(X)
        
        # 预测
        predictions = self.model.predict(X_scaled)
        
        return predictions
    
    def predict_single(self, features: Dict[str, float]) -> float:
        """
        单个样本预测
        
        Args:
            features: 特征字典
            
        Returns:
            预测的HV值
        """
        predictions = self.predict_batch([features])
        return float(predictions[0])


# 便捷函数用于测试
if __name__ == "__main__":
    # 测试ModelXAdapter加载
    adapter = ModelXAdapter()
    print(f"✓ ModelX loaded successfully")
    print(f"  Model type: {type(adapter.model)}")
    print(f"  Expected features: {len(adapter.EXPECTED_FEATURES)}")
    print(f"  Matminer available: {MATMINER_AVAILABLE}")
