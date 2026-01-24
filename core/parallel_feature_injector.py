"""
inject_features 并行处理优化模块

实现特征注入的并行处理和缓存机制
预期性能提升：4-8x
"""
import multiprocessing as mp
from functools import lru_cache, partial
import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple, Any
import warnings


def _get_empty_features() -> Dict[str, Any]:
    """返回空特征字典"""
    return {
        'pred_formation_energy': np.nan,
        'pred_lattice_param': np.nan,
        'pred_magnetic_moment': np.nan,
        'vec_binder': np.nan,
        'lattice_mismatch': np.nan,
        'coherent_potential': np.nan,
        'is_coherent': False,
        'lattice_distortion': np.nan,
    }


def _process_single_row_worker(args: Tuple) -> Dict[str, Any]:
    """
    处理单行数据（用于并行处理的全局函数）
    
    必须是模块级函数以支持Windows multiprocessing (pickle序列化)
    
    Args:
        args: (injector, composition_str, ceramic_type)
        
    Returns:
        特征字典
    """
    injector, comp_str, ceramic_type = args
    
    # 解析成分
    composition = injector.composition_parser.parse(comp_str)
    if not composition:
        return _get_empty_features()
    
    # 计算所有特征
    try:
        features = {
            'pred_formation_energy': injector.predict_formation_energy(composition),
            'pred_lattice_param': injector.predict_lattice_parameter(composition),
            'pred_magnetic_moment': injector.predict_magnetic_moment(composition),
            'vec_binder': injector.calculate_vec(composition),
        }
        
        # 晶格相关特征
        if features['pred_lattice_param'] is not None:
            features['lattice_mismatch'] = injector.calculate_lattice_mismatch(
                features['pred_lattice_param'], ceramic_type
            )
            features['coherent_potential'] = injector.calculate_coherent_potential(
                features['pred_lattice_param'], ceramic_type
            )
            features['is_coherent'] = features['coherent_potential'] < 0.01 if features['coherent_potential'] else False
            
            # Vegards晶格
            vegard = injector.calculate_vegards_lattice(composition)
            if vegard:
                features['lattice_distortion'] = abs(features['pred_lattice_param'] - vegard)
            else:
                features['lattice_distortion'] = np.nan
        else:
            features['lattice_mismatch'] = np.nan
            features['coherent_potential'] = np.nan
            features['is_coherent'] = False
            features['lattice_distortion'] = np.nan
        
        return features
        
    except Exception as e:
        warnings.warn(f"处理失败: {e}")
        return _get_empty_features()


class ParallelFeatureInjector:
    """
    并行特征注入器
    
    解决Matminer特征化瓶颈（占48%时间）
    """
    
    def __init__(self, injector):
        """
        初始化并行注入器
        
        Args:
            injector: FeatureInjector实例
        """
        self.injector = injector
        self._feature_cache = {}  # 特征缓存
    
    def inject_features_parallel(self, df: pd.DataFrame,
                                 comp_col: str = 'binder_composition',
                                 ceramic_type_col: str = 'Ceramic_Type',
                                 n_jobs: int = None,
                                 verbose: bool = True) -> pd.DataFrame:
        """
        并行特征注入（多进程版本）
        
        Windows兼容：使用模块级worker函数支持pickle序列化
        
        Args:
            df: 输入DataFrame
            comp_col: 成分列名
            ceramic_type_col: 陶瓷类型列名
            n_jobs: 进程数（None=CPU核心数）
            verbose: 是否显示进度
            
        Returns:
            添加特征的DataFrame
        """
        import time
        start = time.time()
        
        if n_jobs is None:
            n_jobs = mp.cpu_count()
        
        if verbose:
            print(f"\n🚀 并行特征注入（{n_jobs}进程）")
            print(f"📊 处理 {len(df)} 行数据...")
        
        df = df.copy()
        
        # 准备ceramic_type
        if ceramic_type_col in df.columns:
            ceramic_types = df[ceramic_type_col].fillna('WC').astype(str)
        else:
            ceramic_types = pd.Series(['WC'] * len(df), index=df.index)
        
        # 准备参数
        args_list = [
            (self.injector, comp, ctype)
            for comp, ctype in zip(df[comp_col], ceramic_types)
        ]
        
        # 并行处理
        if verbose:
            print(f"⚡ 开始并行处理...")
        
        # 使用全局worker函数（支持pickle）
        with mp.Pool(processes=n_jobs) as pool:
            results = pool.map(_process_single_row_worker, args_list)
        
        # 合并结果
        result_df = pd.DataFrame(results, index=df.index)
        for col in result_df.columns:
            df[col] = result_df[col]
        
        elapsed = time.time() - start
        if verbose:
            print(f"✅ 完成！耗时: {elapsed:.2f}秒 ({len(df)/elapsed:.1f} 行/秒)")
        
        return df
    def inject_features_cached(self, df: pd.DataFrame,
                               comp_col: str = 'binder_composition',
                               ceramic_type_col: str = 'Ceramic_Type',
                               verbose: bool = True) -> pd.DataFrame:
        """
        带缓存的特征注入
        
        对重复的成分使用缓存，避免重复计算Matminer特征
        
        Args:
            df: 输入DataFrame
            comp_col: 成分列名
            ceramic_type_col: 陶瓷类型列名
            verbose: 是否显示进度
            
        Returns:
            添加特征的DataFrame
        """
        import time
        start = time.time()
        
        if verbose:
            print(f"\n💾 带缓存的特征注入")
            print(f"📊 处理 {len(df)} 行数据...")
        
        df = df.copy()
        
        # 统计唯一成分
        unique_comps = df[comp_col].dropna().unique()
        if verbose:
            print(f"📝 唯一成分: {len(unique_comps)}/{len(df)} ({len(unique_comps)/len(df)*100:.1f}%)")
        
        # 准备ceramic_type
        if ceramic_type_col in df.columns:
            ceramic_types = df[ceramic_type_col].fillna('WC').astype(str)
        else:
            ceramic_types = pd.Series(['WC'] * len(df), index=df.index)
        
        # 使用缓存计算
        cache_hits = 0
        results = []
        
        for comp_str, ceramic_type in zip(df[comp_col], ceramic_types):
            cache_key = (comp_str, ceramic_type)
            
            # 检查缓存
            if cache_key in self._feature_cache:
                results.append(self._feature_cache[cache_key])
                cache_hits += 1
            else:
                # 计算特征（使用全局worker）
                feat = _process_single_row_worker((self.injector, comp_str, ceramic_type))
                self._feature_cache[cache_key] = feat
                results.append(feat)
        
        # 合并结果
        result_df = pd.DataFrame(results, index=df.index)
        for col in result_df.columns:
            df[col] = result_df[col]
        
        elapsed = time.time() - start
        if verbose:
            print(f"💰 缓存命中: {cache_hits}/{len(df)} ({cache_hits/len(df)*100:.1f}%)")
            print(f"✅ 完成！耗时: {elapsed:.2f}秒 ({len(df)/elapsed:.1f} 行/秒)")
        
        return df
