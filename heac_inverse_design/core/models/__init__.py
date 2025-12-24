"""
Models Module

模型封装模块，提供ModelX、ModelY和ProxyModels的统一接口。
"""

from .base_model import PredictionModel
from .modelx import ModelX
from .modely import ModelY
from .proxy_models import ProxyModelEnsemble

__all__ = [
    'PredictionModel',
    'ModelX',
    'ModelY',
    'ProxyModelEnsemble',
]
