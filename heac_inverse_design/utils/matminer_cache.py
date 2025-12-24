"""
Proxy模型缓存优化

提供更高效的Matminer特征计算和缓存机制。
"""

from functools import lru_cache
from typing import Dict, Tuple
import numpy as np

try:
    from matminer.featurizers.composition import ElementProperty
    from pymatgen.core import Composition
    MATMINER_AVAILABLE = True
except ImportError:
    MATMINER_AVAILABLE = False


class MatminerCache:
    """Matminer特征计算缓存"""
    
    def __init__(self, cache_size: int = 512):
        """
        初始化缓存
        
        Args:
            cache_size: LRU缓存大小
        """
        self.cache_size = cache_size
        if MATMINER_AVAILABLE:
            self.featurizer = ElementProperty.from_preset("magpie")
        else:
            self.featurizer = None
    
    @lru_cache(maxsize=512)
    def compute_features(self, comp_tuple: Tuple) -> np.ndarray:
        """
        计算Matminer特征（带缓存）
        
        Args:
            comp_tuple: (('Co', 0.3), ('Ni', 0.3), ...) 排序后的成分元组
            
        Returns:
            Matminer特征数组
        """
        if not MATMINER_AVAILABLE or self.featurizer is None:
            return np.zeros(250)  # 返回默认零数组
        
        try:
            # 转换为Composition对象
            comp_dict = dict(comp_tuple)
            comp = Composition(comp_dict)
            
            # 计算特征
            features = self.featurizer.featurize(comp)
            return np.array(features)
        except Exception as e:
            print(f"Matminer computation failed: {e}")
            return np.zeros(250)
    
    def get_features(self, composition: Dict[str, float]) -> np.ndarray:
        """
        获取成分的Matminer特征
        
        Args:
            composition: 元素->分数字典
            
        Returns:
            特征数组
        """
        # 过滤小分数并排序（用于缓存key）
        comp_filtered = {k: v for k, v in composition.items() if v > 0.001}
        comp_tuple = tuple(sorted(comp_filtered.items()))
        
        return self.compute_features(comp_tuple)
    
    def clear_cache(self):
        """清空缓存"""
        self.compute_features.cache_clear()
    
    def get_cache_info(self) -> Dict:
        """获取缓存统计信息"""
        info = self.compute_features.cache_info()
        return {
            'hits': info.hits,
            'misses': info.misses,
            'size': info.currsize,
            'maxsize': info.maxsize,
            'hit_rate': info.hits / (info.hits + info.misses) if (info.hits + info.misses) > 0 else 0
        }


# 全局缓存实例
_matminer_cache = None

def get_matminer_cache() -> MatminerCache:
    """获取全局Matminer缓存实例"""
    global _matminer_cache
    if _matminer_cache is None:
        _matminer_cache = MatminerCache()
    return _matminer_cache
