"""
ModelY - 断裂韧性预测模型

封装XGBoost模型用于KIC预测。
"""

from .base_model import PredictionModel
from typing import Dict, List
import joblib
import pandas as pd
import numpy as np
import warnings


class ModelY(PredictionModel):
    """断裂韧性(KIC)预测模型"""
    
    # ModelY使用的13个特征
    REQUIRED_FEATURES = [
        'pred_magnetic_moment',
        'Binder_Ni_atomic_frac',
        'Composite_MagpieData mean GSmagmom',
        'Mean_Free_Path',
        'Binder_transition metal fraction',
        'Grain_Size_um',
        'lattice_mismatch_wc',
        'Sinter_Temp_C',
        'Binder_frac d valence electrons',
        'pred_formation_energy',
        'pred_lattice_param',
        'Binder_MagpieData range MeltingT',
        'Binder_Vol_Pct',
    ]
    
    TARGET = 'KIC_MPa_m'
    R2_SCORE = 0.76
    
    def load_model(self):
        """加载ModelY模型"""
        try:
            data = joblib.load(self.model_path)
            
            if isinstance(data, dict):
                self.model = data['model']
                self.scaler = data.get('scaler')
                self.feature_names = data.get('feature_names', self.REQUIRED_FEATURES)
                self.metadata = {
                    'r2_score': self.R2_SCORE,
                    'target': self.TARGET,
                    'description': 'XGBoost模型用于预测断裂韧性',
                }
            else:
                self.model = data
                self.feature_names = self.REQUIRED_FEATURES
        except Exception as e:
            raise RuntimeError(f"Failed to load ModelY from {self.model_path}: {e}")
    
    def predict(self, features: Dict[str, float]) -> float:
        """
        预测KIC
        
        Args:
            features: 特征字典
            
        Returns:
            预测的KIC值（绝对值，因为物理上不能为负）
        """
        # 验证特征
        is_valid, missing = self.validate_features(features)
        if not is_valid:
            raise ValueError(f"Missing features: {missing}")
        
        # 准备DataFrame
        df = pd.DataFrame([features])[self.REQUIRED_FEATURES]
        
        # 标准化
        if self.scaler is not None:
            X = self.scaler.transform(df)
        else:
            X = df.values
        
        # 预测
        prediction = self.model.predict(X)[0]
        
        # 处理负值（物理不合理）
        if prediction < 0:
            warnings.warn(
                f"ModelY预测返回负值({prediction:.2f})，已转换为绝对值。"
                "这可能表明训练数据存在问题。",
                UserWarning
            )
            prediction = abs(prediction)
        
        return float(prediction)
    
    def get_required_features(self) -> List[str]:
        """返回所需的13个特征"""
        return self.REQUIRED_FEATURES
    
    def predict_batch(self, features_list: List[Dict[str, float]]) -> np.ndarray:
        """
        批量预测
        
        Args:
            features_list: 特征字典列表
            
        Returns:
            预测值数组（所有负值已转为绝对值）
        """
        df = pd.DataFrame(features_list)[self.REQUIRED_FEATURES]
        
        if self.scaler is not None:
            X = self.scaler.transform(df)
        else:
            X = df.values
        
        predictions = self.model.predict(X)
        
        # 处理负值
        negative_mask = predictions < 0
        if negative_mask.any():
            warnings.warn(
                f"ModelY批量预测中有{negative_mask.sum()}个负值，已转换为绝对值。",
                UserWarning
            )
            predictions = np.abs(predictions)
        
        return predictions
