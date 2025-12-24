"""
逆向设计引擎

使用优化算法从目标性能反推最优成分和工艺参数。
"""

from typing import Dict, List, Tuple, Optional
import optuna
import numpy as np
from ..models import ModelX, ModelY, ProxyModelEnsemble
from ..features import FeatureExtractor
try:
    from ...utils import get_matminer_cache
except ImportError:
    # Fallback if utils not available
    get_matminer_cache = None


class DesignSolution:
    """设计方案数据类"""
    
    def __init__(self, composition: Dict[str, float],
                 grain_size: float,
                 ceramic_vol: float,
                 sinter_temp: float,
                 predicted_hv: float,
                 predicted_kic: float):
        self.composition = composition
        self.grain_size = grain_size
        self.ceramic_vol = ceramic_vol
        self.sinter_temp = sinter_temp
        self.predicted_hv = predicted_hv
        self.predicted_kic = predicted_kic
    
    def to_dict(self) -> Dict:
        return {
            'composition': self.composition,
            'grain_size_um': self.grain_size,
            'ceramic_vol_fraction': self.ceramic_vol,
            'sinter_temp_c': self.sinter_temp,
            'HV': self.predicted_hv,
            'KIC': self.predicted_kic,
        }


class InverseDesigner:
    """逆向设计主引擎"""
    
    def __init__(self,
                 modelx: ModelX,
                 modely: ModelY,
                 proxy_models: ProxyModelEnsemble,
                 feature_extractor: FeatureExtractor):
        """
        初始化逆向设计器
        
        Args:
            modelx: HV预测模型
            modely: KIC预测模型
            proxy_models: Proxy模型集合
            feature_extractor: 特征提取器
        """
        self.modelx = modelx
        self.modely = modely
        self.proxy = proxy_models
        self.extractor = feature_extractor
    
    def design(self,
               target_hv_range: Tuple[float, float],
               target_kic_range: Tuple[float, float],
               allowed_elements: List[str],
               ceramic_type: str = 'WC',
               ceramic_vol_range: Tuple[float, float] = (0.5, 0.7),
               grain_size_range: Tuple[float, float] = (0.5, 5.0),
               sinter_temp_range: Tuple[float, float] = (1350, 1550),
               n_trials: int = 200) -> List[DesignSolution]:
        """
        执行逆向设计
        
        Args:
            target_hv_range: 目标HV范围 (min, max)
            target_kic_range: 目标KIC范围 (min, max)
            allowed_elements: 允许的元素列表
            ceramic_type: 陶瓷类型
            ceramic_vol_range: 陶瓷体积分数范围
            grain_size_range: 晶粒尺寸范围(μm)
            sinter_temp_range: 烧结温度范围(°C)
            n_trials: 优化迭代次数
            
        Returns:
            Pareto最优解列表
        """
        # 创建多目标优化study
        study = optuna.create_study(
            directions=['maximize', 'maximize'],  # 同时最大化HV和KIC
            sampler=optuna.samplers.NSGAIISampler(population_size=50)
        )
        
        def objective(trial):
            # 1. 采样成分（改进的Dirichlet分布方法）
            n_elements = len(allowed_elements)
            
            # 使用log-normal分布采样，然后归一化（更均匀的探索）
            raw_fractions = []
            for i, el in enumerate(allowed_elements):
                # 在log空间采样以获得更好的分布
                log_val = trial.suggest_float(f'log_frac_{el}', -3, 0)  # 10^-3 到 10^0
                raw_fractions.append(10 ** log_val)
            
            # 归一化
            total = sum(raw_fractions)
            fractions = [f / total for f in raw_fractions]
            composition = dict(zip(allowed_elements, fractions))
            
            # 2. 采样工艺参数
            grain_size = trial.suggest_float('grain_size', *grain_size_range)
            ceramic_vol = trial.suggest_float('ceramic_vol', *ceramic_vol_range)
            sinter_temp = trial.suggest_float('sinter_temp', *sinter_temp_range)
            
            # 3. Proxy预测（激活真实预测 + 缓存优化）
            try:
                # 使用缓存的Matminer计算
                cache = get_matminer_cache()
                matminer_feats = cache.get_features(composition)
                
                # 使用Proxy模型预测
                proxy_preds = self.proxy.predict_all(matminer_feats)
            except Exception as e:
                # 降级到默认值
                import warnings
                warnings.warn(f"Proxy prediction failed, using defaults: {e}", UserWarning)
                proxy_preds = {
                    'pred_formation_energy': -0.5,
                    'pred_lattice_param': 3.6,
                    'pred_magnetic_moment': -0.5,
                }
            
            # 4. 特征提取
            try:
                features = self.extractor.extract_all(
                    composition, grain_size, ceramic_vol,
                    sinter_temp, proxy_preds, ceramic_type
                )
            except Exception as e:
                print(f"Feature extraction failed: {e}")
                return -10000, -10000  # 惩罚值
            
            # 5. 预测
            try:
                hv = self.modelx.predict(features)
                kic = self.modely.predict(features)
            except Exception as e:
                print(f"Prediction failed: {e}")
                return -10000, -10000
            
            # 6. 约束惩罚
            penalty = 0
            
            # HV约束
            if hv < target_hv_range[0]:
                penalty += (target_hv_range[0] - hv) * 10
            elif hv > target_hv_range[1]:
                penalty += (hv - target_hv_range[1]) * 10
            
            # KIC约束
            if kic < target_kic_range[0]:
                penalty += (target_kic_range[0] - kic) * 100
            elif kic > target_kic_range[1]:
                penalty += (kic - target_kic_range[1]) * 100
            
            return hv - penalty, kic - penalty
        
        # 运行优化
        study.optimize(objective, n_trials=n_trials, show_progress_bar=True)
        
        # 提取Pareto最优解
        solutions = []
        for trial in study.best_trials:
            # 重建成分 (根据log-normal采样逻辑)
            raw_fractions = []
            for el in allowed_elements:
                log_val = trial.params.get(f'log_frac_{el}')
                if log_val is not None:
                    raw_fractions.append(10 ** log_val)
                else:
                    # Fallback for compatibility
                    raw_fractions.append(trial.params.get(f'frac_{el}', 0.1))
            
            # 归一化
            total = sum(raw_fractions)
            composition = {}
            for i, el in enumerate(allowed_elements):
                composition[el] = raw_fractions[i] / total
            
            solution = DesignSolution(
                composition=composition,
                grain_size=trial.params['grain_size'],
                ceramic_vol=trial.params['ceramic_vol'],
                sinter_temp=trial.params['sinter_temp'],
                predicted_hv=trial.values[0],
                predicted_kic=trial.values[1]
            )
            solutions.append(solution)
        
        return solutions
