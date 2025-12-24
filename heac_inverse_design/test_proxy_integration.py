"""
测试真实Proxy模型集成

验证Matminer特征计算和Proxy模型预测是否正常工作。
"""

import sys
sys.path.insert(0, r'd:\ML\HEAC 0.2')

print("=" * 60)
print("Testing Real Proxy Model Integration")
print("=" * 60)

# Test 1: MatminerCache
print("\n[Test 1] MatminerCache...")
try:
    from heac_inverse_design.utils import get_matminer_cache
    
    cache = get_matminer_cache()
    test_comp = {'Co': 0.3, 'Ni': 0.3, 'Fe': 0.25, 'Cr': 0.15}
    
    features = cache.get_features(test_comp)
    print(f"[OK] Matminer features computed")
    print(f"   Shape: {features.shape}")
    print(f"   Sample values: {features[:5]}")
    
    # Test caching
    features2 = cache.get_features(test_comp)
    cache_info = cache.get_cache_info()
    print(f"   Cache hits: {cache_info['hits']}")
    print(f"   Cache hit rate: {cache_info['hit_rate']:.1%}")
except Exception as e:
    print(f"[FAIL] MatminerCache: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Proxy Model Predictions
print("\n[Test 2] Proxy Model Predictions...")
try:
    from heac_inverse_design.core.models import ProxyModelEnsemble
    import numpy as np
    
    proxy = ProxyModelEnsemble(r'd:\ML\HEAC 0.2\models\proxy_models')
    
    # Use matminer features
    proxy_preds = proxy.predict_all(features)
    
    print(f"[OK] Proxy predictions:")
    print(f"   Formation Energy: {proxy_preds['pred_formation_energy']:.4f} eV/atom")
    print(f"   Lattice Parameter: {proxy_preds['pred_lattice_param']:.4f} A")
    print(f"   Magnetic Moment: {proxy_preds['pred_magnetic_moment']:.4f} uB/atom")
except Exception as e:
    print(f"[FAIL] Proxy predictions: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Full Integration
print("\n[Test 3] Full Integration in InverseDesigner...")
try:
    from heac_inverse_design.core.models import ModelX, ModelY
    from heac_inverse_design.core.features import FeatureExtractor
    from heac_inverse_design.core.optimization import InverseDesigner
    
    modelx = ModelX(r'd:\ML\HEAC 0.2\models\ModelX.pkl')
    modely = ModelY(r'd:\ML\HEAC 0.2\models\ModelY.pkl')
    extractor = FeatureExtractor()
    
    designer = InverseDesigner(modelx, modely, proxy, extractor)
    
    print("[OK] InverseDesigner created with real Proxy integration")
    print("\n" + "=" * 60)
    print("SUCCESS! Real Proxy model integration working")
    print("=" * 60)
except Exception as e:
    print(f"[FAIL] Integration: {e}")
    import traceback
    traceback.print_exc()

print("\nNext: Test in actual optimization run")
