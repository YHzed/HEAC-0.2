"""
替换 modelx_adapter.py 中的 extract_modelx_features 方法 (第136-215行)

使用以下代码完全替换现有的 extract_modelx_features 方法：
"""

def extract_modelx_features(
    self,
    composition_atomic: Dict[str, float],
    composition_wt: Dict[str, float],
    binder_vol_pct: float,  # ❗ 改为vol_pct
    grain_size_um: float,
    proxy_features: Dict[str, float],
    ceramic_type: str = 'WC'
) -> Dict[str, float]:
    """
    提取ModelX所需的11个特征（实际训练特征）
    
    Args:
        composition_atomic: 粘结相原子分数
        composition_wt: 粘结相质量分数
        binder_vol_pct: 粘结相体积百分比
        grain_size_um: 晶粒尺寸(μm)
        proxy_features: 代理模型预测特征
        ceramic_type: 陶瓷类型
        
    Returns:
        11个特征的字典
    """
    features = {}
    
    # 1. Matminer特征（使用原子分数）
    matminer_feats = self.compute_matminer_features(composition_atomic)
    
    # 2. 从Matminer提取需要的特征
    features['Composite_MagpieData mean NUnfilled'] = matminer_feats.get('MagpieData mean NUnfilled', 0.0)
    features['Binder_MagpieData avg_dev NdUnfilled'] = matminer_feats.get('MagpieData avg_dev NdUnfilled', 0.0)
    features['Binder_frac d valence electrons'] = matminer_feats.get('frac d valence electrons', 0.0)
    features['Binder_MagpieData range Column'] = matminer_feats.get('MagpieData range Column', 0.0)
    features['Binder_MagpieData minimum SpaceGroupNumber'] = matminer_feats.get('MagpieData minimum SpaceGroupNumber', 0.0)
    
    # 3. Proxy特征
features['pred_formation_energy'] = proxy_features.get('pred_formation_energy', 0.0)
    
    # 4. 简单特征
    features['Grain_Size_um'] = grain_size_um
    features['Binder_Vol_Pct'] = binder_vol_pct  # ❗ 使用体积百分比
    
    # 5. 衍生特征 - lattice_mismatch_wc
    pred_lattice = proxy_features.get('pred_lattice_param', 3.6)  # 使用默认值如果缺失
    features['lattice_mismatch_wc'] = self._calculate_lattice_mismatch(
        pred_lattice,
        ceramic_type
    )
    
    # 6. 差异特征 - Diff_Number
    if len(composition_atomic) > 1:
        atomic_nums = [self._get_atomic_number(el) for el in composition_atomic.keys()]
        features['Diff_Number'] = max(atomic_nums) - min(atomic_nums)
    else:
        features['Diff_Number'] = 0
    
    # 7. 元素计数（阈值>0.01）
    features['Binder_Element_Count'] = sum(1 for v in composition_atomic.values() if v > 0.01)
    
    return features
