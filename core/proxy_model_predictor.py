"""
Proxy Models 预测器（适配器）

用于加载已训练的 Proxy Models 并进行预测
"""

import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class ProxyModelPredictor:
    """Proxy Models 预测器"""
    
    def __init__(self, model_dir: str = 'models/proxy_models'):
        """
        初始化预测器
        
        Args:
            model_dir: 模型文件目录
        """
        self.model_dir = Path(model_dir)
        self.models = {}
        self.feature_names = None
        self._loaded = False
        
        # 尝试加载模型
        self._try_load_models()
    
    def _try_load_models(self):
        """尝试加载模型文件"""
        if not self.model_dir.exists():
            logger.warning(f"Model directory not found: {self.model_dir}")
            return False
        
        try:
            # 加载特征名称
            feature_file = self.model_dir / 'feature_names.pkl'
            if feature_file.exists():
                self.feature_names = joblib.load(feature_file)
            
            # 加载各个模型(只加载已训练的模型)
            model_files = {
                'formation_energy': 'formation_energy_model.pkl',
                'lattice': 'lattice_model.pkl',
                'magnetic_moment': 'magnetic_moment_model.pkl',
                # bulk_modulus, shear_modulus未训练,已移除
            }
            
            for model_name, filename in model_files.items():
                model_path = self.model_dir / filename
                if model_path.exists():
                    self.models[model_name] = joblib.load(model_path)
                    logger.info(f"Loaded model: {model_name}")
            
            if self.models:
                self._loaded = True
                logger.info(f"Loaded {len(self.models)} Proxy Models")
                return True
            else:
                logger.warning("No models found")
                return False
                
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            return False
    
    def predict(self, binder_formula: str) -> Dict[str, float]:
        """
        预测物理属性
        
        Args:
            binder_formula: 粘结相化学式（如 "Co1Cr1Fe1Ni1"）
            
        Returns:
            预测结果字典
        """
        if not self._loaded:
            logger.warning("Models not loaded, returning default values")
            return self._get_default_predictions()
        
        try:
            # 计算 Matminer 特征
            features = self._compute_features(binder_formula)
            
            if features is None:
                return self._get_default_predictions()
            
            # 预测
            predictions = {}
            
            if 'formation_energy' in self.models:
                pred = self.models['formation_energy'].predict(features)[0]
                predictions['formation_energy'] = float(pred)
            
            if 'lattice' in self.models:
                volume_pred = self.models['lattice'].predict(features)[0]
                # 转换 volume_per_atom 到晶格常数（假设立方）
                lattice_param = volume_pred ** (1/3)
                predictions['lattice_param'] = float(lattice_param)
            
            if 'magnetic_moment' in self.models:
                pred = self.models['magnetic_moment'].predict(features)[0]
                predictions['magnetic_moment'] = float(pred)
            
            if 'bulk_modulus' in self.models:
                pred = self.models['bulk_modulus'].predict(features)[0]
                predictions['bulk_modulus'] = float(pred)
            
            if 'shear_modulus' in self.models:
                pred = self.models['shear_modulus'].predict(features)[0]
                predictions['shear_modulus'] = float(pred)
            
            return predictions
            
        except Exception as e:
            logger.error(f"Prediction failed for {binder_formula}: {e}")
            return self._get_default_predictions()
    
    def _compute_features(self, binder_formula: str) -> Optional[np.ndarray]:
        """
        计算 Matminer 特征
        
        Args:
            binder_formula: 化学式
            
        Returns:
            特征向量
        """
        try:
            from matminer.featurizers.composition import ElementProperty
            from pymatgen.core import Composition
            
            # 创建 composition
            comp = Composition(binder_formula)
            
            # 计算特征（使用与训练相同的 preset）
            featurizer = ElementProperty.from_preset("magpie")
            feature_values = featurizer.featurize(comp)
            
            # 转换为同训练数据相同形状
            if self.feature_names is not None:
                # 匹配特征名称
                feature_dict = dict(zip(featurizer.feature_labels(), feature_values))
                features = []
                for fname in self.feature_names:
                    features.append(feature_dict.get(fname, 0.0))
                return np.array([features])
            else:
                return np.array([feature_values])
            
        except Exception as e:
            logger.error(f"Feature computation failed: {e}")
            return None
    
    def _get_default_predictions(self) -> Dict[str, float]:
        """返回默认预测值（当模型不可用时）"""
        return {
            'formation_energy': -0.5,  # eV/atom
            'lattice_param': 3.6,  # Å
            'magnetic_moment': 0.5,  # μB/atom
            'bulk_modulus': 200.0,  # GPa
            'shear_modulus': 80.0  # GPa
        }
