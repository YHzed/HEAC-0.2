"""
Proxy Models - 代理模型集合

封装3个proxy模型：形成能、晶格参数、磁矩。
"""

from typing import Dict, Optional
import joblib
import numpy as np
from pathlib import Path


class ProxyModelEnsemble:
    """Proxy模型集合"""
    
    # 默认值（当预测失败时使用）
    DEFAULT_VALUES = {
        'pred_formation_energy': -0.5,  # eV/atom
        'pred_lattice_param': 3.6,      # Å
        'pred_magnetic_moment': -0.5,   # μB/atom
    }
    
    def __init__(self, model_dir: str = 'models/proxy_models'):
        """
        初始化Proxy模型集合
        
        Args:
            model_dir: Proxy模型目录
        """
        self.model_dir = Path(model_dir)
        
        # 加载3个模型
        self.formation_energy_model = self._load_model('formation_energy_model.pkl')
        self.lattice_model = self._load_model('lattice_model.pkl')
        self.magnetic_moment_model = self._load_model('magnetic_moment_model.pkl')
        
        # 加载特征名称
        feature_names_path = self.model_dir / 'feature_names.pkl'
        if feature_names_path.exists():
            self.feature_names = joblib.load(feature_names_path)
        else:
            self.feature_names = None
    
    def _load_model(self, filename: str):
        """加载单个模型"""
        model_path = self.model_dir / filename
        if model_path.exists():
            return joblib.load(model_path)
        else:
            return None
    
    def predict_formation_energy(self, matminer_features: np.ndarray) -> Optional[float]:
        """预测形成能"""
        if self.formation_energy_model is None:
            return None
        
        try:
            prediction = self.formation_energy_model.predict(matminer_features.reshape(1, -1))
            return float(prediction[0])
        except Exception as e:
            print(f"Formation energy prediction failed: {e}")
            return None
    
    def predict_lattice_parameter(self, matminer_features: np.ndarray) -> Optional[float]:
        """预测晶格参数"""
        if self.lattice_model is None:
            return None
        
        try:
            # 注意：lattice model可能预测体积，需要转换为晶格常数
            # a = (4 * V)^(1/3) for FCC
            prediction = self.lattice_model.predict(matminer_features.reshape(1, -1))
            volume = float(prediction[0])
            
            # 转换体积→晶格常数
            lattice = (4 * volume) ** (1/3)
            return lattice
        except Exception as e:
            print(f"Lattice parameter prediction failed: {e}")
            return None
    
    def predict_magnetic_moment(self, matminer_features: np.ndarray) -> Optional[float]:
        """预测磁矩"""
        if self.magnetic_moment_model is None:
            return None
        
        try:
            prediction = self.magnetic_moment_model.predict(matminer_features.reshape(1, -1))
            return float(prediction[0])
        except Exception as e:
            print(f"Magnetic moment prediction failed: {e}")
            return None
    
    def predict_all(self, matminer_features: np.ndarray) -> Dict[str, float]:
        """
        预测所有Proxy特征
        
        Args:
            matminer_features: Matminer特征向量
            
        Returns:
            包含3个Proxy预测的字典
        """
        results = {}
        
        # 形成能
        fe = self.predict_formation_energy(matminer_features)
        results['pred_formation_energy'] = fe if fe is not None else self.DEFAULT_VALUES['pred_formation_energy']
        
        # 晶格参数
        lp = self.predict_lattice_parameter(matminer_features)
        results['pred_lattice_param'] = lp if lp is not None else self.DEFAULT_VALUES['pred_lattice_param']
        
        # 磁矩
        mm = self.predict_magnetic_moment(matminer_features)
        results['pred_magnetic_moment'] = mm if mm is not None else self.DEFAULT_VALUES['pred_magnetic_moment']
        
        return results
    
    def get_model_info(self) -> Dict:
        """返回模型信息"""
        return {
            'formation_energy': self.formation_energy_model is not None,
            'lattice_parameter': self.lattice_model is not None,
            'magnetic_moment': self.magnetic_moment_model is not None,
            'feature_dimensionality': len(self.feature_names) if self.feature_names else 'unknown',
            'default_values': self.DEFAULT_VALUES,
        }
