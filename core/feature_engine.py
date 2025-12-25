"""
特征计算引擎

功能：
- 优先级 1: 调用 Proxy Models（DFT 物理特征预测）
- 优先级 2: 物理特征计算（基于成分和 Proxy 结果）
- 优先级 3: Matminer 化学特征（可选，按需）

集成模块：
- composition_parser: 成分解析
- physics_calculator: 物理属性计算
- proxy_models: DFT 预测模型
"""

import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)


class FeatureEngine:
    """特征计算引擎"""
    
    def __init__(self):
        """初始化引擎"""
        from core.composition_parser import CompositionParser
        from core.physics_calculator import PhysicsCalculator
        
        self.parser = CompositionParser()
        self.physics_calc = PhysicsCalculator()
        
        # 延迟加载 Proxy Models（避免导入错误）
        self.proxy_models = None
        self._proxy_loaded = False
    
    def _load_proxy_models(self):
        """延迟加载 Proxy Models"""
        if self._proxy_loaded:
            return self.proxy_models is not None
        
        try:
            from core.proxy_model_predictor import ProxyModelPredictor
            self.proxy_models = ProxyModelPredictor()
            self._proxy_loaded = True
            logger.info("Proxy Models loaded successfully")
            return True
        except Exception as e:
            logger.warning(f"Failed to load Proxy Models: {e}")
            self.proxy_models = None
            self._proxy_loaded = True
            return False
    
    def calculate_features(
        self,
        binder_formula: str,
        ceramic_formula: str = 'WC',
        binder_wt_pct: Optional[float] = None,
        use_matminer: bool = False,
        **kwargs
    ) -> Dict:
        """
        计算所有特征（完整流程）
        
        Args:
            binder_formula: 粘结相化学式，如 "Co1Cr1Fe1Ni1"
            ceramic_formula: 陶瓷相化学式，默认 "WC"
            binder_wt_pct: 粘结相质量百分比（用于 vol% 计算）
            use_matminer: 是否使用 Matminer 特征（默认 False）
            **kwargs: 其他参数
            
        Returns:
            dict: {
                'proxy_features': {...},  # Proxy Model 预测结果
                'physics_features': {...},  # 物理计算特征
                'matminer_features': {...} (可选),  # Matminer 特征
                'metadata': {...}  # 元数据
            }
        """
        result = {
            'proxy_features': {},
            'physics_features': {},
            'metadata': {
                'calculated_at': datetime.now().isoformat(),
                'binder_formula': binder_formula,
                'ceramic_formula': ceramic_formula,
                'has_matminer': False
            }
        }
        
        try:
            # === 优先级 1: Proxy Models ===
            proxy_results = self.calculate_proxy_features(binder_formula)
            result['proxy_features'] = proxy_results
            
            # === 优先级 2: 物理计算 ===
            physics_results = self.calculate_physics_features(
                binder_formula=binder_formula,
                ceramic_formula=ceramic_formula,
                binder_wt_pct=binder_wt_pct,
                proxy_results=proxy_results
            )
            result['physics_features'] = physics_results
            
            # === 优先级 3: Matminer (可选) ===
            if use_matminer:
                try:
                    matminer_results = self.calculate_matminer_features(binder_formula)
                    result['matminer_features'] = matminer_results
                    result['metadata']['has_matminer'] = True
                except Exception as e:
                    logger.warning(f"Matminer calculation failed: {e}")
                    result['matminer_features'] = {}
            
            return result
            
        except Exception as e:
            logger.error(f"Error in calculate_features: {e}")
            result['metadata']['error'] = str(e)
            return result
    
    def calculate_proxy_features(self, binder_formula: str) -> Dict[str, float]:
        """
        优先级 1: 调用 5 个 Proxy Models
        
        Args:
            binder_formula: 粘结相化学式
            
        Returns:
            dict: {
                'pred_formation_energy': float,  # eV/atom
                'pred_lattice_param': float,  # Å
                'pred_magnetic_moment': float,  # μB/atom
                'pred_bulk_modulus': float,  # GPa
                'pred_shear_modulus': float  # GPa
            }
        """
        features = {
            'pred_formation_energy': None,
            'pred_lattice_param': None,
            'pred_magnetic_moment': None,
            'pred_bulk_modulus': None,
            'pred_shear_modulus': None
        }
        
        try:
            # 加载 Proxy Models
            if not self._load_proxy_models():
                logger.warning("Proxy Models not available, using default values")
                return self._get_default_proxy_features()
            
            # 调用预测
            predictions = self.proxy_models.predict(binder_formula)
            
            # 映射结果
            if predictions:
                features['pred_formation_energy'] = predictions.get('formation_energy', None)
                features['pred_lattice_param'] = predictions.get('lattice_param', None)
                features['pred_magnetic_moment'] = predictions.get('magnetic_moment', None)
                features['pred_bulk_modulus'] = predictions.get('bulk_modulus', None)
                features['pred_shear_modulus'] = predictions.get('shear_modulus', None)
            
            return features
            
        except Exception as e:
            logger.error(f"Error in Proxy Model prediction: {e}")
            return self._get_default_proxy_features()
    
    def calculate_physics_features(
        self,
        binder_formula: str,
        ceramic_formula: str,
        binder_wt_pct: Optional[float],
        proxy_results: Dict
    ) -> Dict[str, float]:
        """
        优先级 2: 物理特征计算
        
        Args:
            binder_formula: 粘结相化学式
            ceramic_formula: 陶瓷相化学式
            binder_wt_pct: 粘结相质量百分比
            proxy_results: Proxy Model 预测结果
            
        Returns:
            dict: {
                'lattice_mismatch': float,
                'vec_binder': float,
                'mean_atomic_radius': float,
                'binder_density': float,
                'binder_vol_pct': float (如果 wt_pct 提供)
            }
        """
        features = {}
        
        try:
            # 1. 晶格失配度（基于 Proxy 预测的晶格常数）
            if proxy_results.get('pred_lattice_param'):
                lattice_mismatch = self.physics_calc.lattice_mismatch(
                    binder_lattice=proxy_results['pred_lattice_param'],
                    ceramic_type=ceramic_formula,
                    structure_type='fcc'  # 假设 FCC
                )
                features['lattice_mismatch'] = lattice_mismatch
            
            # 2. VEC（价电子浓度）
            vec = self.physics_calc.calculate_vec(binder_formula)
            features['vec_binder'] = vec
            
            # 3. 平均原子半径
            mean_radius = self.physics_calc.calculate_mean_atomic_radius(binder_formula)
            features['mean_atomic_radius'] = mean_radius
            
            # 4. 粘结相密度
            density = self.physics_calc.calculate_density(binder_formula)
            features['binder_density'] = density
            
            # 5. wt% → vol% 转换（如果提供了质量百分比）
            if binder_wt_pct is not None and density is not None:
                vol_pct = self.physics_calc.wt_to_vol(
                    binder_wt_pct=binder_wt_pct,
                    binder_formula=binder_formula,
                    ceramic_formula=ceramic_formula
                )
                features['binder_vol_pct'] = vol_pct
            
            return features
            
        except Exception as e:
            logger.error(f"Error in physics feature calculation: {e}")
            return features
    
    def calculate_matminer_features(self, binder_formula: str) -> Dict[str, float]:
        """
        优先级 3: Matminer 化学特征（可选）
        
        Args:
            binder_formula: 粘结相化学式
            
        Returns:
            dict: Magpie 特征等
        """
        features = {}
        
        try:
            from matminer.featurizers.composition import ElementProperty
            from pymatgen.core import Composition
            
            # 创建 Magpie 特征器
            featurizer = ElementProperty.from_preset("magpie")
            
            # 计算特征
            comp = Composition(binder_formula)
            feature_values = featurizer.featurize(comp)
            feature_names = featurizer.feature_labels()
            
            # 构建字典
            for name, value in zip(feature_names, feature_values):
                features[f'magpie_{name.lower().replace(" ", "_")}'] = value
            
            return features
            
        except Exception as e:
            logger.warning(f"Matminer feature calculation failed: {e}")
            return {}
    
    def batch_calculate(
        self,
        formulas: List[str],
        ceramic_formulas: Optional[List[str]] = None,
        binder_wt_pcts: Optional[List[float]] = None,
        use_matminer: bool = False
    ) -> pd.DataFrame:
        """
        批量计算特征
        
        Args:
            formulas: 粘结相化学式列表
            ceramic_formulas: 陶瓷相化学式列表（可选）
            binder_wt_pcts: 粘结相质量百分比列表（可选）
            use_matminer: 是否使用 Matminer
            
        Returns:
            DataFrame: 特征矩阵
        """
        results = []
        
        # 默认值
        if ceramic_formulas is None:
            ceramic_formulas = ['WC'] * len(formulas)
        if binder_wt_pcts is None:
            binder_wt_pcts = [None] * len(formulas)
        
        # 批量计算
        for i, formula in enumerate(formulas):
            try:
                features = self.calculate_features(
                    binder_formula=formula,
                    ceramic_formula=ceramic_formulas[i],
                    binder_wt_pct=binder_wt_pcts[i],
                    use_matminer=use_matminer
                )
                
                # 展开特征
                flat_features = {
                    'binder_formula': formula,
                    **features.get('proxy_features', {}),
                    **features.get('physics_features', {}),
                    **features.get('matminer_features', {})
                }
                
                results.append(flat_features)
                
            except Exception as e:
                logger.error(f"Error processing formula {formula}: {e}")
                continue
        
        return pd.DataFrame(results)
    
    def _get_default_proxy_features(self) -> Dict[str, float]:
        """返回默认的 Proxy 特征值（当模型不可用时）"""
        return {
            'pred_formation_energy': -0.5,  # eV/atom
            'pred_lattice_param': 3.6,  # Å (典型 FCC)
            'pred_magnetic_moment': 0.5,  # μB/atom
            'pred_bulk_modulus': 200.0,  # GPa
            'pred_shear_modulus': 80.0  # GPa
        }


# 便捷函数
def calculate_features_for_composition(
    composition_str: str,
    binder_vol_pct: Optional[float] = None,
    use_matminer: bool = False
) -> Dict:
    """
    便捷函数：从原始成分字符串计算特征
    
    Args:
        composition_str: 原始成分字符串，如 "WC-10CoCrFeNi"
        binder_vol_pct: 已知的粘结相体积百分比（可选）
        use_matminer: 是否使用 Matminer
        
    Returns:
        dict: 包含所有特征
    """
    from core.composition_parser import CompositionParser
    
    # 解析成分
    parser = CompositionParser()
    parse_result = parser.parse(composition_str)
    
    if not parse_result.get('success'):
        logger.error(f"Failed to parse composition: {composition_str}")
        return {}
    
    # 计算特征
    engine = FeatureEngine()
    features = engine.calculate_features(
        binder_formula=parse_result['binder_formula'],
        ceramic_formula=parse_result['ceramic_formula'],
        binder_wt_pct=parse_result.get('binder_wt_pct'),
        use_matminer=use_matminer
    )
    
    # 添加解析结果
    features['composition_info'] = parse_result
    
    return features
