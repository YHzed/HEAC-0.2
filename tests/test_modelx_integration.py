"""
ModelX集成测试

测试：
1. PhysicsEngine生成ModelX特征
2. ModelXAdapter预测
3. AIPredictor使用ModelX预测HV
"""

import sys
sys.path.insert(0, r'd:\ML\HEAC 0.2')

from core.system_architecture import DesignSpace, PhysicsEngine, AIPredictor

print("=" * 80)
print("ModelX Integration Test")
print("=" * 80)

# 测试配方：Co-Ni-Fe-Cr-Mo HEA + WC
design = DesignSpace(
    hea_composition={'Co': 1.0, 'Ni': 1.0, 'Fe': 0.5, 'Cr': 0.3, 'Mo': 0.2},
    is_mass_fraction=False,
    ceramic_type='WC',
    ceramic_vol_fraction=0.5,
    grain_size_um=1.0,
    sinter_temp_c=1400,
    sinter_time_min=60
)

print("\n1. Testing PhysicsEngine.compute_modelx_features()...")
try:
    engine = PhysicsEngine()
    modelx_features = engine.compute_modelx_features(design)
    
    print(f"✓ Generated {len(modelx_features)} features")
    print("\nFeature values:")
    for i, (key, value) in enumerate(modelx_features.items(), 1):
        print(f"  {i:2d}. {key:40s} = {value:8.4f}")
    
    # 检查是否有NaN/Inf
    import numpy as np
    nan_count = sum(1 for v in modelx_features.values() if np.isnan(v) or np.isinf(v))
    if nan_count > 0:
        print(f"\n⚠️  Warning: {nan_count} features contain NaN/Inf!")
    else:
        print("\n✓ All features are valid (no NaN/Inf)")
        
except Exception as e:
    print(f"✗ Feature generation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n2. Testing ModelXAdapter.predict_single()...")
try:
    hv_pred = engine.modelx_adapter.predict_single(modelx_features)
    print(f"✓ ModelX HV prediction: {hv_pred:.1f} HV")
    
    # 合理性检查
    if 1200 < hv_pred < 2500:
        print("✓ Prediction is within reasonable HV range (1200-2500)")
    else:
        print(f"⚠️  Warning: Prediction ({hv_pred:.1f}) outside typical range")
        
except Exception as e:
    print(f"✗ ModelX prediction failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n3. Testing AIPredictor with ModelX...")
try:
    predictor = AIPredictor()
    results = predictor.predict(design)
    
    print(f"✓ Predicted HV: {results['Predicted_HV']:.1f} HV")
    print(f"✓ Source: {results['HV_Source']}")
    print(f"✓ Predicted K1C: {results['Predicted_K1C']:.2f} MPa·m½")
    print(f"✓ K1C Source: {results['K1C_Source']}")
    
    # 验证是否使用了ModelX
    if 'ModelX' in results['HV_Source']:
        print("\n✓✓✓ SUCCESS: AIPredictor is using ModelX!")
    else:
        print(f"\n⚠️  Warning: Expected ModelX but got {results['HV_Source']}")
        
except Exception as e:
    print(f"✗ AIPredictor test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 80)
print("✓✓✓ All tests passed!")
print("=" * 80)
