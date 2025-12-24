"""
ModelX - 硬度预测模型

封装XGBoost模型用于HV预测。
"""

from .base_model import PredictionModel
from typing import Dict, List
import joblib
import pandas as pd
import numpy as np


class ModelX(PredictionModel):
    """硬度(HV)预测模型"""
    
    # ModelX实际使用的11个特征
    REQUIRED_FEATURES = [
        'Composite_MagpieData mean NUnfilled',
        'Binder_MagpieData avg_dev NdUnfilled',
        'Binder_frac d valence electrons',
        'pred_formation_energy',
        'Binder_MagpieData range Column',
        'Grain_Size_um',
        'lattice_mismatch_wc',
        'Diff_Number',
        'Binder_MagpieData minimum SpaceGroupNumber',
        'Binder_Element_Count',
        'Binder_Vol_Pct',
    ]
    
    TARGET = 'HV_kgf_mm2'
    R2_SCORE = 0.91
    
    def load_model(self):
        """加载ModelX模型"""
        try:
            data = joblib.load(self.model_path)
            
            if isinstance(data, dict):
                self.model = data['model']
                self.scaler = data.get('scaler')
                self.feature_names = data.get('feature_names', self.REQUIRED_FEATURES)
                self.metadata = {
                    'r2_score': self.R2_SCORE,
                    'target': self.TARGET,
                    'description': 'XGBoost模型用于预测硬度',
                }
            else:
                # 直接是模型对象
                self.model = data
                self.feature_names = self.REQUIRED_FEATURES
        except Exception as e:
            raise RuntimeError(f"Failed to load ModelX from {self.model_path}: {e}")
    
    def predict(self, features: Dict[str, float]) -> float:
        """
        预测HV
        
        Args:
            features: 特征字典
            
        Returns:
            预测的HV值
        """
        # 验证特征
        is_valid, missing = self.validate_features(features)
        if not is_valid:
            raise ValueError(f"Missing features: {missing}")
        
        # 准备DataFrame
        df = pd.DataFrame([features])[self.REQUIRED_FEATURES]
        
        # 标准化（如果有scaler）
        if self.scaler is not None:
            X = self.scaler.transform(df)
        else:
            X = df.values
        
        # 预测
        prediction = self.model.predict(X)[0]
        
        return float(prediction)
    
    def get_required_features(self) -> List[str]:
        """返回所需的11个特征"""
        return self.REQUIRED_FEATURES
    
    def predict_batch(self, features_list: List[Dict[str, float]]) -> np.ndarray:
        """
        批量预测
        
        Args:
            features_list: 特征字典列表
            
        Returns:
            预测值数组
        """
        df = pd.DataFrame(features_list)[self.REQUIRED_FEATURES]
        
        if self.scaler is not None:
            X = self.scaler.transform(df)
        else:
            X = df.values
        
        return self.model.predict(X)
