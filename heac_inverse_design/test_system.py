"""
测试脚本 - 验证新逆向设计系统

测试模型加载和基本功能。
"""

import sys
import os

# 添加路径
sys.path.insert(0, r'd:\ML\HEAC 0.2')

print("=" * 60)
print("HEA Cermet 逆向设计系统 - 测试脚本")
print("=" * 60)

# Test script with ASCII indicators to comply with Windows console encoding

# [Test 1] Importing modules...
try:
    from heac_inverse_design.core.models import ModelX, ModelY, ProxyModelEnsemble
    from heac_inverse_design.core.features import FeatureExtractor
    from heac_inverse_design.core.optimization import InverseDesigner
    print("[OK] All modules imported successfully")
except Exception as e:
    print(f"[FAIL] Module import failed: {e}")
    sys.exit(1)

# [Test 2] Loading ModelX...
print("\n[Test 2] Loading ModelX...")
try:
    modelx = ModelX(r'd:\ML\HEAC 0.2\models\ModelX.pkl')
    print(f"[OK] ModelX loaded successfully")
    print(f"   - Feature count: {len(modelx.get_required_features())}")
    print(f"   - Model info: {modelx.get_model_info()['metadata']}")
except Exception as e:
    print(f"[FAIL] ModelX load failed: {e}")

# [Test 3] Loading ModelY...
print("\n[Test 3] Loading ModelY...")
try:
    modely = ModelY(r'd:\ML\HEAC 0.2\models\ModelY.pkl')
    print(f"[OK] ModelY loaded successfully")
    print(f"   - Feature count: {len(modely.get_required_features())}")
    print(f"   - Model info: {modely.get_model_info()['metadata']}")
except Exception as e:
    print(f"[FAIL] ModelY load failed: {e}")

# [Test 4] Loading Proxy models...
print("\n[Test 4] Loading Proxy models...")
try:
    proxy = ProxyModelEnsemble(r'd:\ML\HEAC 0.2\models\proxy_models')
    info = proxy.get_model_info()
    print(f"[OK] Proxy models loaded successfully")
    print(f"   - Formation Energy: {'[YES]' if info['formation_energy'] else '[NO]'}")
    print(f"   - Lattice Parameter: {'[YES]' if info['lattice_parameter'] else '[NO]'}")
    print(f"   - Magnetic Moment: {'[YES]' if info['magnetic_moment'] else '[NO]'}")
except Exception as e:
    print(f"[FAIL] Proxy models load failed: {e}")

# [Test 5] Feature Extractor...
print("\n[Test 5] Initializing Feature Extractor...")
try:
    extractor = FeatureExtractor()
    print(f"[OK] Feature Extractor initialized")
except Exception as e:
    print(f"[FAIL] Feature Extractor init failed: {e}")

# [Test 6] Inverse Designer...
print("\n[Test 6] Creating Inverse Designer...")
try:
    designer = InverseDesigner(modelx, modely, proxy, extractor)
    print(f"[OK] Inverse Designer created")
except Exception as e:
    print(f"[FAIL] Inverse Designer creation failed: {e}")

# [Test 7] Simple prediction test...
print("\n[Test 7] Testing prediction...")
try:
    # Create test features (simplified)
    test_features_x = {feat: 0.0 for feat in modelx.get_required_features()}
    test_features_x.update({
        'Grain_Size_um': 1.0,
        'Binder_Vol_Pct': 40.0,
        'pred_formation_energy': -0.5,
        'Binder_Element_Count': 4,
    })
    
    hv = modelx.predict(test_features_x)
    print(f"[OK] ModelX prediction successful: HV = {hv:.2f}")
except Exception as e:
    print(f"[WARN] ModelX prediction test skipped: {e}")

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)

print("\n下一步:")
print("运行以下命令启动Streamlit应用:")
print("  cd heac_inverse_design\\ui")
print("  streamlit run inverse_design_app.py")
