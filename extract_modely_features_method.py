"""
ModelY特征提取方法
添加到 ModelXAdapter 类中
"""

def extract_modely_features(
    self,
    composition_atomic: Dict[str, float],
    composition_wt: Dict[str, float],
    binder_vol_pct: float,
    grain_size_um: float,
    sinter_temp_c: float,
    proxy_features: Dict[str, float],
    ceramic_type: str = 'WC'
) -> Dict[str, float]:
    """
    提取ModelY所需的13个特征
    
    Args:
        composition_atomic: 粘结相原子分数
        composition_wt: 粘结相质量分数  
        binder_vol_pct: 粘结相体积百分比
        grain_size_um: 晶粒尺寸(μm)
        sinter_temp_c: 烧结温度(°C)
        proxy_features: 代理模型预测特征
        ceramic_type: 陶瓷类型
        
    Returns:
        13个特征的字典
    """
    features = {}
    
    # 1. Matminer特征
    matminer_feats = self.compute_matminer_features(composition_atomic)
    
    # 2. 从Matminer提取需要的3个特征
    features['Composite_MagpieData mean GSmagmom'] = matminer_feats.get('MagpieData mean GSmagmom', 0.0)
    features['Binder_frac d valence electrons'] = matminer_feats.get('frac d valence electrons', 0.0)
    features['Binder_MagpieData range MeltingT'] = matminer_feats.get('MagpieData range MeltingT', 0.0)
    
    # 3. 全部3个Proxy特征
    features['pred_magnetic_moment'] = proxy_features.get('pred_magnetic_moment', 0.0)
    features['pred_formation_energy'] = proxy_features.get('pred_formation_energy', 0.0)
    features['pred_lattice_param'] = proxy_features.get('pred_lattice_param', 0.0)
    
    # 4. 成分特征
    features['Binder_Ni_atomic_frac'] = composition_atomic.get('Ni', 0.0)
    
    # 5. 过渡金属比例
    transition_metals = ['Ti', 'V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zr', 'Nb', 'Mo', 'W', 'Re']
    tm_fraction = sum(composition_atomic.get(el, 0.0) for el in transition_metals)
    features['Binder_transition metal fraction'] = tm_fraction
    
    # 6. 简单特征
    features['Grain_Size_um'] = grain_size_um
    features['Binder_Vol_Pct'] = binder_vol_pct
    features['Sinter_Temp_C'] = sinter_temp_c
    
    # 7. 衍生特征
    features['lattice_mismatch_wc'] = self._calculate_lattice_mismatch(
        proxy_features.get('pred_lattice_param', 3.6),
        ceramic_type
    )
    
    # 8. Mean Free Path计算
    # 简化公式: λ ≈ d * (1 - Vf) / Vf，其中d是晶粒尺寸，Vf是陶瓷体积分数
    ceramic_vol_frac = (100 - binder_vol_pct) / 100.0
    if ceramic_vol_frac > 0 and ceramic_vol_frac < 1.0:
        mean_free_path = grain_size_um * (1 - ceramic_vol_frac) / ceramic_vol_frac
    else:
        mean_free_path = grain_size_um * 0.5  # 默认值
    features['Mean_Free_Path'] = mean_free_path
    
    return features
