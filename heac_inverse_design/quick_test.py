"""
快速测试脚本 - 验证新逆向设计系统

此脚本测试所有核心组件的加载和基本功能。
运行: python quick_test.py
"""

import sys
import os

# 添加路径
sys.path.insert(0, r'd:\ML\HEAC 0.2')

print("=" * 60)
print("HEA Cermet Inverse Design System - Quick Test")
print("=" * 60)

# Test 1: Import modules
print("\n[Test 1] Importing modules...")
try:
    from heac_inverse_design.core.models import ModelX, ModelY, ProxyModelEnsemble
    from heac_inverse_design.core.features import FeatureExtractor
    from heac_inverse_design.core.optimization import InverseDesigner
    print("[OK] All modules imported successfully")
except Exception as e:
    print(f"[FAIL] Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Load ModelX
print("\n[Test 2] Loading ModelX...")
try:
    modelx = ModelX(r'd:\ML\HEAC 0.2\models\ModelX.pkl')
    print(f"[OK] ModelX loaded")
    print(f"   Features: {len(modelx.get_required_features())}")
    print(f"   R2 Score: {modelx.R2_SCORE}")
except Exception as e:
    print(f"[FAIL] ModelX: {e}")
    modelx = None

# Test 3: Load ModelY
print("\n[Test 3] Loading ModelY...")
try:
    modely = ModelY(r'd:\ML\HEAC 0.2\models\ModelY.pkl')
    print(f"[OK] ModelY loaded")
    print(f"   Features: {len(modely.get_required_features())}")
    print(f"   R2 Score: {modely.R2_SCORE}")
except Exception as e:
    print(f"[FAIL] ModelY: {e}")
    modely = None

# Test 4: Load Proxy models
print("\n[Test 4] Loading Proxy models...")
try:
    proxy = ProxyModelEnsemble(r'd:\ML\HEAC 0.2\models\proxy_models')
    info = proxy.get_model_info()
    print(f"[OK] Proxy models loaded")
    print(f"   Formation Energy: {info['formation_energy']}")
    print(f"   Lattice Parameter: {info['lattice_parameter']}")
    print(f"   Magnetic Moment: {info['magnetic_moment']}")
except Exception as e:
    print(f"[FAIL] Proxy: {e}")
    proxy = None

# Test 5: Feature Extractor
print("\n[Test 5] Creating Feature Extractor...")
try:
    extractor = FeatureExtractor()
    print(f"[OK] Feature Extractor created")
except Exception as e:
    print(f"[FAIL] Extractor: {e}")
    extractor = None

# Test 6: Inverse Designer
print("\n[Test 6] Creating Inverse Designer...")
if all([modelx, modely, proxy, extractor]):
    try:
        designer = InverseDesigner(modelx, modely, proxy, extractor)
        print(f"[OK] Inverse Designer created")
        print("\n" + "=" * 60)
        print("SUCCESS! All components loaded correctly.")
        print("=" * 60)
        print("\nNext step: Run the Streamlit app:")
        print("  cd heac_inverse_design\\ui")
        print("  streamlit run inverse_design_app.py")
    except Exception as e:
        print(f"[FAIL] Designer: {e}")
else:
    print("[SKIP] Cannot create designer (missing components)")
    print("\n" + "=" * 60)
    print("PARTIAL SUCCESS - Some components failed to load")
    print("=" * 60)
