"""
模型抽象基类

定义所有预测模型的统一接口。
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import numpy as np
import joblib
from pathlib import Path


class PredictionModel(ABC):
    """预测模型抽象基类"""
    
    def __init__(self, model_path: str):
        """
        初始化模型
        
        Args:
            model_path: 模型文件路径
        """
        self.model_path = Path(model_path)
        self.model = None
        self.scaler = None
        self.feature_names: List[str] = []
        self.metadata: Dict = {}
        
        self.load_model()
    
    @abstractmethod
    def load_model(self):
        """加载模型（子类实现）"""
        pass
    
    @abstractmethod
    def predict(self, features: Dict[str, float]) -> float:
        """
        预测
        
        Args:
            features: 特征字典
            
        Returns:
            预测值
        """
        pass
    
    @abstractmethod
    def get_required_features(self) -> List[str]:
        """返回所需特征列表"""
        pass
    
    def validate_features(self, features: Dict[str, float]) -> tuple[bool, List[str]]:
        """
        验证特征完整性
        
        Args:
            features: 特征字典
            
        Returns:
            (is_valid, missing_features)
        """
        required = set(self.get_required_features())
        provided = set(features.keys())
        missing = required - provided
        
        return len(missing) == 0, list(missing)
    
    def get_model_info(self) -> Dict:
        """返回模型信息"""
        return {
            'model_path': str(self.model_path),
            'num_features': len(self.get_required_features()),
            'feature_names': self.get_required_features(),
            'metadata': self.metadata,
        }
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(features={len(self.get_required_features())})"
